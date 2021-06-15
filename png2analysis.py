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
import meshcd2png

def main():
    print(sys.argv[0]+": Started @",datetime.datetime.now())
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
    plt.show()
    print(sys.argv[0]+": Finished @",datetime.datetime.now())
#---
if __name__ == '__main__':
    main()
