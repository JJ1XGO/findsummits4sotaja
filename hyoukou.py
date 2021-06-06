import sys
import re
import numpy as np
import matplotlib.pyplot as plt

with open(sys.argv[1], "r") as f:
    # mesh
    r = re.compile("<mesh>(.+)</mesh>") # <mesh>の正規表現オブジェクト生成
    for ln in f:    # ファイル読み込み
        m = r.search(ln)    # <mesh>を検索
        if m != None:       # あったら
            mesh = m.group(1)   # マッチした文字列を取得
            break
    # grid len
    r = re.compile("<gml:high>(.+) (.+)</gml:high>")
    for ln in f:
        m = r.search(ln)
        if m != None:
            xlen = int(m.group(1)) + 1  # highのX値(5mメッシュだと224)+1
            ylen = int(m.group(2)) + 1  # highのY値(5mメッシュだと149) +1
            break
    # start
    r = re.compile("<gml:tupleList>")
    for ln in f:
        m = r.search(ln)
        if m != None:
            break
    # data
    data = []
    r  = re.compile("</gml:tupleList>")
    r2 = re.compile(",(.+)")
    for ln in f:
        m = r.search(ln)
        if m != None:   # </gml:tupleList>なら抜ける
            break
        else:
            m = r2.search(ln)
            if m != None:
                data.append(float(m.group(1)))  # dataリストに値(標高)を追加
    # start point
    startx = starty = 0
    r = re.compile("<gml:startPoint>(.+) (.+)</gml:startPoint>")
    for ln in f:
        m = r.search(ln)
        if m != None:
            startx = int(m.group(1))    # startPoint X の値をセット
            starty = int(m.group(2))    # startPoint Y の値をセット
            break

data2 = np.empty(xlen*ylen) # 配列生成
start_pos = starty*xlen + startx    # startPoint(0 1)の場合、1x150+0=150

lendata=len(data)
print(lendata)

for i in range(xlen*ylen):
    if i < start_pos or i > lendata+start_pos-1:
        data2[i] = -9999.               # 先頭から始まってなければ-9999を入れる
    else:
        data2[i] = data[i-start_pos]    # startPointに達したら値を入れる

data = data2.reshape(ylen, xlen)    # 2次元配列に変換。xlen列分、ylen行作る

#print(data)
plt.imshow(data)
plt.colorbar()
plt.show()
