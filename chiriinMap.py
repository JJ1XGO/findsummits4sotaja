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
    与えられた座標に対応する(dtlZoomLvl-1)レベルの地理院地図タイル画像を取得し、該当範囲の画像を切り取ってリサイズしたものをimageで返す
    """
    # 与えられた座標の緯度経度を求める
    (lat, lon)=meshcd2png.pixel2LatLng(z, pix*x, pix*y)
    # 1レベル下のタイル座標を求める
    (tileX, tileY, pointX, pointY)=meshcd2png.latlon2tilePixel(lat, lon, z-1)
    if (pointX != 0 and pointX != 128):
        print("Check pointX! {}/{}/{}:(0, 0) -> ({}, {}) -> {}/{}/{}:(ww{}ww, {})".format(z, x, y, lat, lon, z-1, tileX, tileY, pointX, pointY))
    if (pointY != 0 and pointY != 128):
        print("Check pointY! {}/{}/{}:(0, 0) -> ({}, {}) -> {}/{}/{}:({}, ww{}ww)".format(z, x, y, lat, lon, z-1, tileX, tileY, pointX, pointY))
    #
    url = "https://cyberjapandata.gsi.go.jp/xyz/dem_png/{}/{}/{}.png".format(z-1, tileX, tileY)
    res=requests.get(url)
    if res.status_code == 200:
        crpimg = Image.open(io.BytesIO(res.content)).crop((pointX, pointY, pointX+pix/2, pointY+pix/2))
        print(crpimg.width, crpimg.height)
        img = crpimg.resize((crpimg.width*2, crpimg.height*2))
    else:
        print("status_code={} dem_png/{}/{}/{}".format(res.status_code, z-1, tileX, tileY))
        print("return N/A image")
        img = Image.new("RGB",(256, 256),(128,0,0))
    return img
#
def fetch_tile(z, x, y):
    """
    与えられた座標に対応する地理院地図タイル画像を取得し、imageで返す
    """
#    url = "https://cyberjapandata.gsi.go.jp/xyz/dem5a_png/{}/{}/{}.png".format(z, x, y)
#    img = Image.open(io.BytesIO(requests.get(url).content))
    for dem5lvl in (["a", "b", "c"]):
        url = "https://cyberjapandata.gsi.go.jp/xyz/dem5{}_png/{}/{}/{}.png".format(dem5lvl, z, x, y)
        res=requests.get(url)
        if res.status_code == 200:
            img = Image.open(io.BytesIO(res.content))
            break
        else:
            print("status_code={} {}/{}/{}/{}".format(res.status_code,dem5lvl, z, x, y))
    else:
        img = fetch_rough_tile(z, x, y)
    '''
# pngの確認テスト
    print("width: {}, height: {}".format(img.size[0], img.size[1]))
    im = np.array(img)

    im_R = im.copy()
    im_R[:, :, (1, 2)] = 0
    im_G = im.copy()
    im_G[:, :, (0, 2)] = 0
    im_B = im.copy()
    im_B[:, :, (0, 1)] = 0
    # 横に並べて結合（どれでもよい）
    #im_RGB = np.concatenate((im_R, im_G, im_B), axis=1)
    im_RGB = np.hstack((im,im_R, im_G, im_B))
    # im_RGB = np.c_['1', im_R, im_G, im_B]
    pil_img_RGB = Image.fromarray(im_RGB)
    pil_img_RGB.save('tile/tile_rgb.png')
#    pil_img_RGB.save('tile/tile_rgb.jpg')
    '''
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
    kumotori=(29030,12883)# 雲取山 15/29030/12883
    akadake=(28978,12870)# 赤岳 15/28978/12870
    m=20
#    fetch_tile(dtlZoomLvl,28978,12870)
#    scope_tile = fetch_scope_tiles((dtlZoomLvl, kumotori[0]-m, kumotori[1]-m), (dtlZoomLvl, kumotori[0]+m, kumotori[1]+m))  # 雲取山タイルを中心にした(m*2+1)**2タイル
    scope_tile = fetch_scope_tiles((dtlZoomLvl, akadake[0]-m, akadake[1]-m), (dtlZoomLvl, akadake[0]+m, akadake[1]+m))  # 赤岳タイルを中心にした(m*2+1)**2タイル
    print(scope_tile.shape)
#    img.show()
    img_scope_tile = Image.fromarray(scope_tile)
    img_scope_tile.save("tile/tile.png")
    print(sys.argv[0]+": Finished @",datetime.datetime.now())
#---
if __name__ == '__main__':
    main()
