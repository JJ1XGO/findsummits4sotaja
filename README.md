# findsummits4sotaja

国土地理院が提供している標高タイルを取得して、SOTA(Summits On The Air)日本支部で対象となる山岳を探し出すプログラム。

# Features
 
 
# Requirement

ハード
* linuxが動作するPC
* CPU：性能が良ければ良い程良いです。
* メモリ：16Gbyte以上を推奨。実行時の使用量は4Gbyte程度ですが、海面の占める割合が大きかったりすると最後10Gbyte超を使用するケースあり。

※Macでも動作するかもしれませんが未確認。

ソフト
* python3
* poetry
 
# Installation
 
Requirementで列挙したライブラリなどのインストール方法 
 
# Usage
 
python3 -m findsummits 1次メッシュコード -s {04,40,44}  
python3 -m findsummits 最も南西の2次メッシュコード -e 最も北東の2次メッシュコード
 
# Note
 
* pythonをはじめ、git/Github/Geojson等、全て0からのスタートなので、コードが見難かったりする部分が多々あると思いますがご容赦ください。
* 地域メッシュと地理院タイルの開始点は一致していないので、指定した基準地域メッシュのエリアを含む領域の標高タイルを取得して分析しています。
* あと、めちゃくちゃ処理に時間が掛かります。今後の課題として取り組む予定。
 
# Author
 
JJ1XGO/Tsutomu Saito JJ1XGO@gmail.com
 
# License
 
findsummits4sotaja is under [GPLv2 license](https://www.gnu.org/licenses/old-licenses/gpl-2.0.ja.html).
 
# Source

出典:国土地理院/地理院タイル [地理院タイル一覧ページ](https://maps.gsi.go.jp/development/ichiran.html)
