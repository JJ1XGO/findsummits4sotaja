import sys
import datetime
import numpy as np
import requests
import io
from PIL import Image
from math import pi
from math import e
from math import atan
from math import log
from math import tan
from math import sin
from math import asin
from math import tanh
from numpy import arctanh
## defval
# 座標を求める際に使用する定数
L = 85.05112878
pix=256     # pngタイルの縦横dot数でもある
## その他
dtlZoomLvl=15# 最も詳細な標高データが入ったzoomレベル

# メッシュコードから緯度/経度を求める
def mesh2latlon(meshCode):
    # 文字列に変換
    meshCode = str(meshCode)
    # １次メッシュ用計算
    code_first_two = meshCode[0:2]
    code_last_two = meshCode[2:4]
    code_first_two = int(code_first_two)
    code_last_two = int(code_last_two)
    lat  = code_first_two * 2 / 3
    lon = code_last_two + 100

    if len(meshCode) > 4:
        # ２次メッシュ用計算
        if len(meshCode) >= 6:
            code_fifth = meshCode[4:5]
            code_sixth = meshCode[5:6]
            code_fifth = int(code_fifth)
            code_sixth = int(code_sixth)
            lat += code_fifth * 2 / 3 / 8
            lon += code_sixth / 8
        # ３次メッシュ用計算
        if len(meshCode) == 8:
            code_seventh = meshCode[6:7]
            code_eighth = meshCode[7:8]
            code_seventh = int(code_seventh)
            code_eighth = int(code_eighth)
            lat += code_seventh * 2 / 3 / 8 / 10
            lon += code_eighth / 8 / 10
    return(lat, lon)
# 緯度経度からピクセル座標を返す
def latlon2PixelPoint(lat, lon, z):
    pixelX = int( (2**(z+7)) * ((lon/180) + 1) )
    pixelY = int( (2**(z+7)/pi) * (-1 * arctanh(sin(lat * pi/180)) + arctanh(sin(L * pi/180))) )
    return pixelX, pixelY
# ピクセル座標から緯度経度を返す
def pixel2LatLng(z, x, y):
    lon = 180 * ((x / 2.0**(z+7) ) - 1)
    lat = 180/pi * (asin(tanh(-pi/2**(z+7)*y + arctanh(sin(pi/180*L)))))
    return lat, lon
# 緯度経度からタイル座標と、そのタイル内の座標を返す
def latlon2tilePixel(lat, lon, z):
    (pixelX,pixelY)=latlon2PixelPoint(lat, lon, z)
    tileX=int(pixelX/pix)
    tileY=int(pixelY/pix)
    pointX=int(pixelX%pix)
    pointY=int(pixelY%pix)
#    print("({}, {}) -> {}/{}/{}:({}, {})".format(lat, lon, z, tileX, tileY, pointX, pointY))
    return tileX, tileY, pointY, pointX
# タイル座標から緯度経度を返す
def tile2latlon(z, x, y):
    lon=(x/2**z)*360-180                # 経度(東経)
    mapy=(y/2.0**z)*2*pi-pi
    lat=2*atan(e**(-mapy))*180/pi-90    # 緯度(北緯)
    return lat, lon
#
def fetch_rough_tile(z, x, y):
    """
    与えられた座標に対応する(dtlZoomLvl-1)レベルの地理院地図タイル画像を取得し、imageと画像内の開始座標を返す
    """
    # 与えられた座標の緯度経度を求める
    (lat,lon)=tile2latlon(z, x, y)
    # 1レベル下のタイル座標を求める
    (tileX, tileY, pointY, pointX)=latlon2tilePixel(lat, lon, z-1)
    if (pointY != 0 and pointY != 128):
        print("Check pointY! {}/{}/{} (0, 0) -> ({}, {}) -> {}/{}/{}:(--> {} <--, {})".format(z, x, y, lat, lon, z-1, tileX, tileY, pointY, pointX))
    if (pointX != 0 and pointX != 128):
        print("Check pointX! {}/{}/{} (0, 0) -> ({}, {}) -> {}/{}/{}:({}, --> {} <--)".format(z, x, y, lat, lon, z-1, tileX, tileY, pointY, pointX))
    #
    url = "https://cyberjapandata.gsi.go.jp/xyz/dem_png/{}/{}/{}.png".format(z-1, tileX, tileY)
    res=requests.get(url)
    if res.status_code == 200:
        img = Image.open(io.BytesIO(res.content))
    else:
        print("status_code={} dem_png/{}/{}/{}".format(res.status_code, z-1, tileX, tileY))
        print("return N/A image")
        img = Image.new("RGB",(256, 256),(128,0,0))
    return img, z-1, tileX, tileY, pointX, pointY
#
def fetch_tile(z, x, y):
    """
    与えられた座標に対応する地理院地図標高タイル画像を取得し、可能な限り標高データで埋めたimageを返す
    """
#    url = "https://cyberjapandata.gsi.go.jp/xyz/dem5a_png/{}/{}/{}.png".format(z, x, y)
#    img = Image.open(io.BytesIO(requests.get(url).content))
    flgGetTile=False
    for dem5lvl in (["a", "b", "c"]):
        url = "https://cyberjapandata.gsi.go.jp/xyz/dem5{}_png/{}/{}/{}.png".format(dem5lvl, z, x, y)
        res=requests.get(url)
        if res.status_code == 200:
            if flgGetTile:  # 既に標高タイルが取得出来てる時は標高データがN/Aの部分だけ入れる
                tilearry = np.array(Image.open(io.BytesIO(res.content)))
                for (pixX,pixY) in list(zip(*np.where(elevsarry==2**23))):
                    imgarry[pixY,pixX] = tilearry[pixY,pixX]
            else:           # 初めて標高タイルが取得出来た時はそのまま入れる
                flgGetTile=True
                imgarry = np.array(Image.open(io.BytesIO(res.content)))
            elevsarry=imgarry[:, :, 0].copy()*np.power(2,16)+imgarry[:, :, 1].copy()*np.power(2,8)+imgarry[:, :, 2].copy()
            if (elevsarry==2**23).any():    #標高データにN/Aがなければ抜ける
                pass
            else:
                break
#        else:
#            print("get_status={} {}/{}/{}/{}".format(res.status_code,dem5lvl, z, x, y))
    # ここまでで最も詳細な標高データの取得完了。標高データN/Aがあったら次のレベルの標高データで補完する
#    if flgGetTile:  # 既に標高タイルが取得出来てる時
    if flgGetTile is False:  # 標高タイルが取得出来ていない時
        imgarry = np.array(Image.new("RGB",(256, 256),(128,0,0)))
        elevsarry=imgarry[:, :, 0].copy()*np.power(2,16)
    if (elevsarry==2**23).any():    #標高データにN/Aがあったら
        (imgtile,zlvl,tileX,tileY,pixX,pixY) = fetch_rough_tile(z, x, y)    # 取り敢えず1レベル粗い標高タイルを取得して
        tilearry = np.array(imgtile)                                        # tilearryに入れる
        for (pixY,pixX) in list(zip(*np.where(elevsarry==2**23))):          # 標高データがN/Aの座標を取得して
            (lat, lon)=pixel2LatLng(z, pix*x+pixX, pix*y+pixY)   # その座標の緯度経度を求め
            # 1レベル下のタイル座標を求める
            (tileXX, tileYY, pointY, pointX)=latlon2tilePixel(lat, lon, z-1)   # 緯度経度から取得したタイルのどの位置に当たるかを求める
            assert tileX == tileXX, "タイル座標のXが一致していません。Image={}/{}/{}:request={}/{}/{}".format(zlvl,tileX,tileY,z-1,tileXX, tileYY)
            assert tileY == tileYY, "タイル座標のYが一致していません。Image={}/{}/{}:request={}/{}/{}".format(zlvl,tileX,tileY,z-1,tileXX, tileYY)
#            print("{}/{}/{} ({}, {}) -> ({}, {}) -> {}/{}/{} ({}, {})".format(z,x,y,pixY,pixX,lat,lon,zlvl,tileX,tileY,pointY,pointX))
            imgarry[pixY,pixX] = tilearry[pointY, pointX]   # 標高データがN/Aの部分だけ入れる
    img = Image.fromarray(imgarry)  # imgarryをImageに変換
    # resizeの動きが明確にわからないので取り敢えず保留
#    else:   # 標高タイルが取得出来てない時
#        (imgtile,zlvl,tileX,tileY,pixX,pixY) = fetch_rough_tile(z, x, y) # 1レベル粗い標高タイルを取得
#        print("{}/{}/{} cropping from {}/{}/{} ({}, {})".format(z, x, y, zlvl,tileX,tileY,pixX,pixY))
#        crpimg = imgtile.crop((pixX, pixY, pixX+pix/2, pixY+pix/2))
##        print(crpimg.width, crpimg.height)
#        img = crpimg.resize((crpimg.width*2, crpimg.height*2))

    return img
#
def fetch_scope_tiles(north_west, south_east):
    """ 北西端・南東端のタイル座標を指定して、長方形領域の標高タイルを取得 """
    assert north_west[0] == south_east[0], "タイル座標のzが一致していません"
    x_range = range(north_west[1], south_east[1]+1)
    y_range = range(north_west[2], south_east[2]+1)
    return  np.concatenate(
        [
            np.concatenate(
                [np.array(fetch_tile(north_west[0], x, y)) for y in y_range],
                axis=0
            ) for x in x_range
        ],
        axis=1
    )
#-------------Main---------------------------------
def main():
    print(sys.argv[0]+": Started @",datetime.datetime.now())

    mesh1=sys.argv[1][0:4]
    wkstartmesh1=str(int(mesh1)+100)
    wkendmesh1=str(int(mesh1)+1)
    (start_lat,start_lon)=mesh2latlon(wkstartmesh1)
    print(start_lat, start_lon)
    (end_lat,end_lon)=mesh2latlon(wkendmesh1)
    print(end_lat, end_lon)
    (startTileX,startTileY,trashPointY,trashPointX)=latlon2tilePixel(start_lat, start_lon, dtlZoomLvl)
    print(startTileX,startTileY)
    (endTileX,endTileY,trashPointY,trashPointX)=latlon2tilePixel(end_lat, end_lon, dtlZoomLvl)
    print(endTileX,endTileY)

    scope_tile = fetch_scope_tiles((dtlZoomLvl,startTileX,startTileY), (dtlZoomLvl,endTileX,endTileY))
    print(scope_tile.shape)
#    img.show()
    img_scope_tile = Image.fromarray(scope_tile)
    img_scope_tile.save("tile/tile.png")

    print(sys.argv[0]+": Finished @",datetime.datetime.now())

#---
if __name__ == '__main__':
    main()
