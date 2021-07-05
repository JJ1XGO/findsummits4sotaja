import sys
import datetime
import os
import configparser
import numpy as np
import os
import requests
import io
from PIL import Image
import matplotlib.pyplot as plt
#
import meshcd2png as m2p
# 設定ファイル読み込み
config=configparser.ConfigParser()
config.read(f"{os.path.dirname(__file__)}/config.ini")
#
m=0
##
def main(args):
    print(f"{__name__}: Started @{datetime.datetime.now()}")
#
    if len(args)==2:
        m=0
    else:
        m=int(args[2])
    lon,lat=config["COORD"][f"{args[1]}"].split(",")
    (tileX, tileY, pointY, pointX)=m2p.latlon2tilePixel(float(lat), float(lon), config["VAL"].getint("ZOOM_LVL"))
    print(f'{args[1]} pixel coordinate:{config["VAL"].getint("ZOOM_LVL")}/{tileX}/{tileY} ({pointX}, {pointY})')
    scope_tile = m2p.fetch_scope_tiles((config["VAL"].getint("ZOOM_LVL"), tileX-m, tileY-m), (config["VAL"].getint("ZOOM_LVL"), tileX+m, tileY+m))  # 指定タイルを中心にした(m*2+1)**2タイル
    print(scope_tile.shape)
#    img.show()
    img_scope_tile = Image.fromarray(scope_tile)
    os.makedirs(config["DIR"]["TILE"] ,exist_ok=True)
    result=f'{config["DIR"]["TILE"]}/0000-00_{config["VAL"].getint("ZOOM_LVL")}-{tileX-m}-{tileY-m}_{config["VAL"].getint("ZOOM_LVL")}-{tileX+m}-{tileY+m}.png'
    img_scope_tile.save(result)
    print(result)
#
    print(f"{__name__}: Finished @{datetime.datetime.now()}")
#---
if __name__ == '__main__':
    print(f"{sys.argv[0]}: Started @{datetime.datetime.now()}")
    args = sys.argv
    if len(args)==1:
        print("山名パラメータを指定してください")
    else:
        main(args)
    print(f"{sys.argv[0]}: Finished @{datetime.datetime.now()}")
