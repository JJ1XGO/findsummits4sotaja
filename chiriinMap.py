import sys
import datetime
import numpy as np
import os
import requests
import io
from PIL import Image
import matplotlib.pyplot as plt

def get_tile(z, x, y):
    """
    今回は標準地図を取得するとしてURLを指定する。
    与えられた座標に対応する地理院地図タイル画像を保存する。
    """
    url = "https://cyberjapandata.gsi.go.jp/xyz/dem5a_png/{}/{}/{}.png".format(z, x, y)
    file_name = "tile/{}_{}_{}.jpg".format(z, x, y)

    imgtile = Image.open(io.BytesIO(requests.get(url).content))

#    with open(file_name, "wb") as aaa:
#        aaa.write(imgtile)
#    cv2.imwrite("tile/tile.png", image)
    plt.imshow(imgtile)
    plt.show()

def main():
    print(sys.argv[0]+": Started @",datetime.datetime.now())
    get_tile(15,28945,12942)
    print(sys.argv[0]+": Finished @",datetime.datetime.now())
#---
if __name__ == '__main__':
    main()
