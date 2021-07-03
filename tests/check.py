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
    print(os.path.dirname(__file__))
    config=configparser.RawConfigParser()
    config.add_section("VAL")
    config.set("VAL","L",85.05112878)
    config.set("VAL","PIX",256)
    config.set("VAL","ZOOM_LVL",15)
    with open("config.ini","w") as f:
        config.write(f)
#
    config=configparser.ConfigParser()
    config.read("config.ini")
    print(config.sections())
#
    print(f"{__name__}: Finished @{datetime.datetime.now()}")
#---
if __name__ == '__main__':
    print(f"{sys.argv[0]}: Started @{datetime.datetime.now()}")
    args = sys.argv
    main()
    print(f"{sys.argv[0]}: Finished @{datetime.datetime.now()}")
