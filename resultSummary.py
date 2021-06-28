import sys
import datetime
import os
import csv
import meshcd2png as m2p
## defval
# 座標を求める際に使用する定数
pix=256     # pngタイルの縦横dot数でもある
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
    basePixelX=upperCornerMap[1]*pix
    basePixelY=upperCornerMap[2]*pix
    print(basePixelX,basePixelY)
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
            sl[8]=float(sl[8])
            sl[9]=float(sl[9])
            if sl[8]>=upperLon and sl[8]<lowerLon and sl[9]<=upperLat and sl[9]>lowerLat:
                summitsList.append(sl)
                pixelX, pixelY = m2p.latlon2PixelPoint(sl[9], sl[8], upperCornerMap[0])
                print(pixelX, pixelY)
    del sl
    for sli,sl in enumerate(summitsList):
        print(sli,sl)
#
    print(f"{args[0]}: Finished @{datetime.datetime.now()}")
##
if __name__ == '__main__':
    args = sys.argv
    if len(args)>1:
        main(filePath=args[1])
    else:
        print("txtファイルを指定してください")
