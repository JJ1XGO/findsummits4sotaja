import sys
import datetime
from math import pi
from math import e
#from math import atan
from math import log
from math import tan
#from math import sin
#from numpy import arctanh

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

def latlon2tile(lat, lon, z):
    x = int((lon / 180 + 1) * 2**z / 2) # x座標
    y = int(((-log(tan((45 + lat / 2) * pi / 180)) + pi) * 2**z / (2 * pi))) # y座標
    return x, y

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
    (start_x,start_y)=latlon2tile(start_lat, start_lon, 15)   # zoomレベルは取り敢えず15固定
    print(start_x, start_y)
    (end_x,end_y)=latlon2tile(end_lat, end_lon, 15)   # zoomレベルは取り敢えず15固定 終点は返ってくる座標の左上なのでx,yそれぞれ-1するのを忘れずに
    print(end_x, end_y)

    print(sys.argv[0]+": Finished @",datetime.datetime.now())

#---
if __name__ == '__main__':
    main()
