import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from src import rp_handler

from BinPack import BinPack

def test_binpack():
    myBinPack = BinPack()
    myBinPack.parts = """
       <svg viewBox="0 0 432.13 593.04">
         <rect width="100" height="50" />
         <rect width="50" height="100" />
         <ellipse rx="20" ry="20" />
       </svg>
    """
    myBinPack.bin = """
       <svg width="300" height="300" viewBox="0 0 300 300">
       </svg>
    """
    result, placed, fails, description = myBinPack.pack()

    assert placed == 3