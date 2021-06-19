import sys
import datetime
import numpy as np
#import os
#import io
from PIL import Image
import matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor
#
def getElevsPoints(elvs):
    elevs=png2elevsnp()
    return elvs,list(zip(*np.where(elevs>=elvs)))
#
def png2elevsnp():
    img = Image.open("tile/tile.png")
#    print(f"width: {img.size[0]}, height: {img.size[1]}")
    im = np.array(img)
    # RGBから標高地を計算: x = 216R + 28G + B
    elevs0=im[:, :, 0].copy()*np.power(2,16)+im[:, :, 1].copy()*np.power(2,8)+im[:, :, 2].copy()
    elevs=np.where(elevs0<2**23, elevs0/100, elevs0)           # x < 223の場合　h = xu
    elevs0=elevs
    elevs=np.where(elevs0==2**23, np.nan, elevs0)              # x = 223の場合　h = NA
    elevs0=elevs
    return np.where(elevs0>2**23, (elevs0-2**24)/100, elevs0)   # x > 223の場合　h = (x-224)u
#
def main():
    print(f"{args[0]}: Started @{datetime.datetime.now()}")
#
    elevs=png2elevsnp()
    print(elevs.shape)
    print(elevs.max(),elevs.min())
## 標高の一覧(高い順)を取得
#    elvslist=list(np.sort(np.unique(elevs))[::-1])
#    print(len(elvslist))
## 取得した標高以上の標高を持つ座標を取得
#    with ProcessPoolExecutor(max_workers=3) as executor: # max_workersは取り敢えずpythonにお任せ
#        futures = executor.map(getElevsPoints, elvslist)
## 取得した座標のダブリを排除(ダブっていたら1番標高の高いものを採用)
#    targetElvs=[]
#    for elvsPoints in futures:
#        if len(targetElvs)==0:
#            targetElvs.append(elvsPoints)
#        else:
#            if targetElvs[-1][2] != elvsPoints[2]:
#                targetElvs.append(elvsPoints)

#    targetElvs=[]
#    for i in range(len(elvslist)):
#        # 取得した標高以上の標高を持つ座標を取得
#        elvsPoints = list(zip(*np.where(elevs>=elvslist[i])))
#        # 取得した座標のダブリを排除(ダブっていたら1番標高の高いものを採用)
#        if len(targetElvs)==0:
#            targetElvs.append((elvslist[i],elvsPoints))
#        else:
#            if targetElvs[-1][1] != elvsPoints:
#                targetElvs.append((elvslist[i],elvsPoints))
#        if i < 10:
#            print(elvslist[i],elvsPoints)
#    print(len(targetElvs))

# 取り敢えず単純に等高線を引いてみる
    xx=np.linspace(0,elevs.shape[1]+1,elevs.shape[1])
    yy=np.linspace(0,elevs.shape[0]+1,elevs.shape[0])
    levels=list(np.linspace(int(elevs.min()),int(elevs.max())+2,(int(elevs.max())-int(elevs.min())+1)))
    elevs = np.flipud(elevs)

    fig, ax = plt.subplots()
    ax.contour(xx, yy, elevs, levels=levels)
    plt.show()
#
    print(f"{args[0]}: Finished @{datetime.datetime.now()}")
#---
if __name__ == '__main__':
    args = sys.argv
    main()
