import sys
import datetime
import os
import configparser
import cv2
from PIL import Image
import numpy as np
import timeit
#
def pilread():
    img = np.array(Image.open("tiles/0000-00_15-28967-12895_15-28977-12905.png"))
    imgcv2 = cv2.cvtColor(img,cv2.COLOR_RGB2BGR)
def cv2read():
    img = cv2.imread("tiles/0000-00_15-28967-12895_15-28977-12905.png")
def pilwrite(img):
    img.save("tiles/test.png")
def cv2write(img):
    imgcv2 = cv2.cvtColor(np.array(img),cv2.COLOR_RGB2BGR)
    cv2.imwrite("tiles/test.png",imgcv2)
#
def main():
    print(f"{__name__}: Started @{datetime.datetime.now()}")
#
#    val = range(100000000)
    loop = 10
    result = timeit.timeit("pilread()", globals=globals(), number=loop)
    print(f"avg-> pilread():{result / loop}")
    result = timeit.timeit("cv2read()", globals=globals(), number=loop)
    print(f"avg-> cv2read():{result / loop}")
#
    img = Image.open("tiles/0000-00_15-28967-12895_15-28977-12905.png")
    result = timeit.timeit(lambda: pilwrite(img), globals=globals(), number=loop)
    print(f"avg-> pilwrite():{result / loop}")

    result = timeit.timeit(lambda: cv2write(img), globals=globals(), number=loop)
    print(f"avg-> cv2write():{result / loop}")
#
    print(f"{__name__}: Finished @{datetime.datetime.now()}")
#
if __name__ == '__main__':
    print(f"{sys.argv[0]}: Started @{datetime.datetime.now()}")
    args = sys.argv[1:]
    main()
    print(f"{sys.argv[0]}: Finished @{datetime.datetime.now()}")
