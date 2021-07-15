import sys
import datetime
import os
import configparser
import cv2
from PIL import Image
import numpy as np
import timeit
#
def normal(img):
    elevs0=img[:, :, 2]*(2**16)+img[:, :, 1]*(2**8)+img[:, :, 0]
def cv2read(img):
    elevs0=img[:, :, 2]*np.power(2,16)+img[:, :, 1]*np.power(2,8)+img[:, :, 0]
#
def main():
    print(f"{__name__}: Started @{datetime.datetime.now()}")
#
#    val = range(100000000)
    loop = 10
    img = cv2.imread("tiles/5338-00_15-28945-12867_15-29036-12942.png")
    result = timeit.timeit(lambda:normal(img), globals=globals(), number=loop)
    print(f"avg-> pilread():{result / loop}")
    result = timeit.timeit(lambda:cv2read(img), globals=globals(), number=loop)
    print(f"avg-> cv2read():{result / loop}")
#
    print(f"{__name__}: Finished @{datetime.datetime.now()}")
#
if __name__ == '__main__':
    print(f"{sys.argv[0]}: Started @{datetime.datetime.now()}")
    args = sys.argv[1:]
    main()
    print(f"{sys.argv[0]}: Finished @{datetime.datetime.now()}")
