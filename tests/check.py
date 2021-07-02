import sys
import datetime
import pprint
#import os
#import requests
#import io
#
#import analyzePng as ap
## defval
# その他
#
def main():
    print(f"{__name__}: Started @{datetime.datetime.now()}")
#
    pprint.pprint(sys.path)
#
    print(f"{__name__}: Finished @{datetime.datetime.now()}")
#---
if __name__ == '__main__':
    print(f"{sys.argv[0]}: Started @{datetime.datetime.now()}")
    args = sys.argv
    main()
    print(f"{sys.argv[0]}: Finished @{datetime.datetime.now()}")
