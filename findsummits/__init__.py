import sys
import os
#print(sys.path)
#print(os.path.abspath(os.path.join(os.path.dirname(__file__))))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
#print(sys.path)
import meshcd2png
import analyzePng
import resultMerge
import resultOutput
