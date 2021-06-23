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
## defval
minimumProminence=150  # プロミネンス(ピークとコルの標高差)最小値
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

    # 小さいピーク値を排除（minimumProminenceより小さなピークは排除）
    temp = np.ma.array(detected_peaks, mask=~(detected_peaks >= minimumProminence))
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
    peakCandidates=[]
    for yy,xx in detectPeaksCoords(elevs):
        peakCandidates.append((elevs[yy][xx],(xx,yy)))
    peakCandidates.sort(key=itemgetter(0,1), reverse=True)
    print(len(peakCandidates))
    print(peakCandidates)
    # 重複排除(dem10から取った標高は2*2の4ピクセルが固まっているので)
    uniqPeakCandidates=[]
    for i,pc in enumerate(peakCandidates):
        if i != 0:
            if prepc[0]==pc[0]: # 同じ標高で4つ固まっていたら南東の座標を採用
                if prepc[1][0]==pc[1][0] and prepc[1][1]==pc[1][1]+1:
                    continue
                if prepc[1][0]==pc[1][0]+1 and prepc[1][1]==pc[1][1]:
                    continue
                if prepc[1][0]==pc[1][0]+1 and prepc[1][1]==pc[1][1]+1:
                    continue
        uniqPeakCandidates.append(pc)
        prepc=pc
    peakCandidates=uniqPeakCandidates
    del uniqPeakCandidates
    print(len(peakCandidates))
    print(peakCandidates)
# 標高の一覧(高い順)を取得
    elvslist=list(np.unique(elevs))[::-1]
    print(len(elvslist))
    for el in elvslist[0:50]:
        if el > peakCandidates[1][0]:    # ピーク(候補)の2番目まで飛ばして良い
            continue
#    for el,xx,yy in peakCandidates[:5]:
#        img=Image.fromarray(np.uint8(np.where(elevs>=el,0,255)))
#        img=Image.fromarray(np.uint8(np.where(elevs>=el,255,0)))
        img=np.uint8(np.where(elevs>=el,255,0))
        # 輪郭を抽出する。最初はベタ塗りの画像から輪郭だけ抽出したいので
        # 階層問わず(cv2.RETR_LIST)輪郭のみのメモリ節約モード(cv2.CHAIN_APPROX_SIMPLE)
        contours, hierarchy = cv2.findContours(img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        # 輪郭を描画する
        contimg=np.zeros(img.shape)
        cv2.drawContours(contimg, contours, -1, 255, thickness=1)
        # ピークをプロットして
        for hh,xy in peakCandidates:
            if el > hh:
                break
            contimg[xy[1]][xy[0]]=255
        img=np.uint8(contimg)   # 輪郭とピークだけの画像にする
        # 再度輪郭を抽出する。2回目は階層構造と詳細な座標を取得したいので
        # 階層あり(cv2.RETR_TREE)の描画プロット全て抽出(cv2.CHAIN_APPROX_NONE)
        contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        print(hierarchy.shape)
        print(hierarchy)
#        print(contours)
        contimg=np.zeros(img.shape)
        cv2.drawContours(contimg, contours, -1, 255, thickness=1)
        cv2.imwrite(f"test/{el}.png",contimg)
#        for i in range(len(contours)):
#            contimg=np.zeros(img.shape)
#            cv2.drawContours(contimg, contours, i, 255, thickness=1)
#            cv2.imwrite(f"test/{el}-{i}.png",contimg)
        # 家系図を作成
        familyTree=[]
        parentCnt=0
        nextHrrchy=0
        while nextHrrchy != -1:
            parentCnt+=1
            peakCnt=0
            currentHrrchy=nextHrrchy
            hrrchy=hierarchy[0][currentHrrchy]
            if hrrchy[3]== -1:  # 親がいないのが親
                if hrrchy[2] == -1: # 子がいなければおそらくピーク
                    hclass="maybe peak"
                else:
                    hclass="contour outside"    # 子がいれば等高線の外枠
                peakNo=-1
                familyTree.append([currentHrrchy,f"{parentCnt*10000:0=7}",hclass,peakCnt,peakNo])
                if hrrchy[2] != -1: # 子がいれば子に入る
                    childCnt=0
                    nextHrrchy=hrrchy[2]
                    while nextHrrchy != -1:
                        childCnt+=1
                        currentHrrchy=nextHrrchy
                        hrrchy=hierarchy[0][currentHrrchy]
                        childNo=int(familyTree[hrrchy[3]][1])+childCnt*100
                        if hrrchy[2] == -1: # 孫がいなければ通常の等高線内枠
                            hclass="maybe contour inside"
                            print(currentHrrchy,contours[currentHrrchy])
                            # ピークの標高に近いうちは輪郭の上に乗っている事がある。ピーク候補がいるか存在チェック
                            for i,pc in enumerate(peakCandidates):
                                if pc[0]<el: # 現在の標高より低いピークは対象外
                                    break
                                for ii in range(len(contours[currentHrrchy])):
                                    if contours[currentHrrchy][ii][0][0]==pc[1][0] and contours[currentHrrchy][ii][0][1]==pc[1][1]:
                                        print(f"found peak! {i} {pc}")
                                        hclass="contour inside incld/peak"
                                        peakNo=i
                                        peakCnt+=1
                                        break
                                else:
                                    continue
                                break
                        else:
                            hclass="maybe contour inside w/peak"    # 孫がいればピークを含む等高線の内枠(多分)
                        familyTree.append([currentHrrchy,f"{childNo:0=7}",hclass,1,peakNo])
                        if hrrchy[2] != -1: # 孫がいれば孫に入る
                            grandChildCnt=0
                            nextHrrchy=hrrchy[2]
                            while nextHrrchy != -1:
                                grandChildCnt+=1
                                currentHrrchy=nextHrrchy
                                hrrchy=hierarchy[0][currentHrrchy]
                                granChildNo=int(familyTree[hrrchy[3]][1])+grandChildCnt
                                if hrrchy[2] == -1: # ひ孫がいなければ多分ピーク
                                    hclass="maybe peak"
                                    print(currentHrrchy,contours[currentHrrchy])
                                    # ピーク候補がいるか存在チェック
                                    for i,pc in enumerate(peakCandidates):
                                        if pc[0]<el: # 現在の標高より低いピークは対象外
                                            break
                                        for ii in range(len(contours[currentHrrchy])):
                                            if contours[currentHrrchy][ii][0][0]==pc[1][0] and contours[currentHrrchy][ii][0][1]==pc[1][1]:
                                                print(f"found peak! {i} {pc}")
                                                hclass="peak"
                                                peakNo=i
                                                peakCnt+=1
                                                break
                                        else:
                                            continue
                                        break
                                else:
                                    print(familyTree)
                                    print(currentHrrchy,childNo)
                                    assert False, "ひ孫はひ孫は想定外。内容要確認"
                                familyTree.append([currentHrrchy,f"{granChildNo:0=7}",hclass,1,peakNo])
                                nextHrrchy=hrrchy[0]
                            else:
                                hrrchy=hierarchy[0][hrrchy[3]]  # 子に戻る
                        nextHrrchy=hrrchy[0]
                    else:
                        print(familyTree[hrrchy[3]])
                        familyTree[hrrchy[3]][3]=peakCnt    # 親にピークを見つけたカウントをセット
                        hrrchy=hierarchy[0][hrrchy[3]]  # 親に戻る
            nextHrrchy=hrrchy[0]
        print(el,familyTree)
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
