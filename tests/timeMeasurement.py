import sys
import datetime
import os
import configparser
import cv2
from PIL import Image
import numpy as np
import timeit
#
def cv2normal(tileimg):
    elevs=tileimg[:, :, 2]*np.power(2,16)+tileimg[:, :, 1]*np.power(2,8)+tileimg[:, :, 0]
    elevs0=np.where(elevs<2**23, elevs/100, elevs)          # x < 223の場合　h = xu
    elevs=np.where(elevs0==2**23, 0, elevs0)                # x = 223の場合　h = NA 取り敢えず0とする
    elevs0=np.where(elevs>2**23, (elevs-2**24)/100, elevs)  # x > 223の場合　h = (x-224)u
    elevs=np.where(elevs0<0, 0, elevs0) # マイナス標高は全て0とする
    img=np.zeros(elevs.shape,dtype=np.uint8)
    img[elevs>=2000]=255
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
def cv2withocl(tileimg):
    elevs=tileimg[:, :, 2]*np.power(2,16)+tileimg[:, :, 1]*np.power(2,8)+tileimg[:, :, 0]
    elevs0=np.where(elevs<2**23, elevs/100, elevs)          # x < 223の場合　h = xu
    elevs=np.where(elevs0==2**23, 0, elevs0)                # x = 223の場合　h = NA 取り敢えず0とする
    elevs0=np.where(elevs>2**23, (elevs-2**24)/100, elevs)  # x > 223の場合　h = (x-224)u
    elevs=np.where(elevs0<0, 0, elevs0) # マイナス標高は全て0とする
    img=np.zeros(elevs.shape,dtype=np.uint8)
    img[elevs>=2000]=255
    contours, hierarchy = cv2.findContours(cv2.UMat(img), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#
def main():
    print(f"{__name__}: Started @{datetime.datetime.now()}")
#
#    val = range(100000000)
    loop = 10
    tileimg = cv2.imread("tiles/5338-00_15-28945-12867_15-29036-12942.png")
    result = timeit.timeit(lambda:cv2normal(tileimg), globals=globals(), number=loop)
    print(f"avg-> cv2normal():{result / loop}")
    result = timeit.timeit(lambda:cv2withocl(tileimg), globals=globals(), number=loop)
    print(f"avg-> cv2withocl():{result / loop}")
#
    print(f"{__name__}: Finished @{datetime.datetime.now()}")
#
if __name__ == '__main__':
    print(f"{sys.argv[0]}: Started @{datetime.datetime.now()}")
    args = sys.argv[1:]
    main()
    print(f"{sys.argv[0]}: Finished @{datetime.datetime.now()}")
