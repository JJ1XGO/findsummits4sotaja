import sys
import datetime
import numpy as np
import os
#import io
from PIL import Image
import cv2
from operator import itemgetter
from scipy.ndimage.filters import maximum_filter
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
# ピークを見つけ出す
def detectPeaksCoords(image, filter_size=20):   #filter_size*5m四方の範囲でピークを見つけ出す
    local_max = maximum_filter(image, footprint=np.ones((filter_size, filter_size)), mode='constant')
    detected_peaks = np.ma.array(image, mask=~(image == local_max))

    # 小さいピーク値を排除（150m以下のピークは排除）
    temp = np.ma.array(detected_peaks, mask=~(detected_peaks >= 150))
    peaks_index = np.where(temp.mask != True)
    return list(zip(*np.where(temp.mask != True)))
#
def main():
    print(f"{args[0]}: Started @{datetime.datetime.now()}")
#
    elevs=png2elevsnp()
    print(elevs.shape)
    print(elevs.max(),elevs.min())
# ピーク(候補)の一覧作成
    peaksList=[]
    for yy,xx in detectPeaksCoords(elevs):
        peaksList.append((elevs[yy][xx],xx,yy))
    peaksList.sort(key=itemgetter(0,1,2), reverse=True)
    print(len(peaksList))
    print(peaksList)
# 標高の一覧(高い順)を取得
    elvslist=list(np.unique(elevs))[::-1]
    print(len(elvslist))
    for el in elvslist[0:10]:
        if el > peaksList[1][0]:    # ピーク(候補)の2番目まで飛ばして良い
            continue
#    for el,xx,yy in peaksList[:5]:
#        img=Image.fromarray(np.uint8(np.where(elevs>=el,0,255)))
#        img=Image.fromarray(np.uint8(np.where(elevs>=el,255,0)))
        img=np.uint8(np.where(elevs>=el,255,0))
        # 輪郭を抽出する
        contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # 輪郭を描画する
        contimg=np.zeros(img.shape)
        cv2.drawContours(contimg, contours, -1, 255, thickness=1)
        # ピークをプロットして
        for hh,xx,yy in peaksList:
            if el > hh:
                break
            contimg[yy][xx]=255
        # 再度輪郭を抽出する
        img=np.uint8(contimg)
        contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        print(hierarchy.shape)
        print(hierarchy)
        print(len(contours))
        print(contours)
        contimg=np.zeros(img.shape)
        cv2.drawContours(contimg, contours, -1, 255, thickness=1)
        cv2.imwrite(f"test/{el}.png",contimg)
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
#    plt.show()
#
    print(f"{args[0]}: Finished @{datetime.datetime.now()}")
#---
if __name__ == '__main__':
    args = sys.argv
    main()
