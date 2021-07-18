import sys
import datetime
import os
import pprint
import configparser
#import requests
#import io
import cv2
import psutil
#
#from .context import findsummits
#import analyzePng as ap
## defval
# その他
#
def main():
    print(f"{__name__}: Started @{datetime.datetime.now()}")
#
#    print(cv2.useOptimized())
    print(os.cpu_count())
    print(psutil.cpu_count())
    print(psutil.cpu_count(logical=False))
#
    print(f"{__name__}: Finished @{datetime.datetime.now()}")
#---
if __name__ == '__main__':
    print(f"{sys.argv[0]}: Started @{datetime.datetime.now()}")
    args = sys.argv
    main()
    print(f"{sys.argv[0]}: Finished @{datetime.datetime.now()}")
