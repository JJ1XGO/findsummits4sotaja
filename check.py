import sys
import datetime
import inspect
import numpy as np
#import os
#import requests
#import io
from operator import itemgetter
from itertools import product
from scipy.ndimage.filters import maximum_filter
#from PIL import Image
import matplotlib.pyplot as plt
#
import analyzePng as ap
## defval
# その他
# ピークを見つけ出す
def detectPeaksCoords(image, filter_size=20):
    local_max = maximum_filter(image, footprint=np.ones((filter_size, filter_size)), mode='constant')
    detected_peaks = np.ma.array(image, mask=~(image == local_max))

    # 小さいピーク値を排除（150m以下のピークは排除）
    temp = np.ma.array(detected_peaks, mask=~(detected_peaks >= 150))
    peaks_index = np.where(temp.mask != True)
    return list(zip(*np.where(temp.mask != True)))

def main():
    f=inspect.currentframe()
    myName=inspect.getframeinfo(f)[0].split("/")[-1].replace("py","")+inspect.getframeinfo(f)[2]+"()"
    print(f"{myName}: Started @{datetime.datetime.now()}")
#
    print(f"{myName}: Finished @{datetime.datetime.now()}")
#---
if __name__ == '__main__':
    print(f"{sys.argv[0]}: Started @{datetime.datetime.now()}")
    args = sys.argv
    main()
    print(f"{sys.argv[0]}: Finished @{datetime.datetime.now()}")
