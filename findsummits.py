#--------Import modules-------------------------
import sys
import datetime
import pathlib
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
import zipfile
from collections import OrderedDict
import traceback
import gc
# for debug
from pprint import pprint

# １次メッシュ対象範囲の縦横数
mesh_ns=0   #縦の数
mesh_ew=0   #横の数

zipFile = "FG-GML-%d-*.zip"
#xmlFile = "FG-GML-%d-*.xml"

mesh_width = 1125
mesh_height = 750

def argv_chk(argv):
    try:
#        pprint(argv)
        if len(argv)<2 or len(argv)>3:
            raise Exception
        if argv[1].isdigit():
            pass
        else:
            raise Exception
        if len(argv)==3:
            if argv[2].isdigit():
                if argv[1]<=argv[2]:
                    pass
                else:
                    raise Exception
            else:
                raise Exception
    except:
        print("Usage: python3 findsummit.py start_mesh_no end_mesh_no")
        print("mesh_no is PrimaryMeshNo(9999)")
        sys.exit(1)

# 1次メッシュ対象範囲の特定/生成
def scope_mesh_generate(start_mesh, end_mesh):
    start_mesh12 = int(start_mesh/100)  #南北方向の開始No(1-2桁目)
    start_mesh34 = int(start_mesh%100)  #東西方向の開始No(3-4桁目)
    end_mesh12 = int(end_mesh/100)      #南北方向の終了No(1-2桁目)
    end_mesh34 = int(end_mesh%100)      #東西方向の終了No(3-4桁目)
    # for debug
    #print("start_mesh12="+str(start_mesh12))
    #print("start_mesh34="+str(start_mesh34))
    #print("end_mesh12="+str(end_mesh12))
    #print("end_mesh34="+str(end_mesh34))

    mesh12 = np.linspace(start_mesh12,end_mesh12,end_mesh12-start_mesh12+1,dtype="int")   #南北方向の対象範囲を配列に入れる
    mesh34 = np.linspace(start_mesh34,end_mesh34,end_mesh34-start_mesh34+1,dtype="int") #東西方向の対象範囲を配列に入れる

    # for debug
    #pprint(mesh12)
    #pprint(mesh34)

    #対象範囲を生成
    mesh_ns=len(mesh12) #南北方向の配列数
    mesh_ew=len(mesh34) #東西方向の配列数
    scope_mesh=np.empty(mesh_ns*mesh_ew)
    for i in range(mesh_ns):
        for j in range(mesh_ew):
            scope_mesh[i*mesh_ew+j]=mesh12[i]*100+mesh34[j]
    results=np.reshape(scope_mesh,(mesh_ns,mesh_ew))
    return results,mesh_ns,mesh_ew

# zipからファイル名を指定してxmlファイルを読み込む
def get_xml_from_zip(zip_file, re_match):
    file_datas = OrderedDict()
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_data:
            # ファイルリスト取得
            infos = zip_data.infolist()
#            pprint(infos)
            for info in infos:
                # ファイルパスでスキップ判定
                if re_match(info.filename) is None:
                    print("No match",info.filename)
                    continue

                # zipからファイルデータを読み込む
                file_data = zip_data.read(info.filename)

                # ファイルパスをキーにして辞書に入れる
                file_datas[info.filename] = file_data

    except zipfile.BadZipFile:
        print(traceback.format_exc())

    return file_datas

def get_data_from_xml(file, data):
    # 内容確認用にファイル名からメッシュ情報を取り出す
    fileNamePurse=file.split("-")
    fileNameMesh1=fileNamePurse[2]
    fileNameMesh2=fileNamePurse[3]
    fileNameMesh3=fileNamePurse[4]
#    print("mesh1="+fileNameMesh1+" mesh2="+fileNameMesh2+" mesh3="+fileNameMesh3)

    strdata=data.decode("utf-8")   # dataはbytes型なのでstr型にdecode

    # mesh
    r = re.compile("<mesh>(.+)</mesh>") # <mesh>の正規表現オブジェクト生成
    m = r.search(strdata)    # <mesh>を検索
    if m != None:       # あったら
        mesh = m.group(1)   # マッチした文字列を取得
    if mesh != fileNameMesh1+fileNameMesh2+fileNameMesh3:
        print("Consistency Error!! FileName="+file+" xml<mesh>="+mesh)
        sys.exit(1)

    # lowerCorner
    r = re.compile("<gml:lowerCorner>(.+) (.+)</gml:lowerCorner>")
    m = r.search(strdata)
    if m != None:
        xlowerCorner = float(m.group(1))  # ３次メッシュの一番北西の経度
        ylowerCorner = float(m.group(2))  # ３次メッシュの一番北西の緯度
#    print("mesh xlowerCorner="+str(xlowerCorner)+" ylowerCorner="+str(ylowerCorner))
    # upperCorner
    r = re.compile("<gml:upperCorner>(.+) (.+)</gml:upperCorner>")
    m = r.search(strdata)
    if m != None:
        xupperCorner = float(m.group(1))  # ３次メッシュの一番北西の経度
        yupperCorner = float(m.group(2))  # ３次メッシュの一番北西の緯度
#    print("mesh xupperCorner="+str(xupperCorner)+" yupperCorner="+str(yupperCorner))
    # grid len
    r = re.compile("<gml:high>(.+) (.+)</gml:high>")
    m = r.search(strdata)
    if m != None:
        xlen = int(m.group(1)) + 1  # highのX値(5mメッシュだと224)+1
        ylen = int(m.group(2)) + 1  # highのY値(5mメッシュだと149) +1
#    print("mesh xlen="+str(xlen)+" ylen="+str(ylen))
#    # 単位データ毎の緯度/経度を後で付加するため、単位データ当たりの緯度/経度を求めておく
#    xUnitData=(xupperCorner-xlowerCorner)/xlen
#    yUnitData=(yupperCorner-ylowerCorner)/ylen

    # start point
    startx = starty = 0
    r = re.compile("<gml:startPoint>(.+) (.+)</gml:startPoint>")
    m = r.search(strdata)
    if m != None:
        startx = int(m.group(1))    # startPoint X の値をセット
        starty = int(m.group(2))    # startPoint Y の値をセット
#    print("start from startx="+str(startx)+" starty="+str(starty))
    # data
    data = []
    r = re.compile(",(.+)")
    m = r.findall(strdata)
    if m != None:
        for d in m:
            h=d.strip()
            data.append(float(h))  # dataリストに値(標高)を追加

    data2 = np.empty(xlen*ylen) # 配列生成
    start_pos = starty*xlen + startx    # startPoint(0 1)の場合、1x150+0=150

    lendata=len(data)   # データ数を確認

    for i in range(xlen*ylen):
        if i < start_pos or i > lendata+start_pos-1:
#            data2[i] = -9999.                  # 先頭から始まってなければ-9999を入れる
            data2[i] = 0                        # 先頭から始まってなければ 0 を入れる
        else:
            if data[i-start_pos] < 0:
                data2[i] = 0                    # マイナス値なら 0 を入れる
            else:
                data2[i] = data[i-start_pos]    # startPointに達したら値を入れる

    data = data2.reshape(ylen, xlen)    # 2次元配列に変換。xlen列分、ylen行作る
    return data, fileNameMesh1, fileNameMesh2, fileNameMesh3\
#        ,xlowerCorner, ylowerCorner, xupperCorner, yupperCorner
#-------------Main---------------------------------
def main():
    print(sys.argv[0]+": Started @",datetime.datetime.now())

#    print("debug:sys.argv="+str(sys.argv))
#    print("debug:len(sys.argv)="+str(len(sys.argv)))
#    for i in range(len(sys.argv)):
#        print("debug:sys.argv["+str(i)+"]="+sys.argv[i])
    argv_chk(sys.argv)

# 1次メッシュ対象範囲の特定
    start_mesh = int(sys.argv[1])
    if len(sys.argv)==2:
        end_mesh = start_mesh
    else:
        end_mesh = int(sys.argv[2])

    scope_mesh,mesh_ns,mesh_ew=scope_mesh_generate(start_mesh, end_mesh)
    print("Scope Primary Mesh No")
    pprint(scope_mesh)
    print("1nd mesh  -> NS*EW=%d*%d=%d" %(mesh_ns,mesh_ew,mesh_ew*mesh_ns))
    print("2nd mesh  -> NS*EW=%d*%d=%d" %(mesh_ns*8,mesh_ew*8,mesh_ns*8*mesh_ew*8))
    print("3rd mesh  -> NS*EW=%d*%d=%d" %(mesh_ns*8*10,mesh_ew*8*10,mesh_ns*8*10*mesh_ew*8*10))
    print("data mesh -> NS*EW=%d*%d=%d" %(mesh_ns*8*10*150,mesh_ew*8*10*225,mesh_ns*8*10*150*mesh_ew*8*10*225))
    gsigridmap=np.zeros(mesh_ns*8*10*150*mesh_ew*8*10*225).reshape(mesh_ns, mesh_ew, 8, 8, 10, 10, 150, 225)    # GSIのメッシュ領域型にreshape
#    print(gsigridmap.shape)
#    pprint(gsigridmap)

# zipファイル読み込み
    zipdir=pathlib.Path("data")
    for i in range(mesh_ns):        # 1次メッシュ南北方向
        for j in range(mesh_ew):    # 1次メッシュ東西方向
            srczip="FG-GML-%d-*.zip" %(scope_mesh[i][j])
            for zf in zipdir.glob(srczip):  # 取得出来たzipファイルは２次メッシュレベル
                print(zf)
                st=str(zf)[5:20]+".+\.xml"
                regexml=re.compile(st).match
                xmls=get_xml_from_zip(zf,regexml)   # zipの中からxmlの内容を読み込む
                for (xfile, xdata) in xmls.items():   # 取得できたxmlファイルは3次メッシュレベル
                    # ファイル名
#                    print('xml file: %s' % xfile)
                    (data, Mesh1, Mesh2,Mesh3\
#                    ,xlowerCorner\
#                    ,ylowerCorner\
#                    ,xupperCorner\
#                    ,yupperCorner\
                    )=get_data_from_xml(xfile, xdata)
#                    print("Mesh1="+Mesh1)
#                    print("Mesh2="+Mesh2)
#                    print("Mesh3="+Mesh3)
##                    print("xlowerCorner="+str(xlowerCorner))
##                    print("ylowerCorner="+str(ylowerCorner))
##                    print("xupperCorner="+str(xupperCorner))
##                    print("yupperCorner="+str(yupperCorner))
                    gsiIdxNS1=0        # 1次メッシュ南北方向の座標
                    gsiIdxEW1=0        # 1次メッシュ東西方向の座標
                    for ii in range(mesh_ns):
                        for jj in range(mesh_ew):
                            if scope_mesh[ii,jj]==Mesh1:
                                gsiIdxNS1=ii        # 1次メッシュ南北方向の座標
                                gsiIdxEW1=jj        # 1次メッシュ東西方向の座標
                                break
                        else:
                            continue
                        break
                    gsiIdxNS2=int(int(Mesh2)/10)    # 2次メッシュ南北方向の座標
                    gsiIdxEW2=int(Mesh2)%10         # 2次メッシュ東西方向の座標
                    gsiIdxNS3=int(int(Mesh3)/10)    # 3次メッシュ南北方向の座標
                    gsiIdxEW3=int(Mesh3)%10         # 3次メッシュ東西方向の座標
#                    print("gsiIdxNS1="+str(gsiIdxNS1))
#                    print("gsiIdxEW1="+str(gsiIdxEW1))
#                    print("gsiIdxNS2="+str(gsiIdxNS2))
#                    print("gsiIdxEW2="+str(gsiIdxEW2))
#                    print("gsiIdxNS3="+str(gsiIdxNS3))
#                    print("gsiIdxEW3="+str(gsiIdxEW3))
#                    for idxns in range(150):
#                        for idxew in range(225):
#                            gsigridmap[\
#                             gsiIdxNS1,gsiIdxEW1\
#                            ,gsiIdxNS2,gsiIdxEW2\
#                            ,gsiIdxNS3,gsiIdxEW3\
#                            ,idxns,idxew]=data[idxns,idxew]
#                            if gsigridmap[\
#                             gsiIdxNS1,gsiIdxEW1\
#                            ,gsiIdxNS2,gsiIdxEW2\
#                            ,gsiIdxNS3,gsiIdxEW3\
#                            ,idxns,idxew]!=0:
#                                print(str(gsigridmap[\
#                                 gsiIdxNS1,gsiIdxEW1\
#                                ,gsiIdxNS2,gsiIdxEW2\
#                                ,gsiIdxNS3,gsiIdxEW3\
#                                ,idxns,idxew]))

                    gsigridmap[
                     gsiIdxNS1,gsiIdxEW1\
                    ,gsiIdxNS2,gsiIdxEW2\
                    ,gsiIdxNS3,gsiIdxEW3
                    ]=data

# gsigridmapはGSIと同じ形で敷き詰められているので、
# imggridmapに対して1枚のイメージに敷き詰め直す
    imglist=[]
    for gsiIdxNS1 in range(mesh_ns):                            # 一番南の方から取っていく:1次メッシュレベル
        for gsiIdxNS2 in range(8):                              # 一番南の方から取っていく:2次メッシュレベル
            for gsiIdxNS3 in range(10):                         # 一番南の方から取っていく:3次メッシュレベル
                for gsiIdxNS4 in range(149,-1,-1):              # 一番南の方から取っていく:標高データレベル(標高データは北から入っているので注意)
                    for gsiIdxEW1 in range(mesh_ew):            # 一番西の方から取っていく:1次メッシュレベル
                        for gsiIdxEW2 in range(8):              # 一番西の方から取っていく:2次メッシュレベル
                            for gsiIdxEW3 in range(10):         # 一番西の方から取っていく:3次メッシュレベル
#                                for gsiIdxEW4 in range(225):   # 一番西の方から取っていく:標高データレベル
                                imglist.extend(\
                                    gsigridmap[\
                                     gsiIdxNS1,gsiIdxEW1\
                                    ,gsiIdxNS2,gsiIdxEW2\
                                    ,gsiIdxNS3,gsiIdxEW3\
                                    ,gsiIdxNS4\
                                    ]\
                                )
# adhoc
    del gsigridmap
    gc.collect()
#    print(str(len(imglist)))
    imggridmap=np.array(imglist).reshape(mesh_ew*8*10*225,mesh_ns*8*10*150) # 全部入ったらreshape
# イメージ出力
    plt.imshow(imggridmap)
    plt.colorbar()
    plt.show()

    print(sys.argv[0]+": Finished @",datetime.datetime.now())

if __name__ == '__main__':
    main()
