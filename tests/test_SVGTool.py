
import unittest
from unittest.mock import patch, MagicMock, mock_open, Mock
import sys
import os
import xml.etree.ElementTree as ET
# Make sure that "src" is known and can be used to import rp_handler.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from src import SVGTool

combined_svg = ""

shape1 = """
<!-- T-shirt -->
<polygon id="full" points="561.00,90.00 441.00,29.00 350.00,0.00 327.00,15.00 286.00,21.00 235.00,17.00 202.00,2.00 123.00,30.00 0.00,95.00 60.00,202.00 110.00,191.00 111.00,570.00 458.00,566.00 455.00,186.00 505.00,199.00" fill="none" role="stock"/>
"""
shape2 = """
<rect x="0" y="0" width="1200" height="750" fill="url(#grid)"></rect>
"""

svg1 = f"""
<svg viewBox="0 0 1200 750" aria-label="Draggable garment parts" id="board">
      {shape1}
</svg>
"""

svg2 = f"""
<svg viewBox="0 0 1200 750" aria-label="Draggable garment parts" id="board">
      {shape2}
  </svg>
"""

class TestSVGTool(unittest.TestCase):
    def test_combine(self):
        combined_svg = SVGTool.SVGTool.combine([svg1, svg2])

        self.assertIn("rect", combined_svg, f"Didn't find a SVG in the combined SVG {combined_svg} ")
        self.assertIn("polygon", combined_svg, f"Didn't find a SVG in the combined SVG {combined_svg} ")

    def test_extract(self):
        combined_svg = SVGTool.SVGTool.combine([svg1, svg2])
        extracted_svgs = SVGTool.SVGTool.extract(combined_svg)

        print(f"extracted {extracted_svgs}")
        self.assertIs(len(extracted_svgs), 2, f"extracted {extracted_svgs} should have 2 extracted SVGs")

    import xml.etree.ElementTree as ET
    def test_apply_attributes(self):
        with_attributes = SVGTool.SVGTool.apply_attribute_to_shapes(svg1,"role","garment")

        root = ET.fromstring(svg1)
        for elem in root:
            attribs = list(elem.attrib.items())

            self.assertTrue(elem.attrib.get("role") == "stock", f"{attribs} should have role attribute")