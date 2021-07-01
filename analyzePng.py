import sys
import datetime
import inspect
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
import defval
#
def png2elevs(filePath):
    img = cv2.imread(filePath)
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
    local_max = maximum_filter(image, footprint=np.ones((defval.const.FILTER_SIZE, defval.const.FILTER_SIZE)), mode='constant')
    detected_peaks = np.ma.array(image, mask=~(image == local_max))

    # 小さいピーク値を排除（minimumProminenceより小さなピークは排除）
    temp = np.ma.array(detected_peaks, mask=~(detected_peaks >= defval.const.MINIMUM_PPROMINENCE))
    peaks_index = np.where(temp.mask != True)
    return list(zip(*np.where(temp.mask != True)))
#
def main(filePath="tile/tile.png", verbose=False, debug=False):
    f=inspect.currentframe()
    myName=inspect.getframeinfo(f)[0].split("/")[-1].replace("py","")+inspect.getframeinfo(f)[2]+"()"
    print(f"{myName}: Started @{datetime.datetime.now()}")
#
    elevs=png2elevs(filePath)
    imageHeightWidth=[es for es in elevs.shape]
    print(f"image height:{imageHeightWidth[0]} width:{imageHeightWidth[1]}")
# ピーク(候補)の一覧作成
    peakCandidates=[(elevs[yy][xx],(xx,yy)) for yy,xx in detectPeaksCoords(elevs)]
    peakCandidates.sort(key=itemgetter(0,1), reverse=True)
    uniqPeakCandidates=[]
    for i,pc in enumerate(peakCandidates):
        # 外枠近辺で見つったピーク候補は今回落選させる(殆どがイメージ外から続く稜線上の最高地点)
        if pc[1][0]<=defval.const.CANDIDATE_BORDERLINE or pc[1][0]>=imageHeightWidth[1]-defval.const.CANDIDATE_BORDERLINE:
            continue
        if pc[1][1]<=defval.const.CANDIDATE_BORDERLINE or pc[1][1]>=imageHeightWidth[0]-defval.const.CANDIDATE_BORDERLINE:
            continue
        # 重複排除(dem10から取った標高は2*2の4ピクセルが固まっているので)
        if i != 0:
            # 同じ標高で座標が1違いだったら1番大きい座標を採用
            if prepc[0]==pc[0] and abs(prepc[1][0]-pc[1][0])<=1 and abs(prepc[1][1]-pc[1][1])<=1:
                    continue
        uniqPeakCandidates.append(pc)
        prepc=pc
    peakCandidates=uniqPeakCandidates
    del uniqPeakCandidates
    for i,pc in enumerate(peakCandidates):
        print(f"peakCandidates:{i} {pc}")
    assert len(peakCandidates)>0, "ピーク候補が見当たらない。内容要確認(pngが小さ過ぎるかも)"
# 標高の一覧(高い順)を取得
    elvslist=list(np.unique(elevs))[::-1]
    print(f"elevation: highest:{elevs.max()}m - lowest:{elevs.min()}, {len(elvslist)} steps will be analyzed")
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
                # 輪郭線を構成する座標の一覧を作成
                contpointList=[tuple(contpoint[0].tolist()) for contpoint in contours[i]]
#                print(contpointList)
                for pci,pc in enumerate(peakCandidates):
                    if pc[0]<el: # 現在の標高より低いピークは対象外
                        continue
                    if pc[1] in contpointList:  # ピーク候補の座標が輪郭線の座標の中にあれば
                        if debug:
                            print(f"found peak candidate! {i}　({pci} {pc})")
                        if int(familyTree[i][1])%(10**((genCnt-2)*2)) == 0: # 子だったら輪郭線内側
                            familyTree[i][2]="contour inside incld/peak"
                        else:   # 孫だったらピーク
                            familyTree[i][2]="peak"
                            # 自分の親(=子)の情報を書き換える
                            familyTree[hierarchy[0][i][3]][2]="contour inside (my child is a peak)"
                            familyTree[hierarchy[0][i][3]][3]=1    # ピーク候補の数
                            familyTree[hierarchy[0][i][3]][4]=pci  # ピーク候補の何番目か
                            familyTree[hierarchy[0][i][3]][5]=pc[0]    # ピーク候補の標高
                        familyTree[i].append(1)     # ピーク候補の数(1)を後ろに追加
                        familyTree[i].append(pci)   # ピーク候補の何番目かを後ろに追加
                        familyTree[i].append(pc[0]) # ピーク候補の標高を後ろに追加
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
                                        if np.all(ct == compCt):
                                            if debug:
                                                print(f"found col! ({ct[0].tolist()})")
                                            colList.append(tuple(ct[0].tolist()))
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
                                                print(f"found col! ({tuple(ct[0].tolist())})")
                                            colList.append(tuple(ct[0].tolist()))
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
                                    # 通常はピークとピークの間にあると思うので、2つのピークそれぞれに最も近いコルを採用。
                                    compPcCrd=peakCandidates[compPcId][1]
                                    pcCrd=peakCandidates[oc[4]][1]
                                    newColList=[]
                                    for cli,cl in enumerate(colList):
                                        dist=math.sqrt((pcCrd[0]-cl[0])**2+(pcCrd[1]-cl[1])**2)+math.sqrt((compPcCrd[0]-cl[0])**2+(compPcCrd[1]-cl[1])**2)
                                        if cli==0:
                                            holdcli=cli
                                            holddist=dist
                                        elif holddist > dist:
                                            holdcli=cli
                                            holddist=dist
                                    newColList.append(colList[holdcli])
                                    colList=newColList
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
    colList=[list(zip(*np.where(elevs==elevs.min())))]
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
    # 出来上がったpeakColProminenceをテキストに吐き出す
    print("analysis completed")
    os.makedirs(defval.const.PCP_DIR ,exist_ok=True)
    result=f"{defval.const.PCP_DIR}/{os.path.splitext(os.path.basename(filePath))[0]}.txt"
    with open(result, mode="w") as f:
        for pcl in peakColProminence:
            dat=f"{pcl[0]},{pcl[1]},{pcl[2]}\n"
            f.write(dat)
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
    from matplotlib.colors import LightSource
    import matplotlib.cm as cm
    from mpl_toolkits.axes_grid1 import make_axes_locatable
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
    os.makedirs(defval.const.IMAGE_DIR ,exist_ok=True)
    plt.savefig(f"{defval.const.IMAGE_DIR}/{os.path.splitext(os.path.basename(filePath))[0]}.pdf", bbox_inches="tight")
#
    print(f"{myName}: Finished @{datetime.datetime.now()}")
#---
if __name__ == '__main__':
    print(f"{sys.argv[0]}: Started @{datetime.datetime.now()}")
    args = sys.argv
    if len(args)>1:
        main(filePath=args[1])
    else:
        print("pngファイルを指定してください")
    print(f"{sys.argv[0]}: Finished @{datetime.datetime.now()}")
