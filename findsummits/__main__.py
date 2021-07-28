import argparse
import meshcd2png
import analyzePng
import resultMerge
import resultOutput
#
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("meshcd",help="基準地域メッシュコード(1次or2次)",type=int)
    group=parser.add_mutually_exclusive_group()
    group.add_argument("-s","--start2ndmeshcd",choices=["04","40","44"]
        ,help="1次メッシュ指定時、スタート基点をずらす場合の2次メッシュコード下2桁")
    group.add_argument("-e","--end2ndmeshcd",type=int
        ,help="2次メッシュ指定時の終了2次メッシュコード")
    args=parser.parse_args()
    ret=meshcd2png.main(meshcd=args.meshcd,
        start2ndmeshcd=args.start2ndmeshcd,
        end2ndmeshcd=args.end2ndmeshcd)
    ret=analyzePng.main(filePath=ret)
    ret=resultMerge.main(filePath=ret)
    resultOutput.main()
#
if __name__ == '__main__':
    main()
