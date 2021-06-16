import sys
import datetime
import numpy as np
import os
import requests
import io
from PIL import Image
import matplotlib.pyplot as plt
#
import meshcd2png as m2p
## defval
# 座標を求める際に使用する定数
pix=256     # pngタイルの縦横dot数でもある
## その他
dtlZoomLvl=15   # 最も詳細な標高データが入ったzoomレベル
#
kitadake=(35.6743, 138.2388)# 北岳 15//
kannondake=(35.7017, 138.3046)# 観音岳 15/28972/12901
akadake=(35.9708, 138.3701)# 赤岳 15/28978/12870
kumotori=(35.8555, 138.9438)# 雲取山 15/29030/12883
m=0
##
def main():
    print("{}: Started @{}".format(args[0],datetime.datetime.now()))
#    (tileX, tileY, pointY, pointX)=m2p.latlon2tilePixel(kitadake[0], kitadake[1], dtlZoomLvl)
#    (tileX, tileY, pointY, pointX)=m2p.latlon2tilePixel(kannondake[0], kannondake[1], dtlZoomLvl)
#    (tileX, tileY, pointY, pointX)=m2p.latlon2tilePixel(akadake[0], akadake[1], dtlZoomLvl)
    (tileX, tileY, pointY, pointX)=m2p.latlon2tilePixel(kumotori[0], kumotori[1], dtlZoomLvl)
    print(dtlZoomLvl, tileX, tileY, pointX, pointY)
    scope_tile = m2p.fetch_scope_tiles((dtlZoomLvl, tileX-m, tileY-m), (dtlZoomLvl, tileX+m, tileY+m))  # 指定タイルを中心にした(m*2+1)**2タイル
    print(scope_tile.shape)
#    img.show()
    img_scope_tile = Image.fromarray(scope_tile)
#    img_scope_tile.save("tile/{}-{}-{}_{}-{}-{}.png".format(dtlZoomLvl, tileX-m, tileY-m, dtlZoomLvl, tileX+m, tileY+m))
    img_scope_tile.save("tile/tile.png".format(dtlZoomLvl, tileX-m, tileY-m, dtlZoomLvl, tileX+m, tileY+m))
    print("{}: Finished @{}".format(args[0],datetime.datetime.now()))
#---
if __name__ == '__main__':
    args = sys.argv
    if len(args)==1:
        m=0
    else:
        m=int(sys.argv[1])
    main()
