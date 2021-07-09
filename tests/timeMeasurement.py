import sys
import datetime
import os
import configparser
import cv2
from PIL import Image
import numpy as np
import timeit
#
def newimagepil():
    img = Image.new("RGB",(256, 256),(128,0,0))
def newimagenp():
    img = np.zeros((256,256,3),dtype=np.uint8)
    img[:, :, 0] = 128
#
def main():
    print(f"{__name__}: Started @{datetime.datetime.now()}")
#
    loop = 10
    result = timeit.timeit("newimagepil()", globals=globals(), number=loop)
    print(result / loop)
    result = timeit.timeit("newimagenp()", globals=globals(), number=loop)
    print(result / loop)
#
    print(f"{__name__}: Finished @{datetime.datetime.now()}")
#
if __name__ == '__main__':
    print(f"{sys.argv[0]}: Started @{datetime.datetime.now()}")
    args = sys.argv[1:]
    main()
    print(f"{sys.argv[0]}: Finished @{datetime.datetime.now()}")
