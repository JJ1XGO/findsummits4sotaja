import const
from fractions import Fraction
#
## defval
# 座標を求める際に使用する定数
const.L=Fraction(85.05112878)   # あまり意味ないかもしれないけど、一応Fractionにしておく
const.PIX=256     # pngタイルの縦横dot数でもある
#
const.ZOOM_LVL=15   # 最も詳細な標高データが入ったzoomレベル
const.MINIMUM_PPROMINENCE=150   # プロミネンス(ピークとコルの標高差)最小値
const.FILTER_SIZE=64
# イメージの中を縦横filter_size(ピクセル)毎に分割し、その区画毎にピークを見つけ出すためのパラメータ
# 標高タイルは一辺が256ピクセルで、レベル15だと1つのタイルの中にピークはせいぜい1〜2座だと思うので、
# 一辺を2分割した128くらいで良いと思うが、一応 64 をデフォルト値としておく。
const.CANDIDATE_BORDERLINE=8
# 外枠付近で見つかるピーク候補は、殆どがイメージ外から続く稜線上の最高地点なので
# 外枠からcandidateBorderline以内の座標にあるピーク候補は外す
const.ERROR_TOLERANCE=24    # JA/YN-009 Gongendake 24
# peakColProminenceとsummitListをピクセル座標で突き合わせる時に、
# 何ピクセルまでの違いなら誤差とするかの許容範囲。レベル15で1ピクセル5m。
# 実際にやりながら調整する

# ファイルを保存するディレクトリ
const.TILE_DIR="tiles"
const.PCP_DIR="pcps"
const.IMAGE_DIR="images"
const.BACKUP_DIR="backups"
# ファイル
const.PEAKCOLINFO="peakColProminenceAll.csv"
