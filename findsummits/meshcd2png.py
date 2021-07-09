import sys
import datetime
import os
import configparser
import numpy as np
import requests
import io
from PIL import Image
from math import pi,e,log,sin,tan,asin,atan,tanh
from numpy import arctanh
from concurrent.futures import ProcessPoolExecutor
# 設定ファイル読み込み
config=configparser.ConfigParser()
config.read(f"{os.path.dirname(__file__)}/config.ini")
#
# メッシュコードから緯度/経度を求める
def mesh2latlon(meshCode):
    # 文字列に変換
    meshCode = str(meshCode)
    # １次メッシュ用計算
    code_first_two = int(meshCode[0:2])
    code_last_two = int(meshCode[2:4])
    lat  = code_first_two * 2 / 3
    lon = code_last_two + 100
    # 一応、２次メッシュ/3次メッシュにも対応しておく
    if len(meshCode) > 4:
        # ２次メッシュ用計算
        if len(meshCode) >= 6:
            code_fifth = int(meshCode[4:5])
            code_sixth = int(meshCode[5:6])
            lat += code_fifth * 2 / 3 / 8
            lon += code_sixth / 8
        # ３次メッシュ用計算
        if len(meshCode) == 8:
            code_seventh = int(meshCode[6:7])
            code_eighth = int(meshCode[7:8])
            lat += code_seventh * 2 / 3 / 8 / 10
            lon += code_eighth / 8 / 10
    return(lat, lon)
# 緯度経度からピクセル座標を返す
def latlon2PixelPoint(lat, lon, z):
    pixelX = int((2**(z+7))*((lon/180)+1))
    pixelY = int((2**(z+7)/pi)*(-1*arctanh(sin(lat*pi/180))+arctanh(sin(config["VAL"].getfloat("L")*pi/180))))
    return pixelX, pixelY
# ピクセル座標から緯度経度を返す
def pixel2LatLng(z, pixelX, pixelY):
    lon=180*((pixelX/2**(z+7))-1)
    lat=180/pi*(asin(tanh(-pi/2**(z+7)*pixelY+arctanh(sin(pi/180*config["VAL"].getfloat("L"))))))
    return lat, lon
# 緯度経度からタイル座標と、そのタイル内の座標を返す
def latlon2tilePixel(lat, lon, z):
    (pixelX,pixelY)=latlon2PixelPoint(lat, lon, z)
    tileX=int(pixelX/config["VAL"].getint("PIX"))
    tileY=int(pixelY/config["VAL"].getint("PIX"))
    pointX=int(pixelX%config["VAL"].getint("PIX"))
    pointY=int(pixelY%config["VAL"].getint("PIX"))
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
    pixx=tileX*config["VAL"].getint("PIX")+pointX
    highlvltileX=int((pixx/denomin)/config["VAL"].getint("PIX"))
    highlvlpointX=int((pixx/denomin)%config["VAL"].getint("PIX"))
    pixy=tileY*config["VAL"].getint("PIX")+pointY
    highlvltileY=int((pixy/denomin)/config["VAL"].getint("PIX"))
    highlvlpointY=int((pixy/denomin)%config["VAL"].getint("PIX"))
    return (z-difflvl, highlvltileX, highlvltileY, highlvlpointY, highlvlpointX)
# 与えられた座標に対応する(config["VAL"].getint("ZOOM_LVL")-1)レベルの地理院地図タイル画像を取得し、imageと画像内の開始座標を返す
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
#        print(f"status_code={res.status_code} dem_png/{highlvlz}/{tileX}/{tileY}.png")
#        print("return N/A image")
#        img = Image.new("RGB",(256, 256),(128,0,0))
        # こちらの方が倍以上速い
        img = np.zeros((256,256,3),dtype=np.uint8)
        img[:, :, 0]=128
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
def main(meshcd,arg2=""):
    print(f"{__name__}: Started @{datetime.datetime.now()}")
#
    # 最北西と再南東の緯度/経度を得るため該当するメッシュコードを求める
    if len(meshcd)==4:
        mesh=int(meshcd)
        startMesh=mesh+100
        endMesh=mesh+1
    elif len(meshcd)==6:
        mesh=int(meshcd)
        # 8進だからややこしいけど、計算式はコレ
        startMesh=mesh+(mesh%100//10+4)//8*10000+(1-2*((mesh%100//10+4)//8))*40
        endMesh=mesh+(mesh%10+4)//8*100+(1-2*((mesh%10+4)//8))*4
#    print(startMesh,endMesh)
    (start_lat,start_lon)=mesh2latlon(startMesh)
    (end_lat,end_lon)=mesh2latlon(endMesh)
    print(f"NorthWest:({start_lat}, {start_lon}) SouthEast:({end_lat}, {end_lon})")
    (startTileX, startTileY, _, _)=latlon2tilePixel(start_lat, start_lon, config["VAL"].getint("ZOOM_LVL"))
    (endTileX, endTileY, _, _)=latlon2tilePixel(end_lat, end_lon, config["VAL"].getint("ZOOM_LVL"))
    print(f'startTile:{config["VAL"].getint("ZOOM_LVL")}/{startTileX}/{startTileY} endTile:{config["VAL"].getint("ZOOM_LVL")}/{endTileX}/{endTileY}')

    scope_tile = fetch_scope_tiles((config["VAL"].getint("ZOOM_LVL"),startTileX,startTileY), (config["VAL"].getint("ZOOM_LVL"),endTileX,endTileY))
    print(scope_tile.shape)
    img_scope_tile = Image.fromarray(scope_tile)
    os.makedirs(config["DIR"]["TILE"] ,exist_ok=True)
    result=f'{config["DIR"]["TILE"]}/{mesh}-00_{config["VAL"].getint("ZOOM_LVL")}-{startTileX}-{startTileY}_{config["VAL"].getint("ZOOM_LVL")}-{endTileX}-{endTileY}.png'
    img_scope_tile.save(result)

    print(f"{__name__}: Finished @{datetime.datetime.now()}")
    return result
#---
if __name__ == '__main__':
    print(f"{sys.argv[0]}: Started @{datetime.datetime.now()}")
    args = sys.argv[1:]
    if len(args)>0:
        ret=main(*args)
    else:
        print("2次メッシュ番号を指定してください")
    print(f"{sys.argv[0]}: Finished @{datetime.datetime.now()}")
