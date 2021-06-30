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
import defval
#
kitadake=(35.6743, 138.2388)    # 北岳 15/28966/12904 (24, 205)
kannondake=(35.7017, 138.3046)  # 観音岳 15/28972/12901 (6, 202)
akanuke=(35.7104, 138.2969)     # 赤抜沢の頭 15/
akadake=(35.9708, 138.3701)     # 赤岳 15/28978/12870 (207, 193)
kumotori=(35.8555, 138.9438)    # 雲取山 15/29030/12883 (196, 249)
m=0
##
def main():
    print("{}: Started @{}".format(args[0],datetime.datetime.now()))
#    (tileX, tileY, pointY, pointX)=m2p.latlon2tilePixel(kitadake[0], kitadake[1], defval.const.ZOOM_LVL)
#    (tileX, tileY, pointY, pointX)=m2p.latlon2tilePixel(kannondake[0], kannondake[1], defval.const.ZOOM_LVL)
#    (tileX, tileY, pointY, pointX)=m2p.latlon2tilePixel(akanuke[0], akanuke[1], defval.const.ZOOM_LVL)
    (tileX, tileY, pointY, pointX)=m2p.latlon2tilePixel(akadake[0], akadake[1], defval.const.ZOOM_LVL)
#    (tileX, tileY, pointY, pointX)=m2p.latlon2tilePixel(kumotori[0], kumotori[1], defval.const.ZOOM_LVL)
    print(defval.const.ZOOM_LVL, tileX, tileY, pointY, pointX)
    scope_tile = m2p.fetch_scope_tiles((defval.const.ZOOM_LVL, tileX-m, tileY-m), (defval.const.ZOOM_LVL, tileX+m, tileY+m))  # 指定タイルを中心にした(m*2+1)**2タイル
    print(scope_tile.shape)
#    img.show()
    img_scope_tile = Image.fromarray(scope_tile)
    img_scope_tile.save(f"tile/0000-00_{defval.const.ZOOM_LVL}-{tileX-m}-{tileY-m}_{defval.const.ZOOM_LVL}-{tileX+m}-{tileY+m}.png")
    print(f"{args[0]}: Finished @{datetime.datetime.now()}")
#---
if __name__ == '__main__':
    args = sys.argv
    if len(args)==1:
        m=0
    else:
        m=int(sys.argv[1])
    main()
