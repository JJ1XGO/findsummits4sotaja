import sys
import datetime
from math import pi
from math import e
#from math import atan
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

    print(sys.argv[0]+": Finished @",datetime.datetime.now())

#---
if __name__ == '__main__':
    main()
