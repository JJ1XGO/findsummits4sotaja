import sys
import datetime
import os
import pprint
import configparser
#import os
#import requests
#import io
import cv2
#
#from .context import findsummits
#import analyzePng as ap
## defval
# その他
#
def main():
    print(f"{__name__}: Started @{datetime.datetime.now()}")
#
    print(cv2.useOptimized())
#
    print(f"{__name__}: Finished @{datetime.datetime.now()}")
#---
if __name__ == '__main__':
    print(f"{sys.argv[0]}: Started @{datetime.datetime.now()}")
    args = sys.argv
    main()
    print(f"{sys.argv[0]}: Finished @{datetime.datetime.now()}")
