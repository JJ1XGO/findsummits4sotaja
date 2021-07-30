import sys
import datetime
import os
import configparser
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
import matplotlib.cm as cm
from mpl_toolkits.axes_grid1 import make_axes_locatable
#
from analyzePng import png2elevs
# 設定ファイル読み込み
config=configparser.ConfigParser()
config.read(f"{os.path.dirname(__file__)}/config.ini")
#
def main(filePath):
    print(f"{__name__}: Started @{datetime.datetime.now()}")
#
    elevs=png2elevs(filePath)
    print(f"image height:{elevs.shape[0]} width:{elevs.shape[1]}")
#
    print("generating elevation image")
# 取り敢えず単純に等高線を引いてみる
#    xx=np.linspace(0,elevs.shape[1],elevs.shape[1])
#    yy=np.linspace(0,elevs.shape[0],elevs.shape[0])
#    levels=list(np.linspace(int(elevs.min()),int(elevs.max())+2,(int(elevs.max())-int(elevs.min())+1)))
#    elevs = np.flipud(elevs)
#
    fig, ax = plt.subplots()
    fig.set_size_inches(16.53 * 2, 11.69 * 2)
#
    ls = LightSource(azdeg=180, altdeg=90)
    rgb = ls.shade(elevs, cm.rainbow)
    cs = ax.imshow(elevs)
    ax.imshow(rgb)
#
    # create an axes on the right side of ax. The width of cax will be 2%
    # of ax and the padding between cax and ax will be fixed at 0.05 inch.
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="2%", pad=0.05)
    fig.colorbar(cs, cax=cax)
#
    ax.set_xticks([])
    ax.set_yticks([])
#
    os.makedirs(config["DIR"]["IMAGE"] ,exist_ok=True)
    plt.savefig(f'{config["DIR"]["IMAGE"]}/{os.path.splitext(os.path.basename(filePath))[0]}.pdf', bbox_inches="tight")
#
if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument("filePath",help="pngファイルのファイルパス")
    args=parser.parse_args()
    main(filePath=args.filePath)
