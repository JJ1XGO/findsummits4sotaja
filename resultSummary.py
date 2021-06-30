import sys
import datetime
import os
import csv
from operator import itemgetter
from decimal import Decimal,ROUND_HALF_UP
import meshcd2png as m2p
## defval
import defval
#
def main(filePath):
    print(f"{args[0]}: Started @{datetime.datetime.now()}")
    # peakColProminenceを読み込む
    with open(filePath) as f:
        peakColProminence=[s.strip() for s in f.readlines()]
    for pcpi,pcp in enumerate(peakColProminence):
        print(pcpi,pcp)
    # ファイル名より座標を求める
    baseName=os.path.splitext(os.path.basename(filePath))[0].replace("_pcp","")
    mapAdress=baseName.split("_")
    upperCornerMap=[int(ma) for ma in mapAdress[1].split("-")]
    lowerCornerMap=[int(ma) for ma in mapAdress[2].split("-")]
    # 緯度経度に変換。lowerCornerLat/Lonはタイル座標に+1して右下のタイルの座標を取ってくる事に注意
    # lowerCornerLat/Lon<= 対象範囲 <lowerCornerLat/Lon
    upperLat, upperLon=m2p.tile2latlon(upperCornerMap[0], upperCornerMap[1], upperCornerMap[2])
    lowerLat, lowerLon=m2p.tile2latlon(lowerCornerMap[0], lowerCornerMap[1]+1, lowerCornerMap[2]+1)
    print(upperLat,upperLon)
    print(lowerLat,lowerLon)
    # ベースとなるピクセル座標を計算
    basePixelX=upperCornerMap[1]*defval.const.PIX
    basePixelY=upperCornerMap[2]*defval.const.PIX
    print(f"basePixelX:{basePixelX} basePixelY:{basePixelY}")
    # 南東端のピクセル座標を計算
    lowerPixelX=lowerCornerMap[1]*defval.const.PIX+defval.const.PIX-1
    lowerPixelY=lowerCornerMap[2]*defval.const.PIX+defval.const.PIX-1
    print(f"lowerPixelX:{lowerPixelX} lowerPixelY:{lowerPixelY}")
    # newPeakColProminencsを作成
    tmpPcp=[[
        t for t in pcp.replace("(","").replace(")","").replace(" ","").split(",")
     ] for pcp in peakColProminence]
    newPeakColProminencs=[
        [upperCornerMap[0]                                  # ピクセル座標のレベル
        ,[basePixelX+int(tpcp[1]),basePixelY+int(tpcp[2])]  # (ピーク)pngの座標をピクセル座標に変換
        ,list(m2p.pixel2LatLng(upperCornerMap[0],basePixelX+int(tpcp[1]),basePixelY+int(tpcp[2])))
        ,float(tpcp[0])                                     # ピークの標高
        ,[basePixelX+int(tpcp[4]),basePixelY+int(tpcp[5])]  # (コル)pngの座標をピクセル座標に変換
        ,list(m2p.pixel2LatLng(upperCornerMap[0],basePixelX+int(tpcp[4]),basePixelY+int(tpcp[5])))
        ,float(tpcp[3])                                     # コルの標高
        ,float(tpcp[6])                                     # プロミネンス
        ] for tpcp in tmpPcp
    ]
    del tmpPcp
    # latとlonの位置を入れ替える
    for npcp in newPeakColProminencs:
        npcp[2][0],npcp[2][1]=npcp[2][1],npcp[2][0]
        npcp[5][0],npcp[5][1]=npcp[5][1],npcp[5][0]
#    for npcp in newPeakColProminencs:
#        print(npcp)
    # summitslist.csvを読み込む
    with open("summitslist.csv") as f:
        sl=[sl for sl in csv.reader(f)]
    summitsList=[]
    for sl in sl:
        # 1行目が項目違うので"JA"で始まるものに絞った
        if sl[0].startswith("JA"):
            # 失効していたら次
            if sl[13] < datetime.date.today().strftime("%d/%m/%Y"):
                continue
            # 欲しい項目を型変換しておく
            sl[4]=int(sl[4])    # 標高 intで良いのか不明
            sl[8]=float(sl[8])  # 経度
            sl[9]=float(sl[9])  # 緯度
            if sl[8]>=upperLon and sl[8]<lowerLon and sl[9]<=upperLat and sl[9]>lowerLat:
                pixelX, pixelY = m2p.latlon2PixelPoint(sl[9], sl[8], upperCornerMap[0])
                sl.append([pixelX, pixelY]) # ピクセル座標を末尾に追加
                summitsList.append(sl)
    del sl
    for sli,sl in enumerate(summitsList):
        print(sli,sl)
    # summitsListとの突き合わせ
    matchCnt=0
    for npcp in newPeakColProminencs:
        for sl in summitsList:
            # ピクセル座標で突き合わせる
            if abs(npcp[1][0]-sl[17][0])<=defval.const.ERROR_TOLERANCE and abs(npcp[1][1]-sl[17][1])<=defval.const.ERROR_TOLERANCE:
                # 一致したら後ろに追加
                npcp.append(sl[0])          # SummitCode
                npcp.append(sl[3])          # SummitName
                npcp.append(sl[4])          # AltM
                npcp.append(sl[17])         # ピクセル座標
                npcp.append([sl[8],sl[9]])  # [Longitude,Latitude]
                sl.append("match")  # summitsListの後ろに追加
                matchCnt+=1
                break
#    for npcp in newPeakColProminencs:
#        print(npcp,len(npcp))
    if matchCnt!=len(summitsList):
        for sl in summitsList:
            if len(sl)!=19: # "match"が入っていれば19になる
                print(sl)
        for npcp in newPeakColProminencs:
            print(npcp)
        assert False, "summitsListとのマッチ件数不一致。内容要確認"
    # newPeakColProminencsの更新
    # SummitCodeがついたものとプロミネンスがninimumProminence以上のものだけ残してあとは捨てる
    peakColProminenceFinalist=[npcp for npcp in newPeakColProminencs if len(npcp)==13]
    for npcp in newPeakColProminencs:
        if len(npcp)!=13 and npcp[7]>=defval.const.MINIMUM_PPROMINENCE:
            npcp.append("JA/ZZ-999")    # 取り敢えずダミーコード
            npcp.append("Unknown yet")  # 取り敢えずダミーの名前
            # 標高。一応summitListに形式を合わせておく
            npcp.append(int(Decimal(str(npcp[3])).quantize(Decimal("0"),rounding=ROUND_HALF_UP)))
            npcp.append(npcp[1])        # ピクセル座標
            npcp.append(npcp[2])        # 緯度経度
            peakColProminenceFinalist.append(npcp)
    peakColProminenceFinalist.sort(key=itemgetter(0,1)) # ピクセル座標で並べ替え
    for pcpf in peakColProminenceFinalist:
        print(pcpf)
#
    print(f"{args[0]}: Finished @{datetime.datetime.now()}")
##
if __name__ == '__main__':
    args = sys.argv
    if len(args)>1:
        main(filePath=args[1])
    else:
        print("txtファイルを指定してください")
