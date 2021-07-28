import sys
import os
import argparse
print("__init__.py")
print(sys.path)
print(os.path.abspath(os.path.join(os.path.dirname(__file__))))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
print(sys.path)
from . import meshcd2png
from . import analyzePng
from . import resultMerge
from . import resultOutput
