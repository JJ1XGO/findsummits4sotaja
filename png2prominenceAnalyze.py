import sys
import datetime
import numpy as np
import os
import io
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import LightSource
from mpl_toolkits.axes_grid1 import make_axes_locatable
#
import peak_prominence2d as pp2d

def main():
    print("{}: Started @{}".format(args[0],datetime.datetime.now()))
    img = Image.open("tile/tile.png")
    print("width: {}, height: {}".format(img.size[0], img.size[1]))
    im = np.array(img)
    # RGBから標高地を計算: x = 216R + 28G + B
    elevs0=im[:, :, 0].copy()*np.power(2,16)+im[:, :, 1].copy()*np.power(2,8)+im[:, :, 2].copy()
    elevs1=np.where(elevs0<2**23, elevs0/100, elevs0)           # x < 223の場合　h = xu
    del elevs0
    elevs2=np.where(elevs1==2**23, np.nan, elevs1)              # x = 223の場合　h = NA
    del elevs1
    elevs3=np.where(elevs2>2**23, (elevs2-2**24)/100, elevs2)   # x > 223の場合　h = (x-224)u
    del elevs2
    print(elevs3.shape)
    print(elevs3.max(),elevs3.min())
#
    # 取り敢えず
    xx=np.linspace(0,img.size[0],img.size[0])
    yy=np.linspace(0,img.size[1],img.size[1])
    XX,YY=np.meshgrid(xx,yy)
    zmax=elevs3.max()

    step=1  #5/10   # 細かく設定した方が精度が良いそうだが時間が掛かる。取り敢えず1m毎に設定
    peaks,idmap,promap,parentmap=pp2d.getProminence(elevs3,step,lats=yy,lons=xx,min_area=None,
            min_depth=150,include_edge=True)

    print ("getProminence finished")
#    print(f"type(peaks):{type(peaks)}")         # <class 'dict'>
#    print(f"type(idmap):{type(idmap)}")         # <class 'numpy.ndarray'>
#    print(f"type(promap):{type(promap)}")       # <class 'numpy.ndarray'>
#    print(f"type(parentmap):{type(parentmap)}") # <class 'numpy.ndarray'>
    for kk,vv in peaks.items():
        print(len(vv))
        for pdatadtl in vv:
            print(f"id:{vv['id']}")
            print(f"height:{vv['height']}")
            print(f"col_level:{vv['col_level']}")
            print(f"prominence:{vv['prominence']}")
            print(f"area:{vv['area']}")
#            print(f"contours:{vv['contours']}")
#            print(f"contour:{vv['contour']}")
            print(f"center:{vv['center']}")
            print(f"parent:{vv['parent']}")
#
    fig, ax = plt.subplots()
    fig.set_size_inches(16.53 * 2, 11.69 * 2)

    ls = LightSource(azdeg=180, altdeg=15)
    rgb = ls.shade(elevs3, cm.rainbow)
    cs = ax.imshow(elevs3)
    ax.imshow(rgb)

# create an axes on the right side of ax. The width of cax will be 2%
# of ax and the padding between cax and ax will be fixed at 0.05 inch.
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="2%", pad=0.05)
    fig.colorbar(cs, cax=cax)

    ax.set_xticks([])
    ax.set_yticks([])

    plt.savefig("tile/tile.pdf", bbox_inches="tight")
#    plt.show(block=False)
#    plt.show()
    print("{}: Finished @{}".format(args[0],datetime.datetime.now()))
#---
if __name__ == '__main__':
    args = sys.argv
    main()
