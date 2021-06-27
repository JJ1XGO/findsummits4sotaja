import sys
import datetime
import numpy as np
import os
#import io
import collections
import math
from decimal import Decimal
import cv2
from operator import itemgetter
from scipy.ndimage.filters import maximum_filter
import matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor
## defval
minimumProminence=150   # プロミネンス(ピークとコルの標高差)最小値
filter_size=32
# イメージの中をfilter_size(ピクセル)毎に分割し、その区画毎にピークを見つけ出すためのパラメータ
# 標高タイルは一辺が256ピクセルで、レベル15だと1つのタイルの中にピークはせいぜい1〜2座だと思うので、
# 一辺を2分割した128くらいで良いと思うが、一応32をデフォルト値としておく。
# テスト時は16で実施。
#
def png2elevs(file):
    img = cv2.imread(file)
    # RGBから標高地を計算: x = 2**16R + 2**8G + B
    # openCVではGBRの順番になるので注意
    elevs0=img[:, :, 2].copy()*np.power(2,16)+img[:, :, 1].copy()*np.power(2,8)+img[:, :, 0].copy()
    elevs=np.where(elevs0<2**23, elevs0/100, elevs0)           # x < 223の場合　h = xu
    elevs0=elevs
    elevs=np.where(elevs0==2**23, np.nan, elevs0)              # x = 223の場合　h = NA
    elevs0=elevs
    elevs=np.where(elevs0>2**23, (elevs0-2**24)/100, elevs0)   # x > 223の場合　h = (x-224)u
    return elevs
# ピークを見つけ出す
def detectPeaksCoords(image):   # filter_size*5m四方の範囲でピークを見つけ出す
    local_max = maximum_filter(image, footprint=np.ones((filter_size, filter_size)), mode='constant')
    detected_peaks = np.ma.array(image, mask=~(image == local_max))

    # 小さいピーク値を排除（minimumProminenceより小さなピークは排除）
    temp = np.ma.array(detected_peaks, mask=~(detected_peaks >= minimumProminence))
    peaks_index = np.where(temp.mask != True)
    return list(zip(*np.where(temp.mask != True)))
#
def main(file="tile/tile.png", verbose=False, debug=False):
    print(f"{args[0]}: Started @{datetime.datetime.now()}")
#
    elevs=png2elevs(file)
    print(elevs.shape)
# ピーク(候補)の一覧作成
    peakCandidates=[]
    for yy,xx in detectPeaksCoords(elevs):
        peakCandidates.append((elevs[yy][xx],(xx,yy)))
    peakCandidates.sort(key=itemgetter(0,1), reverse=True)
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
    for i,pc in enumerate(peakCandidates):
        print(f"peakCandidates:{i} {pc}")
# 標高の一覧(高い順)を取得
    print(elevs.max(),elevs.min())
    elvslist=list(np.unique(elevs))[::-1]
    print(len(elvslist))
    peakColProminence=[]
    for el in elvslist:
        # ピーク(候補)の2番目まで飛ばして良い
        if len(peakCandidates)>1 and el > peakCandidates[1][0]:
            continue
        # ピーク(候補)が残り1つになったら標高の1番低い所まで飛ばして良い
        if len(peakCandidates)==1 and el > elvslist[-1]:
            continue
#        debug = True if el==2674.02 else False
        if verbose:
            print(f"analyzing elevation {el} m")
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
        if debug:
            print(hierarchy)
#        contimg=np.zeros(img.shape)
#        cv2.drawContours(contimg, contours, -1, 255, thickness=1)
#        cv2.imwrite(f"test/{el}.png",contimg)
#        for i in range(len(contours)):
#            contimg=np.zeros(img.shape)
#            cv2.drawContours(contimg, contours, i, 255, thickness=1)
#            cv2.imwrite(f"test/{el}-{i}.png",contimg)
        # 先ずは何世代までいるか確認
        nextHrrchy=0
        genCnt=0
        for hrrchy in hierarchy[0]:
            if hrrchy[2]== -1:  # 子供がいないのが対象
                genCntt=1
                nextHrrchy=hrrchy
                while nextHrrchy[3] != -1:
                    genCntt+=1
                    currentHrrchy=nextHrrchy
                    nextHrrchy=hierarchy[0][currentHrrchy[3]]
                if genCnt < genCntt:
                    genCnt=genCntt
        #親世代だけだったら子供が出てくるまで飛ばす
        if debug:
            print(f"{el} 世代階層:{genCnt}")
        if genCnt==1:
            continue
        # 家系図を作成
        familyTree=[]
        parentCnt=0
#        while nextHrrchy != -1:
        for hi,hrrchy in enumerate(hierarchy[0]):
            if hrrchy[3]== -1:  # 親だったら(親がいないのが親)
                selfGeneration=1
                parentCnt+=1
                childCnt=0
                gChildCnt=0
                g2gChildCnt=0   # ひ孫用カウンタ
                g3gChildCnt=0   # 玄孫用カウンタ
                g4gChildCnt=0   # 来孫用カウンタ
            else:   # 親以外
                if hrrchy[1]==-1:   # 自分が長兄だったら
                    # 親の番号から自分の世代を求める
                    myPfNumber=int(familyTree[hrrchy[3]][1])
                    if myPfNumber%(10**((genCnt-1)*2))==0:  # 自分の親が親世代なら
                        selfGeneration=2
                        childCnt+=1
                    elif myPfNumber%(10**((genCnt-2)*2))==0:  # 自分の親が子世代なら
                        selfGeneration=3
                        gChildCnt+=1
                    elif myPfNumber%(10**((genCnt-3)*2))==0:  # 自分の親が孫世代なら
                        selfGeneration=4
                        g2gChildCnt+=1
                    elif myPfNumber%(10**((genCnt-4)*2))==0:  # 自分の親が玄孫世代なら
                        selfGeneration=5
                        g3gChildCnt+=1
                    elif myPfNumber%(10**((genCnt-5)*2))==0:  # 自分の親が来孫世代なら
                        selfGeneration=6
                        g4gChildCnt+=1
                    else:
                        for i in range(len(contours)):
                            contimg=np.zeros(img.shape)
                            cv2.drawContours(contimg, contours, i, 255, thickness=1)
                            cv2.imwrite(f"test/{el}-{i}.png",contimg)
                        contimg=np.zeros(img.shape)
                        cv2.drawContours(contimg, contours, -1, 255, thickness=1)
                        cv2.imwrite(f"test/{el}.png",contimg)
                        print(f"{el} hierarchy:{hierarchy}")
                        print(f"{el} contours[{currentHrrchy}]:{contours[currentHrrchy]}")
                        print(f"{el} contours[{hrrchy[2]}]:{contours[hrrchy[2]]}")
                        for i,pft in enumerate(familyTree):
                            print(f"{el} familyTree:{i} {pft}")
                        assert False, "昆孫以降は想定外。内容要確認"
                else:
                    # 上の兄弟の番号から自分の世代を求める
                    myBfNumber=int(familyTree[hrrchy[1]][1])
                    if myBfNumber%(10**((genCnt-2)*2))==0:  # 自分の兄が子世代なら
                        selfGeneration=2
                        childCnt+=1
                    elif myBfNumber%(10**((genCnt-3)*2))==0:  # 自分の兄が孫世代なら
                        selfGeneration=3
                        gChildCnt+=1
                    elif myBfNumber%(10**((genCnt-4)*2))==0:  # 自分の兄が孫世代なら
                        selfGeneration=4
                        g2gChildCnt+=1
                    elif myBfNumber%(10**((genCnt-5)*2))==0:  # 自分の兄が玄孫世代なら
                        selfGeneration=5
                        g3gChildCnt+=1
                    elif myBfNumber%(10**((genCnt-6)*2))==0:  # 自分の兄が来孫世代なら
                        selfGeneration=6
                        g4gChildCnt+=1
                # 自分より下の世代のカウンタクリア
                if selfGeneration<=2:
                    gChildCnt=0
                if selfGeneration<=3:
                    g2gChildCnt=0   # ひ孫用カウンタ
                if selfGeneration<=4:
                    g3gChildCnt=0   # 玄孫用カウンタ
                if selfGeneration<=5:
                    g4gChildCnt=0   # 来孫用カウンタ
            # 簡単な説明を追加
            if selfGeneration%2 != 0:   # 奇数世代(親、孫、玄孫)
                if hrrchy[2] == -1: # 子供がいなければおそらくピーク
                    hclass="maybe peak"
                else:
                    hclass="contour outside"    # 子供がいれば等高線の外枠
            else:   # 偶数世代(子、曾孫、来孫)
                if hrrchy[2] == -1: # 子供がいなければ通常の等高線内枠
                    hclass="contour inside"
                else:
                    hclass="contour inside (maybe grandchild is a peak)"    # 子供がいればピークを含む等高線の内枠(多分)
            # 番号を計算
            fNumber=str(int(parentCnt*(10**((genCnt-1)*2))+\
                    childCnt*(10**((genCnt-2)*2))+\
                    gChildCnt*(10**((genCnt-3)*2))+\
                    g2gChildCnt*(10**((genCnt-4)*2))+\
                    g3gChildCnt*(10**((genCnt-5)*2))+\
                    g4gChildCnt*(10**((genCnt-6)*2))))
            familyTree.append([hi,fNumber.zfill((genCnt*2)+1),hclass])
        if debug:
            for ft in familyTree:
                print(el,ft)
        # 家系図にピーク候補の情報追加
        for ft in familyTree:
            if int(ft[1])%(10**((genCnt-1)*2)) == 0: # 親の時
                if ft[0]==0:
                    pass
                else:
                    familyTree[parentIdx].append(peakCnt)
                    # 親のピーク候補の番号には、見つけたピーク候補の最小値を入れる
                    familyTree[parentIdx].append(min(foundPeaksCandidate) if len(foundPeaksCandidate)!=0 else -1)
                    familyTree[parentIdx].append(peakCandidates[familyTree[parentIdx][4]][0] if len(foundPeaksCandidate)!=0 else -1)
                parentIdx=ft[0]
                peakCnt=0
                foundPeaksCandidate=[]
            else:   # 親以外
                i = ft[0]
                for contpoint in contours[i]:  # 境界線の座標情報を舐める
                    compPc=(contpoint[0][0],contpoint[0][1])
                    for iii,pc in enumerate(peakCandidates):
                        if pc[0]<el: # 現在の標高より低いピークは対象外
                            continue
                        if compPc==pc[1]:    # 輪郭線の座標とピーク候補の座標が一致
                            if debug:
                                print(f"found peak candidate! {i}　({iii} {pc})")
                            if int(familyTree[i][1])%(10**((genCnt-2)*2)) == 0: # 子だったら輪郭線内側
                                familyTree[i][2]="contour inside incld/peak"
                            else:   # 孫だったらピーク
                                familyTree[i][2]="peak"
                                # 自分の親(=子)の情報を書き換える
                                familyTree[hierarchy[0][i][3]][2]="contour inside (my child is a peak)"
                                familyTree[hierarchy[0][i][3]][3]=1    # ピーク候補の数
                                familyTree[hierarchy[0][i][3]][4]=iii  # ピーク候補の何番目か
                                familyTree[hierarchy[0][i][3]][5]=pc[0]    # ピーク候補の標高
                            familyTree[i].append(1)     # ピーク候補の数(1)を後ろに追加
                            familyTree[i].append(iii)   # ピーク候補の何番目かを後ろに追加
                            familyTree[i].append(pc[0]) # ピーク候補の標高を後ろに追加
                            break
                    else:
                        continue
                    break
                else:   # 見つからなかったら
                    familyTree[i].append(0)     # ピーク候補の数(0)を後ろに追加
                    familyTree[i].append(-1)    # ピーク候補の何番目かには-1を後ろに追加
                    familyTree[i].append(-1)    # ピーク候補の標高には-1を後ろに追加
                # 見つけたピーク候補の番号が今回初めてだったら
                if familyTree[i][3]==1 and familyTree[i][4] not in foundPeaksCandidate:
                    foundPeaksCandidate.append(familyTree[i][4]) # 見つけたピーク候補の番号を控えておく
                    peakCnt+=1  # 見つけたピーク数をカウントアップ
        else:
            familyTree[parentIdx].append(peakCnt)
            # 親のピーク候補の番号には、見つけたピーク候補の最小値を入れる
            familyTree[parentIdx].append(min(foundPeaksCandidate) if len(foundPeaksCandidate)!=0 else -1)
            familyTree[parentIdx].append(peakCandidates[familyTree[parentIdx][4]][0] if len(foundPeaksCandidate)!=0 else -1)
# (2804.51, (183, 420))
#        for ft in familyTree:
#            if ft[5]==2804.51:
#                 debug=True
#                 break
#        else:
#            debug=False
#
        if debug:
            for ft in familyTree:
                print(el,ft)
        # 家系図チェック。1つの親にピークは1つ。2つ以上あればコルに到達
        for ft in familyTree:
            if int(ft[1])%(10**((genCnt-1)*2)) == 0: # 親の時
                peakCandidate2peakSw = True if ft[3] > 1 else False
                if peakCandidate2peakSw:
                    findColFb = 0   # コルを探す時に前の子と比較するか後ろの子と比較するかのフラグを初期化
                    overChild=[]
                    parentNo=int(ft[1])//(10**((genCnt-1)*2))
                    for oc in familyTree:   # 自分と子だけの家系図作成
                        if int(oc[1])//(10**((genCnt-1)*2)) == parentNo and int(oc[1])%(10**((genCnt-2)*2)) == 0:
                            overChild.append(oc)
                    if debug:
                        for oc in overChild:
                            print(f"overChild:{el} {oc}")
                    for oci,oc in enumerate(overChild):    # 自分と子だけの家系図を舐める
                        if oci==0:
                            compPcId=oc[4]
                            compPcElvs=oc[5]
                        else:
                            if findColFb==0 and oc[3]>0:
                                if oc[4]==compPcId: # 先に親と同じピーク候補が来たかどうか
                                    findColFb=-1    # 前にいれば前の子と比較する
                                else:
                                    findColFb=1     # 後ろにいれば後ろの子と比較する
                            if oc[3]!=0 and oc[4]!=compPcId:    # 親の持つピーク候補の番号と違う時
                                # コルの座標を求める
                                colList=[]
                                if debug:
                                    print(f"childId:{oc[0]} try to find col for peakCandidatesId:{oc[4]}")
                                # 座標の接点を探す
                                for ct in contours[oc[0]]:
                                    for compCt in contours[overChild[oci+findColFb][0]]:
                                        if ct[0][0] == compCt[0][0] and ct[0][1] == compCt[0][1]:
                                            if debug:
                                                print(f"found col! ({ct[0][0]} {ct[0][1]})")
                                            colList.append((ct[0][0],ct[0][1]))
                                            break
                                    else:
                                        continue
                                    break
                                else:
                                    if debug:
                                        print("col not found... try parent check")
                                    # もしかしてこっちが主流か？
                                    # 親の輪郭線にしか存在しない座標がある。
                                    # 親の座標の中に今の標高と一致する座標がある筈なので抜き出してみる。
                                    for ct in contours[overChild[0][0]]:
                                        if elevs[ct[0][1]][ct[0][0]] == el:
                                            if debug:
                                                print(f"found col! ({ct[0][0]} {ct[0][1]})")
                                            colList.append((ct[0][0],ct[0][1]))

                                if len(colList)>1:  # コル座標が複数ある時
                                    newColList=[]
                                    # 同じ座標が複数出てきた時はそこが接点なので採用する
                                    for cl in collections.Counter(colList).most_common():
                                        if cl[1]>1:
                                            newColList.append(cl[0])
                                    if len(newColList)>0:
                                        colList=newColList
                                    colSet=set(colList) # 重複排除
                                    colList=list(colSet)
                                if len(colList)>1:  # コル座標が複数ある時
                                    # 通常はピークとピークの間にあると思うので、2つのピーク座標にあるコルを採用。ちょっと雑
                                    # この辺りは実際にやってみながら修正していく
                                    scopeList=[]
                                    compPcCrd=peakCandidates[compPcId][1]
                                    scopeList.append(compPcCrd)
                                    pcCrd=peakCandidates[oc[4]][1]
                                    scopeList.append(pcCrd)
                                    scopeList.sort()
                                    newColList=[]
                                    for cl in colList:
                                        if scopeList[0]<=cl and cl<=scopeList[1]:
                                            newColList.append(cl)
                                    newColList.sort()
                                    if len(newColList)==0:  # ピークとピークの間にないケースは近い方を採用
                                        for cli,cl in enumerate(colList):
                                            dist=math.sqrt((pcCrd[0]-cl[0])**2+(pcCrd[1]-cl[1])**2)
                                            if cli==0:
                                                holdcli=cli
                                                holddist=dist
                                            elif holddist > dist:
                                                holdcli=cli
                                                holddist=dist
                                        newColList.append(colList[holdcli])
                                        colList=newColList
                                    elif len(newColList)==1:
                                        colList=newColList
                                    else:   # これでも複数あるケースがあるので、今のピークに近い方を採用する
                                        for ncli,ncl in enumerate(newColList):
                                            dist=math.sqrt((pcCrd[0]-ncl[0])**2+(pcCrd[1]-ncl[1])**2)
                                            if ncli==0:
                                                holdcli=ncli
                                                holddist=dist
                                            elif holddist > dist:
                                                holdcli=ncli
                                                holddist=dist
                                        colList=[]
                                        colList.append(newColList[holdcli])
                                # ここまでやって1つにならないケースはコルが見つからない時。処理を中止させて内容要確認
                                if len(colList)!=1:
                                    for i in range(len(contours)):
                                        contimg=np.zeros(img.shape)
                                        cv2.drawContours(contimg, contours, i, 255, thickness=1)
                                        cv2.imwrite(f"test/{el}-{i}.png",contimg)
                                    contimg=np.zeros(img.shape)
                                    cv2.drawContours(contimg, contours, -1, 255, thickness=1)
                                    cv2.imwrite(f"test/{el}.png",contimg)
                                    #print(f"contours:{contours}")
                                    print(f"{el} hierarchy:{hierarchy}")
                                    for i,pft in enumerate(familyTree):
                                        print(f"{el} familyTree:{i} {pft}")
                                    print(f"{el} peakId:{oc[4]} colList:{colList}")
                                    for pci,pc in enumerate(peakCandidates):
                                        print(f"{el} peakCandidates:{pci} {pc}")
                                    assert False, "コル座標がみつからない。もしくは複数存在。内容要確認"
                                if debug:
                                    print(f"{el} peakId:{oc[4]} colList:{colList}")
                                # ピーク候補の更新
                                for pci,pc in enumerate(peakCandidates):
                                    if oc[4]==pci and oc[5]==pc[0]: # 念の為、インデックスと標高の2つでチェック
                                        popPc=peakCandidates.pop(pci)   # ピーク候補から削除
                                        # peakColProminenceに追加
                                        prominence=float(Decimal(str(popPc[0]))-Decimal(str(el)))
                                        if verbose:
                                            if prominence >= minimumProminence:
                                                print(f"found peak! that matches SOTA-JA criteria. peak:{popPc} col:{(el,colList[0][0])} prominence:{prominence}")
                                            else:
                                                print(f"found peak! but not matches SOTA-JA criteria. peak:{popPc} col:{(el,colList[0][0])} prominence:{prominence}")
                                        peakColProminence.append((popPc,(el,colList[0]),prominence))
                                        # ピーク候補の更新が終わったらスイッチを元に戻す
                                        peakCandidate2peakSw=False
                                if debug:
                                    for pci,pc in enumerate(peakCandidates):
                                        print(f"{el} new peakCandidates:{pci} {pc}")
    # 最後、1番標高の高いピークをpeakColProminenceに登録する
    colList=[]
    colList.append(list(zip(*np.where(elevs==elevs.min()))))
    # 複数あった時は一番近い座標を採用
    if len(colList)>1:
        pcCrd=peakCandidates[0][1]
        for cli,cl in enumerate(colList):
            dist=math.sqrt((pcCrd[0]-cl[0])**2+(pcCrd[1]-cl[1])**2)
            if cli==0:
                holdcli=cli
                holddist=dist
            else:
                if holddist > dist:
                    holdcli=cli
                    holddist=dist
        else:
            newColList.append(colList[holdcli])
        colList=newColList
    if len(colList)!=1:
        print(colList)
        assert False, "コル座標がみつからない。もしくは複数存在。内容要確認"
    popPc=peakCandidates.pop(0)   # ピーク候補から削除
    # ピークとコルの標高差がminimumProminence以上あればpeakColProminenceに追加
    prominence=float(Decimal(str(popPc[0]))-Decimal(str(elevs.min())))
    if verbose:
        if prominence >= minimumProminence:
            print(f"found peak! that matches SOTA-JA criteria. peak:{popPc} col:{(elevs.min(),colList[0][0])} prominence:{prominence}")
        else:
            print(f"found peak! but not matches SOTA-JA criteria. peak:{popPc} col:{(elevs.min(),colList[0][0])} prominence:{prominence}")
    peakColProminence.append((popPc,(elevs.min(),colList[0][0]),prominence))
    peakColProminence.sort(key=itemgetter(0,1,2), reverse=True)
    for pcli,pcl in enumerate(peakColProminence):
        print(f"peakColProminence:{pcli} {pcl}")

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
