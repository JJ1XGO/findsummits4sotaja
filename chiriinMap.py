import sys
import datetime
import numpy as np
import os
import requests
import io
from PIL import Image
import matplotlib.pyplot as plt
#
import meshcd2png
## defval
# 座標を求める際に使用する定数
pix=256     # pngタイルの縦横dot数でもある
## その他
dtlZoomLvl=15# 最も詳細な標高データが入ったzoomレベル

def fetch_rough_tile(z, x, y):
    """
    与えられた座標に対応する(dtlZoomLvl-1)レベルの地理院地図タイル画像を取得し、imageと画像内の開始座標を返す
    """
    # 与えられた座標の緯度経度を求める
    (lat, lon)=meshcd2png.pixel2LatLng(z, pix*x, pix*y)
    # 1レベル下のタイル座標を求める
    (tileX, tileY, pointY, pointX)=meshcd2png.latlon2tilePixel(lat, lon, z-1)
    if (pointY != 0 and pointY != 128):
        print("Check pointY! {}/{}/{}:(0, 0) -> ({}, {}) -> {}/{}/{}:({}, ww{}ww)".format(z, x, y, lat, lon, z-1, tileX, tileY, pointX, pointY))
    if (pointX != 0 and pointX != 128):
        print("Check pointX! {}/{}/{}:(0, 0) -> ({}, {}) -> {}/{}/{}:(ww{}ww, {})".format(z, x, y, lat, lon, z-1, tileX, tileY, pointX, pointY))
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
            (lat, lon)=meshcd2png.pixel2LatLng(z, pix*x+pixX, pix*y+pixY)   # その座標の緯度経度を求め
            # 1レベル下のタイル座標を求める
            (tileXX, tileYY, pointY, pointX)=meshcd2png.latlon2tilePixel(lat, lon, z-1)   # 緯度経度から取得したタイルのどの位置に当たるかを求める
            assert tileX == tileXX, "タイル座標のXが一致していません"
            assert tileY == tileYY, "タイル座標のYが一致していません"
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
#
def main():
    print(sys.argv[0]+": Started @",datetime.datetime.now())
    kumotori=(35.8555, 138.9438)# 雲取山 15/29030/12883
    akadake=(35.9708, 138.3701)# 赤岳 15/28978/12870
    m=10
#    (tileX, tileY, pointY, pointX)=meshcd2png.latlon2tilePixel(kumotori[0], kumotori[1], dtlZoomLvl)
    (tileX, tileY, pointY, pointX)=meshcd2png.latlon2tilePixel(akadake[0], akadake[1], dtlZoomLvl-1)
    print(dtlZoomLvl-1, tileX, tileY, pointX, pointY)
    (tileX, tileY, pointY, pointX)=meshcd2png.latlon2tilePixel(akadake[0], akadake[1], dtlZoomLvl)
    print(dtlZoomLvl, tileX, tileY, pointX, pointY)
    scope_tile = fetch_scope_tiles((dtlZoomLvl, tileX-m, tileY-m), (dtlZoomLvl, tileX+m, tileY+m))  # 指定タイルを中心にした(m*2+1)**2タイル
    print(scope_tile.shape)
#    img.show()
    img_scope_tile = Image.fromarray(scope_tile)
    img_scope_tile.save("tile/tile.png")
    print(sys.argv[0]+": Finished @",datetime.datetime.now())
#---
if __name__ == '__main__':
    main()
