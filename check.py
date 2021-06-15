import sys
import datetime
#import numpy as np
#import os
#import requests
#import io
#from PIL import Image
#import matplotlib.pyplot as plt
#
import meshcd2png as m2p
## defval
# その他
dtlZoomLvl=15   # 最も詳細な標高データが入ったzoomレベル
uppercorner=(15, 28954, 12902)
lowercorner=(15, 28955, 12903)
#
def main():
    print("{}: Started @{}".format(args[0],datetime.datetime.now()))
    assert uppercorner[0] == lowercorner[0], "タイル座標のzが一致していません"
    z=uppercorner[0]

    for y in (range(uppercorner[2],lowercorner[2]+1)):
        for x in (range(uppercorner[1],lowercorner[1]+1)):
            for (yy,xx) in ((0,0),(0,255),(255,0),(255,255)):
                # タイル座標から上位レベルでのタイル座標を求める
                (highlvlz, highlvltileX, highlvltileY, highlvlpointY, highlvlpointX)=m2p.getHighLvlTilePoint(z, x, y, yy, xx, 1)
                print("{}/{}/{} ({}, {}) -> {}/{}/{} ({}, {})".format(z, x, y, yy, xx, highlvlz, highlvltileX, highlvltileY, highlvlpointY, highlvlpointX))
                (highlvlz, highlvltileX, highlvltileY, highlvlpointY, highlvlpointX)=m2p.getHighLvlTilePoint(z, x, y, yy, xx, 2)
                print("{}/{}/{} ({}, {}) -> {}/{}/{} ({}, {})".format(z, x, y, yy, xx, highlvlz, highlvltileX, highlvltileY, highlvlpointY, highlvlpointX))
#
    print("{}: Finished @{}".format(args[0],datetime.datetime.now()))
#---
if __name__ == '__main__':
    args = sys.argv
    main()
