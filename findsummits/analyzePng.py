import sys
import datetime
import os
import configparser
import argparse
import numpy as np
#import io
import collections
import math
from decimal import Decimal
import cv2
from operator import itemgetter
from tqdm import tqdm
# 設定ファイル読み込み
config=configparser.ConfigParser()
config.read(f"{os.path.dirname(__file__)}/config.ini")
# 時間測定
import csv
#
def png2elevs(filePath):
    img = cv2.imread(filePath)
    # RGBから標高地を計算: x = 2**16R + 2**8G + B
    # openCVではGBRの順番になるので注意
    elevs=img[:, :, 2]*2**16+img[:, :, 1]*2**8+img[:, :, 0]
    elevs0=np.where(elevs<2**23, elevs/100, elevs)          # x < 223の場合　h = xu
    elevs=np.where(elevs0==2**23, 0, elevs0)                # x = 223の場合　h = NA 取り敢えず0とする
    elevs0=np.where(elevs>2**23, (elevs-2**24)/100, elevs)  # x > 223の場合　h = (x-224)u
    elevs=np.where(elevs0<0, 0, elevs0) # マイナス標高は全て0とする
    return elevs
#
def main(filePath, debug=False, processtimelog=False):
    print(f"{__name__}: Started @{datetime.datetime.now()}")
#
# 時間測定
    if processtimelog:
        os.makedirs(config["LOG"]["DATA"] ,exist_ok=True)
        with open(config["LOG"]["DATA"]+"/processtime.csv","w") as f:
            csv.writer(f).writerow(["el","func","seconds"])
        start=datetime.datetime.now()
#
    elevs=png2elevs(filePath)
#    imageHeightWidth=[es for es in elevs.shape]
    print(f"image height:{elevs.shape[0]} width:{elevs.shape[1]}")
# 標高の一覧(高い順)を取得
    elvslist=list(np.unique(elevs))[::-1]
    print(f"elevation: highest:{elevs.max()}m - lowest:{elevs.min()}m, difference:{float(Decimal(str(elevs.max()))-Decimal(str(elevs.min())))}m")
    print(f"{len(elvslist)} steps will be analyzed")
# 時間測定
    if processtimelog:
        td=datetime.datetime.now()-start
        with open(config["LOG"]["DATA"]+"/processtime.csv","a") as f:
            csv.writer(f).writerow(["--","image read etc.",td.total_seconds()])
        start=datetime.datetime.now()
#
    peakCandidates=[]
    peakColProminence=[]
    print("analyzing start")
    for el in tqdm(elvslist):
        # 海面に達した時は処理しない
        if el==0:
            continue
        # 標高がMINIMUM_PROMINENCE-5mより低くて、ピーク候補が1人だけになったら以下処理しない
        if el<config["VAL"].getint("MINIMUM_PROMINENCE")-5 and len(peakCandidates)==1:
            continue
        # img=np.uint8(np.where(elevs>=el,255,0))
        # いくつか試してみたが今の所これが1番速い。2行になったけど上記の半分以下
        img=np.zeros(elevs.shape,dtype=np.uint8)
        img[elevs>=el]=255
        # 輪郭を抽出する。最初はベタ塗りの画像から親の輪郭だけ抽出したいので
        # 最も外側の輪郭のみ(cv2.RETR_EXTERNAL)のメモリ節約モード(cv2.CHAIN_APPROX_SIMPLE)
        # 子供がいたらそれは凹地なので気にしない
        contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
# 時間測定
        if processtimelog:
            td=datetime.datetime.now()-start
            with open(config["LOG"]["DATA"]+"/processtime.csv","a") as f:
                csv.writer(f).writerow([el,"findContours(1)",td.total_seconds()])
            start=datetime.datetime.now()
#
        # 輪郭を描画する
        img=np.zeros(img.shape,dtype=np.uint8)
        cv2.drawContours(img, contours, -1, 255, thickness=1)
        # ピークをプロットして輪郭とピークだけの画像にする
        for hh,xy in peakCandidates:
            img[xy[1],xy[0]]=255
        # 再度輪郭を抽出する。2回目は階層構造と詳細な座標を取得したいので
        # 階層あり(cv2.RETR_TREE)の描画プロット全て抽出(cv2.CHAIN_APPROX_NONE)
        contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        # hierarchyは最初の次元がサイズ1で扱い辛いので、最初の次元を削除したビューを生成する
        hierarchy2d=hierarchy.squeeze(0)
# 時間測定
        if processtimelog:
            td=datetime.datetime.now()-start
            with open(config["LOG"]["DATA"]+"/processtime.csv","a") as f:
                csv.writer(f).writerow([el,"findContours(2)",td.total_seconds()])
            start=datetime.datetime.now()
#
        if debug:
            #print(hierarchy)
            print(hierarchy2d)
# debug
#        if el==2078.4:
#            contimg=np.zeros(img.shape)
#            cv2.drawContours(contimg, contours, -1, 255, thickness=1)
#            cv2.imwrite(f'{config["DIR"]["IMAGE"]}/{el}.png',contimg)
#            for i in range(len(contours)):
#                contimg=np.zeros(img.shape)
#                cv2.drawContours(contimg, contours, i, 255, thickness=1)
#                cv2.imwrite(f'{config["DIR"]["IMAGE"]}/{el}-{i}.png',contimg)
# debug
        for hi,hrrchy in enumerate(hierarchy2d):
            # ピーク候補に入れるかどうかの処理なので現在の標高がMINIMUM_PROMINENCEより低ければ次の人へ
            if el<config["VAL"].getint("MINIMUM_PROMINENCE")-5: # -5mまで対象とする
                continue
            if hrrchy[2]!= -1:  # 子供がいたら次の人へ
                continue
            # 親もいなければピーク候補にいるか確認
            if hrrchy[3]==-1:
                contpointSet={tuple(contpoint[0].tolist()) for contpoint in contours[hi]}
                for pc in peakCandidates:
                    if pc[1] in contpointSet:  # ピーク候補の座標が輪郭線の座標の中にあればこのループを抜けて次の人
                        break
                else:   # なければピーク候補に入れる
                    contpointList=[]
                    for cl in contpointSet:
                        if debug:
                            print(f"{el} borderline check:{cl}")
                        # 外枠近辺で見つかったピーク候補は今回落選させる(殆どがイメージ外から続く稜線上の最高地点)
                        if cl[0]<=config["VAL"].getint("CANDIDATE_BORDERLINE"):
                            continue
                        if cl[0]>=elevs.shape[1]-config["VAL"].getint("CANDIDATE_BORDERLINE"):
                            continue
                        if cl[1]<=config["VAL"].getint("CANDIDATE_BORDERLINE"):
                            continue
                        if cl[1]>=elevs.shape[0]-config["VAL"].getint("CANDIDATE_BORDERLINE"):
                            continue
                        contpointList.append(cl)
                        if debug:
                            print(f"{el} borderline check pass:{cl}")
                    if debug:
                        print(f"{el} contpointList:{contpointList}")
                    if len(contpointList)>0:    # 残った座標があれば
                        contpointList.sort(key=itemgetter(0))    # 座標で並べ替え。(x,y)なので西側有利の北側有利
                        peakCandidates.append((el,contpointList[0])) # 1番先頭をピーク候補に追加
# 時間測定
        if processtimelog:
            td=datetime.datetime.now()-start
            with open(config["LOG"]["DATA"]+"/processtime.csv","a") as f:
                csv.writer(f).writerow([el,"new peakCandidate check",td.total_seconds()])
            start=datetime.datetime.now()
#
        if debug:
            for pci,pc in enumerate(peakCandidates):
                print(f"{el} peakCandidates:{pci} {pc}")
        # ピーク候補が1人以下だったら次が出てくるまで飛ばす
        if len(peakCandidates)<=1:
            continue
        # 家系図を作成
        familyTree=[None]*len(hierarchy2d)    # 必要な数だけ最初に配列作っておく
        rejPeakCandidates=[]
        parentCnt=0
        for hi,hrrchy in enumerate(hierarchy2d):
            if hrrchy[3]== -1:  # 親だったら(親がいないのが親)
                selfGeneration=1
                parentCnt+=1
                childCnt=0
                gChildCnt=0
            else:   # 親以外
                if hrrchy[1]==-1:   # 自分が長兄だったら
                    # 親の番号から自分の世代を求める
                    myPfNumber=int(familyTree[hrrchy[3]][1])
                    if myPfNumber%100000==0:  # 自分の親が親世代なら
                        selfGeneration=2
                        childCnt+=1
                    elif myPfNumber%100==0:  # 自分の親が子世代なら
                        selfGeneration=3
                        gChildCnt+=1
                    else:
                        for i in range(len(contours)):
                            contimg=np.zeros(img.shape)
                            cv2.drawContours(contimg, contours, i, 255, thickness=1)
                            cv2.imwrite(f'{config["DIR"]["IMAGE"]}/{el}-{i}.png',contimg)
                        contimg=np.zeros(img.shape)
                        cv2.drawContours(contimg, contours, -1, 255, thickness=1)
                        cv2.imwrite(f'{config["DIR"]["IMAGE"]}/{el}.png',contimg)
                        print(f"{el} hierarchy:{hierarchy2d}")
                        print(f"{el} contours[{hi}]:{contours[hi]}")
                        print(f"{el} contours[{hrrchy[2]}]:{contours[hrrchy[2]]}")
                        for i,pft in enumerate(familyTree):
                            print(f"{el} familyTree:{i} {pft}")
                        print(f"{__name__}: Abnormal Termination @{datetime.datetime.now()}")
                        assert False, "曾孫以降は想定外。内容要確認"
                else:
                    # 上の兄弟の番号から自分の世代を求める
                    myBfNumber=int(familyTree[hrrchy[1]][1])
                    if myBfNumber%100==0:  # 自分の兄が子世代なら
                        selfGeneration=2
                        childCnt+=1
                    else:  # 自分の兄が孫世代なら
                        selfGeneration=3
                        gChildCnt+=1
                # 自分より下の世代のカウンタクリア
                if selfGeneration<=2:
                    gChildCnt=0
            # 簡単な説明を追加
            if selfGeneration%2 != 0:   # 奇数世代(親、孫)
                if hrrchy[2] == -1: # 子供がいなければおそらくピーク
                    hclass="maybe a peak"
                else:
                    hclass="contour outside"    # 子供がいれば等高線の外枠
            else:   # 偶数世代(子)
                if hrrchy[2] == -1: # 子供がいなければ通常の等高線内枠
                    hclass="contour inside"
                else:
                    hclass="contour inside (my child maybe a peak)"    # 子供がいればピークを含む等高線の内枠(多分)
            # 番号を計算
            fNumber=str(int(parentCnt*100000+childCnt*100+gChildCnt))
            # ピーク候補の情報を付加する
            # 輪郭線を構成する座標の一覧を作成
            cpSet={tuple(contpoint[0].tolist()) for contpoint in contours[hi]}
            for pci,pc in enumerate(peakCandidates):
                if pc[1] in cpSet:  # ピーク候補の座標が輪郭線の座標の中にあれば
                    if debug:
                        print(f"found peak candidate! {fNumber}　({pci} {pc})")
                    if selfGeneration==1:   # 親
                        if hrrchy[2] == -1: # 子供がいなければおそらくピーク
                            hclass="peak"
                        else:
                            hclass="contour outside incld/peak" # 子供がいれば等高線の外枠
                            ## 子がいる親の輪郭線にピーク候補の座標が現れたらその時点で落選確定
                            #rejPeakCandidates.append(pc[1])
                    if selfGeneration==2:   # 子
                        hclass="contour inside incld/peak"
                    if selfGeneration==3:   # 孫
                        hclass="peak"
                    pcCnt=1         # ピーク候補の数(1)
                    pcNo=pci        # ピーク候補の何番目か
                    pcAlt=pc[0]     # ピーク候補の標高
                    pcCord=pc[1]    # ピーク候補の座標
                    break
            else:   # 見つからなかったら
                pcCnt=0         # ピーク候補の数(1)
                pcNo=-1         # ピーク候補の何番目か
                pcAlt=None      # ピーク候補の標高
                pcCord=None     # ピーク候補の座標
            # 最初に用意しておいた配列に入れる
            familyTree[hi]=[hi,fNumber.zfill(8),hclass,pcCnt,pcNo,pcAlt,pcCord]
# 時間測定
        if processtimelog:
            td=datetime.datetime.now()-start
            with open(config["LOG"]["DATA"]+"/processtime.csv","a") as f:
                csv.writer(f).writerow([el,"make familyTree",td.total_seconds()])
            start=datetime.datetime.now()
#
        if debug:
            for ft in familyTree:
                print(f"{el} ft(1):{ft}")
        # 家系図の情報整理
        for ft in familyTree:
            if int(ft[1])%100000==0: # 親の時
                if ft[0]==0:
                    pass
                else:   # 1つ前の親の情報を更新
                    if hierarchy2d[parentIdx][2]==-1:
                        pass    # 子がいなかったら更新しない
                    else:
                        if len(foundPeaksCandidate)!=0:
                            familyTree[parentIdx][3]=peakCnt
                            # 親のピーク候補の番号には、見つけたピーク候補の最小値を入れる
                            familyTree[parentIdx][4]=min(foundPeaksCandidate)
                            familyTree[parentIdx][5]=peakCandidates[familyTree[parentIdx][4]][0]
                            familyTree[parentIdx][6]=peakCandidates[familyTree[parentIdx][4]][1]
                parentIdx=ft[0]
                peakCnt=0
                foundPeaksCandidate=[]
            else:   # 親以外
                # ピーク候補の番号が今回初めてだったら
                if ft[3]==1 and ft[4] not in set(foundPeaksCandidate):
                    foundPeaksCandidate.append(ft[4]) # 見つけたピーク候補の番号を控えておく
                    peakCnt+=1  # 見つけたピーク数をカウントアップ
                    if int(ft[1])%100==0:    # 子だったら
                        pass    # 何もしない
                    else:   # 孫だったら自分の親(=子)の情報を書き換える
                        childIdx=hierarchy2d[ft[0]][3]
                        # 子にピーク候補の情報がない、もしくは子のピーク候補Noの方が自分(孫)のピーク候補No以上の時
                        if familyTree[childIdx][4]==-1 or familyTree[childIdx][4]>ft[4]:
                            if familyTree[childIdx][4]!=-1:
                                rejPeakCandidates.append(familyTree[childIdx][6])
                            familyTree[childIdx][2]="contour inside (my child is a peak)"    # 簡単な説明
                            familyTree[childIdx][3]+=1      # ピーク候補の数(+1)
                            familyTree[childIdx][4]=ft[4]   # ピーク候補の何番目か
                            familyTree[childIdx][5]=ft[5]   # ピーク候補の標高
                            familyTree[childIdx][6]=ft[6]   # ピーク候補の座標
                        else:   # それ以外はあり得ないが、あった時はピーク候補から落選させる
                            rejPeakCandidates.append(ft[6])

                else:   # 見つからなかったら
                    ft[3]=0          # ピーク候補の数(0)
                    ft[4]=-1         # ピーク候補の何番目か(-1)
                    ft[5]=-1         # ピーク候補の標高(-1)
        else:   # 終わったら1番最後の親の情報を更新
            familyTree[parentIdx][3]=peakCnt
            # 親のピーク候補の番号には、見つけたピーク候補の最小値を入れる
            familyTree[parentIdx][4]=min(foundPeaksCandidate) if len(foundPeaksCandidate)!=0 else -1
            familyTree[parentIdx][5]=peakCandidates[familyTree[parentIdx][4]][0] if len(foundPeaksCandidate)!=0 else -1
            familyTree[parentIdx][6]=peakCandidates[familyTree[parentIdx][4]][1] if len(foundPeaksCandidate)!=0 else None
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
                print(f"{el} ft(2):{ft}")
# 時間測定
        if processtimelog:
            td=datetime.datetime.now()-start
            with open(config["LOG"]["DATA"]+"/processtime.csv","a") as f:
                csv.writer(f).writerow([el,"update familyTree",td.total_seconds()])
            start=datetime.datetime.now()
#
        # 家系図チェック。1つの親にピークは1つ。2つ以上あればコルに到達
        for ft in familyTree:
            if int(ft[1])%100000 != 0: # 親じゃなければ次の人
                continue
            peakCandidate2peakSw = True if ft[3] > 1 else False
            if not peakCandidate2peakSw:    # ピークを2つ持つ人が対象
                continue
            findColFb = 0   # コルを探す時に前の子と比較するか後ろの子と比較するかのフラグを初期化
            overChild=[]
            parentNo=int(ft[1])//100000
            for oc in familyTree:   # 自分と子だけの家系図作成
                if int(oc[1])//100000==parentNo and int(oc[1])%100==0:
                    overChild.append(oc)
            if debug:
                for oc in overChild:
                    print(f"{el} overChild:{oc}")
            colList=[]
            for oci,oc in enumerate(overChild):    # 自分と子だけの家系図を舐める
                if oci==0:  # 親の時
                    winnerPcNo=oc[4]
                    winnerPcCrd=oc[6]
                else:   # 子の時
                    if findColFb==0 and oc[3]>0:
                        if oc[4]==winnerPcNo: # 先に親と同じピーク候補が来たかどうか
                            findColFb=-1    # 前にいれば前の子と比較する
                        else:
                            findColFb=1     # 後ろにいれば後ろの子と比較する
                    if oc[3]!=0 and oc[4]!=winnerPcNo:    # 親の持つピーク候補の番号と違う時、コル座標を探す
                        loserPcNo=oc[4]
                        loserPcCrd=oc[6]
                        if debug:
                            print(f"childId:{oc[0]} try to find col for peakCandidatesId:{oc[4]}")
                        # 当初は輪郭線内側に接点があると思っていたが、実際にやってみると
                        # 親の輪郭線にしか接点が存在しないケースが殆ど。
                        # 親の座標の中に今の標高と一致する座標がある筈なのでそれを抜き出す。
                        elCrds=set(tuple(zip(*np.where(elevs==el))))
                        for ct in contours[oc[0]]:
                            if (ct[0][1],ct[0][0]) in elCrds:
                                if debug:
                                    print(f"found col! ({tuple(ct[0].tolist())})")
                                colList.append(tuple(ct[0].tolist()))
                        if len(colList)==0:
                            # 親の座標に見つからなかった時、隣接する子との接点を探す
                            for ct in contours[oc[0]]:  # 自分の輪郭線の座標と
                                for compCt in contours[overChild[oci+findColFb][0]]:    # 相手の輪郭線の座標を比較して
                                    if np.all(ct==compCt):  # 一致していればコル座標を発見
                                        if debug:
                                            print(f"found col! ({ct[0].tolist()})")
                                        colList.append(tuple(ct[0].tolist()))
                                        break
                                else:   # 見つからなかったら
                                    continue    # 次の座標へ
                                break
                            else:   # 子同士の接点が見つからなかった時
                                # どこだかわからないので現在の標高と同じ標高の座標を全部抜き出す
                                for oc2 in overChild:
                                    for ct in contours[oc2[0]]:
                                        if elevs[ct[0][1],ct[0][0]] == el:
                                            colList.append(tuple(ct[0].tolist()))
                            break   # ループを抜ける
#
            if len(colList)==0:  # コル座標が見つからなかった時
                # rejPeakCandidatesに誰かいれば、標高の高い孫に弾かれた孫なので、MINIMUM_PROMINENCE以上あれば最後に救済する
                for rpc in rejPeakCandidates:
                    # 先ずは家系図より自分の情報を得る
                    salvation=False
                    for ft in familyTree:
                        if rpc==ft[6] and ft[5]-el>=config["VAL"].getint("MINIMUM_PROMINENCE"):
                            loserPcNo=ft[4]
                            loserPcCrd=rpc
                            # 自分のfamilyNoから自分の親(子)のfamilyNoを得る
                            childFNo=str((int(ft[1])//100)*100).zfill(8)
                            salvation=True
                            break
                    if salvation:
                        # 次に家系図より自分の親(子)の輪郭線Noを得て、子の輪郭線座標を取得する
                        for ft in familyTree:
                            if childFNo==ft[1]:
                                for ct in contours[ft[0]]:
                                    if elevs[ct[0][1],ct[0][0]] == el:
                                        colList.append(tuple(ct[0].tolist()))
                                break
                        else:
                            continue
                        break
#
            if len(colList)==0:  # コル座標が見つからなかった時
                # 子が出来る前に飲み込まれた些細なピークが悪さしたと思われる。
                # 特に何もしない(悪さしたピークはrejPeakCandidatesに入っている筈なので後で除外される)
                continue
#
            if len(colList)>1:  # コル座標が複数ある時
                # 通常はピークとピークの間にあると思うので、2つのピークそれぞれに最も近いコルを採用。
                newColList=[]
                for cli,cl in enumerate(colList):
                    dist=math.sqrt((winnerPcCrd[0]-cl[0])**2+(winnerPcCrd[1]-cl[1])**2)+math.sqrt((loserPcCrd[0]-cl[0])**2+(loserPcCrd[1]-cl[1])**2)
                    if cli==0:
                        holdcli=cli
                        holddist=dist
                    elif holddist > dist:
                        holdcli=cli
                        holddist=dist
                newColList.append(colList[holdcli])
                colList=newColList
            if len(colList)!=1:
                # ここに来る事はない筈だが。あった場合は処理を中止させて内容要確認
                #for i in range(len(contours)):
                #    contimg=np.zeros(img.shape)
                #    cv2.drawContours(contimg, contours, i, 255, thickness=1)
                #    cv2.imwrite(f"test/{el}-{i}.png",contimg)
                #contimg=np.zeros(img.shape)
                #cv2.drawContours(contimg, contours, -1, 255, thickness=1)
                #cv2.imwrite(f"test/{el}.png",contimg)
                #print(f"contours:{contours}")
                for i,hl in enumerate(hierarchy2d):
                    print(f"{el} hierarchy:{i} {hl}")
                for i,pft in enumerate(familyTree):
                    print(f"{el} familyTree:{i} {pft}")
                for i,ocl in enumerate(overChild):
                    print(f"{el} overChild:{i} {ocl}")
                for pci,pc in enumerate(peakCandidates):
                    print(f"{el} peakCandidates:{pci} {pc}")
                print(f"{el} peakNo:{loserPcNo} colList:{colList}")
                #for ocl in overChild:
                #    print(f"{el} contours:{ocl[0]} {[tuple(contpoint[0].tolist()) for contpoint in contours[ocl[0]]]}")
                for rpci,rpc in enumerate(rejPeakCandidates):
                    print(f"{el} rejPeakCandidates:{rpci} {rpc}")
                print(f"{__name__}: Abnormal Termination @{datetime.datetime.now()}")
                assert False, "コル座標がみつからない。もしくは複数存在。内容要確認"
            if debug:
                print(f"{el} peakNo:{loserPcNo} colList:{colList}")
            # ピーク候補の更新
            for pci,pc in enumerate(peakCandidates):
                #if oc[4]==pci and oc[5]==pc[0]: # 念の為、インデックスと標高の2つでチェック
                # 同じ標高で先に誰かが先に消しているとインデックスが合わなくなるので突合キーを座標に変更。
                if loserPcCrd==pc[1]:
                    popPc=peakCandidates.pop(pci)   # ピーク候補から削除
                    # peakColProminenceに追加
                    prominence=float(Decimal(str(popPc[0]))-Decimal(str(el)))
                    peakColProminence.append((popPc,(el,colList[0]),prominence))
                    break
            else:   # ここに来る事はない筈だが、万が一ここに来た場合は先に誰かが消しているので特に何もしない
                #for i,hl in enumerate(hierarchyList):
                #    print(f"{el} hierarchy:{i} {hl}")
                #for i,pft in enumerate(familyTree):
                #    print(f"{el} familyTree:{i} {pft}")
                #for i,ocl in enumerate(overChild):
                #    print(f"{el} overChild:{i} {ocl}")
                #for pci,pc in enumerate(peakCandidates):
                #    print(f"{el} peakCandidates:{pci} {pc}")
                #print(f"{el} peakNo:{loserPcNo} colList:{colList}")
                ##for oc in overChild:
                ##    print(f"{el} contours:{oc[0]} {[tuple(contpoint[0].tolist()) for contpoint in contours[oc[0]]]}")
                #for rpci,rpc in enumerate(rejPeakCandidates):
                #    print(f"{el} rejPeakCandidates:{rpci} {rpc}")
                #print(f"{__name__}: Abnormal Termination @{datetime.datetime.now()}")
                #assert False, "コルの見つかったピーク候補がpeakCandidates内に見当たらない。内容要確認"
                pass
            if debug:
                for pci,pc in enumerate(peakCandidates):
                    print(f"{el} new peakCandidates:{pci} {pc}")
# 時間測定
        if processtimelog:
            td=datetime.datetime.now()-start
            with open(config["LOG"]["DATA"]+"/processtime.csv","a") as f:
                csv.writer(f).writerow([el,"check familyTree",td.total_seconds()])
            start=datetime.datetime.now()
#
        if debug:
            for rpci,rpc in enumerate(rejPeakCandidates):
                print(f"{el} rejPeakCandidates:{rpci} {rpc}")
        # 最後に不合格になったピーク候補が残っていれば除外する
        rpcCordSet={rpc for rpc in rejPeakCandidates}
        peakCandidates=[pc for pc in peakCandidates if pc[1] not in rpcCordSet]
# 時間測定
        if processtimelog:
            td=datetime.datetime.now()-start
            with open(config["LOG"]["DATA"]+"/processtime.csv","a") as f:
                csv.writer(f).writerow([el,"update peakCandidates",td.total_seconds()])
            start=datetime.datetime.now()
#
    # 最後、残ったピーク候補をpeakColProminenceに登録する
    colList=list(zip(*np.where(elevs==elevs.min())))
    for pci,pc in enumerate(peakCandidates):
        if debug:
            print(f"{elevs.min()} peakCandidates:{pci} {pc}")
        # 複数あった時は一番近い座標を採用
        if len(colList)==1:
            newColList=colList
        elif len(colList)>1:
            newColList=[]
            for cli,cl in enumerate(colList):
                dist=math.sqrt((pc[1][1]-cl[0])**2+(pc[1][0]-cl[1])**2)
                if cli==0:
                    holdcli=cli
                    holddist=dist
                elif holddist > dist:
                    holdcli=cli
                    holddist=dist
            else:
                newColList.append((colList[holdcli][1],colList[holdcli][0]))
        elif len(colList)==0:
            print(colList)
            print(f"{__name__}: Abnormal Termination @{datetime.datetime.now()}")
            assert False, "コル座標がみつからない。内容要確認"
        # ピークとコルの標高差がminimumProminence以上あればpeakColProminenceに追加
        prominence=float(Decimal(str(pc[0]))-Decimal(str(elevs.min())))
        peakColProminence.append((pc,(elevs.min(),newColList[0]),prominence))
    peakColProminence.sort(key=itemgetter(0,1,2), reverse=True)
    for pcli,pcl in enumerate(peakColProminence):
        print(f"peakColProminence:{pcli} {pcl}")
    # 出来上がったpeakColProminenceをテキストに吐き出す
    print("analyzing completed")
    os.makedirs(config["DIR"]["PCP"] ,exist_ok=True)
    result=f'{config["DIR"]["PCP"]}/{os.path.splitext(os.path.basename(filePath))[0]}.pcp'
    with open(result, mode="w") as f:
        for pcl in peakColProminence:
            dat=f"{pcl[0]},{pcl[1]},{pcl[2]}\n"
            f.write(dat)
#
    print(f"{__name__}: Finished @{datetime.datetime.now()}")
    return result
#
if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument("filePath",help="pngファイルのファイルパス")
    parser.add_argument("-d", "--debug", help="show debug info",
        action="store_true")
    parser.add_argument("-p", "--processtimelog", help="save time log info",
        action="store_true")
    args=parser.parse_args()
    ret=main(filePath=args.filePath, debug=args.debug, processtimelog=args.processtimelog)
