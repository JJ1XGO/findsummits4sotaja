import sys
import datetime
import os
import pprint
import configparser
#import os
#import requests
#import io
#
#from .context import findsummits
#import analyzePng as ap
## defval
# その他
#
def main():
    print(f"{__name__}: Started @{datetime.datetime.now()}")
#
    print([None]*10)
    print(type([None]*10))
    print(len([None]*10))
#
    print(f"{__name__}: Finished @{datetime.datetime.now()}")
#---
if __name__ == '__main__':
    print(f"{sys.argv[0]}: Started @{datetime.datetime.now()}")
    args = sys.argv
    main()
    print(f"{sys.argv[0]}: Finished @{datetime.datetime.now()}")
