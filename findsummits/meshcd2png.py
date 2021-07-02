import sys
import datetime
import numpy as np
import requests
import io
from PIL import Image
from math import pi
from math import e
from math import log
from math import sin
from math import tan
from math import asin
from math import atan
from math import tanh
from numpy import arctanh
from concurrent.futures import ProcessPoolExecutor
## defval
from . import defval
#
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
    pixelY = int( (2**(z+7)/pi) * (-1 * arctanh(sin(lat * pi/180)) + arctanh(sin(defval.const.L * pi/180))) )
    return pixelX, pixelY
# ピクセル座標から緯度経度を返す
def pixel2LatLng(z, pixelX, pixelY):
    lon = 180 * ((pixelX / 2.0**(z+7) ) - 1)
    lat = 180/pi * (asin(tanh(-pi/2**(z+7)*pixelY + arctanh(sin(pi/180*defval.const.L)))))
    return lat, lon
# 緯度経度からタイル座標と、そのタイル内の座標を返す
def latlon2tilePixel(lat, lon, z):
    (pixelX,pixelY)=latlon2PixelPoint(lat, lon, z)
    tileX=int(pixelX/defval.const.PIX)
    tileY=int(pixelY/defval.const.PIX)
    pointX=int(pixelX%defval.const.PIX)
    pointY=int(pixelY%defval.const.PIX)
#    print("({}, {}) -> {}/{}/{}:({}, {})".format(lat, lon, z, tileX, tileY, pointX, pointY))
    return tileX, tileY, pointY, pointX
# タイル座標から緯度経度を返す
def tile2latlon(z, x, y):
    lon=(x/2**z)*360-180                # 経度(東経)
    mapy=(y/2.0**z)*2*pi-pi
    lat=2*atan(e**(-mapy))*180/pi-90    # 緯度(北緯)
    return lat, lon
# 現在のタイル座標から上位レベルのタイル座標を取得する
def getHighLvlTilePoint(z, tileX, tileY, pointY, pointX, difflvl):
# 一度緯度経度に変換してから新たに求め直すと
# 誤差が生じて正しい座標が求められないケースがあるので
# タイル座標から直接計算して求める
# 1レベルより上のタイルを使うことはないと思うけど一応汎用的に使える様にしておく
    denomin=np.power(2,difflvl)
    pixx=tileX*defval.const.PIX+pointX
    highlvltileX=int((pixx/denomin)/defval.const.PIX)
    highlvlpointX=int((pixx/denomin)%defval.const.PIX)
    pixy=tileY*defval.const.PIX+pointY
    highlvltileY=int((pixy/denomin)/defval.const.PIX)
    highlvlpointY=int((pixy/denomin)%defval.const.PIX)
    return (z-difflvl, highlvltileX, highlvltileY, highlvlpointY, highlvlpointX)
# 与えられた座標に対応する(dtlZoomLvl-1)レベルの地理院地図タイル画像を取得し、imageと画像内の開始座標を返す
def fetch_rough_tile(z, x, y):
    # 1レベル上のタイル座標を求める
    (highlvlz, tileX, tileY, pointY, pointX)=getHighLvlTilePoint(z, x, y, 0, 0, 1)
    if (pointY != 0 and pointY != 128):
        print(f"Check pointY! {z}/{x}/{y}:(0, 0) -> {highlvlz}/{tileX}/{tileY}:(w-> {pointY} <-w, {pointX})")
    if (pointX != 0 and pointX != 128):
        print(f"Check pointX! {z}/{x}/{y}:(0, 0) -> {highlvlz}/{tileX}/{tileY}:({pointY}, w-> {pointX} <-w)")
    #
    url = f"https://cyberjapandata.gsi.go.jp/xyz/dem_png/{highlvlz}/{tileX}/{tileY}.png"
    res=requests.get(url)
    if res.status_code == 200:
        img = Image.open(io.BytesIO(res.content))
    else:
        print(f"status_code={res.status_code} dem_png/{highlvlz}/{tileX}/{tileY}.png")
        print("return N/A image")
        img = Image.new("RGB",(256, 256),(128,0,0))
    return img, z-1, tileX, tileY, pointX, pointY
# 与えられた座標に対応する地理院地図標高タイル画像を取得し、可能な限り標高データで埋めたimageを返す
def fetch_tile(z, x, y):
    flgGetTile=False
    for dem5lvl in (["a", "b", "c"]):
        url = f"https://cyberjapandata.gsi.go.jp/xyz/dem5{dem5lvl}_png/{z}/{x}/{y}.png"
        res=requests.get(url)
        if res.status_code == 200:
            if flgGetTile:  # 既に標高タイルが取得出来てる時は標高データがN/Aの部分だけ入れる
                tilearry = np.array(Image.open(io.BytesIO(res.content)))
                for (pixY,pixX) in list(zip(*np.where(elevsarry==2**23))):
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
#            print(f"get_status={res.status_code} {dem5lvl}/{z}/{x}/{y}")
    # ここまでで最も詳細な標高データの取得完了。標高データN/Aがあったら次のレベルの標高データで補完する
#    if flgGetTile:  # 既に標高タイルが取得出来てる時
    if flgGetTile is False:  # 標高タイルが取得出来ていない時
        imgarry = np.array(Image.new("RGB",(256, 256),(128,0,0)))
        elevsarry=imgarry[:, :, 0].copy()*np.power(2,16)
    if (elevsarry==2**23).any():    #標高データにN/Aがあったら
        (imgtile,zlvl,tileX,tileY,pixX,pixY) = fetch_rough_tile(z, x, y)    # 取り敢えず1レベル粗い標高タイルを取得して
        tilearry = np.array(imgtile)                                        # tilearryに入れる
        for (pixY,pixX) in list(zip(*np.where(elevsarry==2**23))):          # 標高データがN/Aの座標を取得して
            (highlvlz, tileXX, tileYY, pointY, pointX)=getHighLvlTilePoint(z, x, y, pixY, pixX, 1)  # 1レベル上のタイル座標を求める
            assert tileX == tileXX, "タイル座標のXが一致していません"
            assert tileY == tileYY, "タイル座標のYが一致していません"
#            print("{}/{}/{} ({}, {}) -> ({}, {}) -> {}/{}/{} ({}, {})".format(z,x,y,pixY,pixX,lat,lon,zlvl,tileX,tileY,pointY,pointX))
            imgarry[pixY,pixX] = tilearry[pointY, pointX]   # 標高データがN/Aの部分だけ入れる
        # ↑ここのforブロックを並列処理化したいが上手く実装出来ず
    img = Image.fromarray(imgarry)  # imgarryをImageに変換
    # resizeの動きが明確にわからないので取り敢えず保留
#    else:   # 標高タイルが取得出来てない時
#        (imgtile,zlvl,tileX,tileY,pixX,pixY) = fetch_rough_tile(z, x, y) # 1レベル粗い標高タイルを取得
#        print("{}/{}/{} cropping from {}/{}/{} ({}, {})".format(z, x, y, zlvl,tileX,tileY,pixX,pixY))
#        crpimg = imgtile.crop((pixX, pixY, pixX+pix/2, pixY+pix/2))
##        print(crpimg.width, crpimg.height)
#        img = crpimg.resize((crpimg.width*2, crpimg.height*2))

    return img
# 並列処理するためのwrapper
def fetch_tile_wrapper(tilecdnts):
    return fetch_tile(*tilecdnts)
# 北西端・南東端のタイル座標を指定して、長方形領域の標高タイルを取得
def fetch_scope_tiles(north_west, south_east):
    assert north_west[0] == south_east[0], "タイル座標のzが一致していません"
    x_range = range(north_west[1], south_east[1]+1)
    y_range = range(north_west[2], south_east[2]+1)
# イメージタイルを取ってくる部分を並列処理化
    tilecdnts=[[north_west[0], x, y] for y in y_range for x in x_range]
    with ProcessPoolExecutor() as executor: # max_workersは取り敢えずpythonにお任せ
        futures = executor.map(fetch_tile_wrapper, tilecdnts)
    # イメージ取り出し。もっとスマートなやり方ありそう
    tileimgs=[f for f in futures]

    return np.concatenate([
            np.concatenate([
                np.array(tileimgs[y*len(x_range)+x]) for x in range(len(x_range))
            ],axis=1) for y in range(len(y_range))
        ],axis=0)
#-------------Main---------------------------------
def main():
    print(f"{__name__}: Started @{datetime.datetime.now()}")

    mesh1=args[1][0:4]
    wkstartmesh1=str(int(mesh1)+100)
    wkendmesh1=str(int(mesh1)+1)
    (start_lat,start_lon)=mesh2latlon(wkstartmesh1)
    print(start_lat, start_lon)
    (end_lat,end_lon)=mesh2latlon(wkendmesh1)
    print(end_lat, end_lon)
    (startTileX, startTileY, _, _)=latlon2tilePixel(start_lat, start_lon, dtlZoomLvl)
    print(startTileX,startTileY)
    (endTileX, endTileY, _, _)=latlon2tilePixel(end_lat, end_lon, dtlZoomLvl)
    print(endTileX,endTileY)

    scope_tile = fetch_scope_tiles((dtlZoomLvl,startTileX,startTileY), (dtlZoomLvl,endTileX,endTileY))
    print(scope_tile.shape)
    img_scope_tile = Image.fromarray(scope_tile)
    os.makedirs(defval.const.TILE_DIR ,exist_ok=True)
    result=f"{defval.const.TILE_DIR}/{args[1]}-00_{dtlZoomLvl}-{startTileX}-{startTileY}_{dtlZoomLvl}-{endTileX}-{endTileY}.png"
    img_scope_tile.save(result)

    print(f"{__name__}: Finished @{datetime.datetime.now()}")
#---
if __name__ == '__main__':
    print(f"{sys.argv[0]}: Started @{datetime.datetime.now()}")
    args = sys.argv
    if len(args)>1:
        main()
    else:
        print("1次メッシュ番号を指定してください")
    print(f"{sys.argv[0]}: Finished @{datetime.datetime.now()}")
