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
    print(f"{args[0]}: Started @{datetime.datetime.now()}")
    img = Image.open("tile/tile.png")
    print("width: {}, height: {}".format(img.size[0], img.size[1]))
    im = np.array(img)
    # RGBから標高地を計算: x = 216R + 28G + B
    elevs0=im[:, :, 0].copy()*np.power(2,16)+im[:, :, 1].copy()*np.power(2,8)+im[:, :, 2].copy()
    elevs=np.where(elevs0<2**23, elevs0/100, elevs0)           # x < 223の場合　h = xu
    elevs0=elevs
    elevs=np.where(elevs0==2**23, np.nan, elevs0)              # x = 223の場合　h = NA
    elevs0=elevs
    elevs=np.where(elevs0>2**23, (elevs0-2**24)/100, elevs0)   # x > 223の場合　h = (x-224)u
    print(elevs.shape)
    print(elevs.max(),elevs.min())
#
    # 取り敢えず
    xx=np.linspace(0,img.size[0]-1,img.size[0])
    yy=np.linspace(0,img.size[1]-1,img.size[1])
    XX,YY=np.meshgrid(xx,yy)
    zmax=elevs.max()

    step=10  #5/10   # 細かく設定した方が精度が良いそうだが時間が掛かる。取り敢えず1m毎に設定
#    peaks,idmap,promap,parentmap=pp2d.getProminence(elevs,step,lats=yy,lons=xx,min_area=None,
    peaks,idmap,promap,parentmap=pp2d.getProminence(elevs,step,
            min_depth=150,include_edge=True)

    print ("getProminence finished")
#    print(f"type(peaks):{type(peaks)}")         # <class 'dict'>
#    print(f"type(idmap):{type(idmap)}")         # <class 'numpy.ndarray'>
#    print(f"type(promap):{type(promap)}")       # <class 'numpy.ndarray'>
#    print(f"type(parentmap):{type(parentmap)}") # <class 'numpy.ndarray'>
    print(f"elevs.max():{elevs.max()}, (y, x):{list(zip(*np.where(elevs==elevs.max())))}")
    for kk,vv in peaks.items():
        print(len(vv))
        for vvk,vvv in vv.items():
            if vvk != "contours" and vvk !="contour":
                print(vvk,vvv)
#
    fig, ax = plt.subplots()
    ls = LightSource(azdeg=180, altdeg=15)
    rgb = ls.shade(elevs, cm.rainbow)
    cs = ax.imshow(elevs)
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
    print(f"{args[0]}: Finished @{datetime.datetime.now()}")
#---
if __name__ == '__main__':
    args = sys.argv
    main()
