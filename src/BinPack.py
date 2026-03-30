import sys
import os
import math
import xml.etree.ElementTree as ET

sys.path.append('/home/parallels/PycharmProjects/Packaide/python')
packaide_path = os.path.join('/app', 'Packaide', 'python')
if packaide_path not in sys.path:
    sys.path.append(packaide_path)

import packaide

class BinPack:
    def __init__(self):

        ## A default bin
        self.bin = """
           <svg width="300" height="300" viewBox="0 0 300 300">
           </svg>
        """

    def _detect_irregular_stock(self):
        # Assume its all irregular for now.
        return True

    def make_irregular_stock_then_pack(self):
        if self._detect_irregular_stock():
            # Doesn't return just sets a new self.bin
            self._make_irregular_stock_with_packed_holes()

        return self.pack()

    def _get_bin_svg_size(self):
        root = ET.fromstring(self.bin)

        width = float(root.get("width").replace("px", "").strip())
        height = float(root.get("height").replace("px", "").strip())

        return width, height

    def _make_irregular_stock_with_packed_holes(self):
        holes = """
            <svg xmlns="http://www.w3.org/2000/svg"
                 width="135000px" height="142800px"
                 viewBox="0.00 0.00 135000.00 142800.00">"""

        # holes should be roughtly this percentage of the SVG
        # how many holes will fit across the image
        holes_across = 32
        hole_scale = 1/holes_across
        width, height = self._get_bin_svg_size()

        holeWidth = width * hole_scale

        # how many holes will fit vertically?
        holes_down = height / holeWidth

        # Total number of holes to fill the image should be a *max* of down x across
        numberOfHoles = holes_across * holes_down
        # Assume only 20% of the image will be empty.
        numberOfHoles = int(math.ceil(numberOfHoles * 0.2))

        print("DEBUG numberOfHoles: ", numberOfHoles)
        for i in range(numberOfHoles):
            holes = holes + f'<circle r="{holeWidth / 2}" />'

        holes = holes + "</svg>"

        # Pack holds around the bin
        result, placed, fails = packaide.pack(
            [self.bin],
            holes,
            tolerance=2.5,  # Discretization tolerance
            offset=0,  # The offset distance around each shape (dilation)
            partial_solution=True,  # Whether to return a partial solution
            rotations=1,  # The number of rotations of parts to try
            persist=False  # Cache results to speed up next run
        )

        print("DEBUG: This is the hole-y bin:")
        print(result[0][1])

        # The result is the new bin with packed shapes interpreted as "holes" by packaide during self.pack()
        self.bin = result[0][1]

    def pack(self):
        if not isinstance(self.parts, str):
            return {"error": "Please provide at least one part."}


        # Attempts to pack as many of the parts as possible.
        result, placed, fails = packaide.pack(
            [self.bin, self.bin, self.bin],  # A list of sheets (SVG documents)
            self.parts,  # An SVG document containing the parts
            tolerance=2.5,  # Discretization tolerance
            offset=0,  # The offset distance around each shape (dilation)
            partial_solution=True,  # Whether to return a partial solution
            rotations=1,  # The number of rotations of parts to try
            persist=True  # Cache results to speed up next run
        )

        result_object = {
            "result": result[0][1],
            "placed": placed,
            "fails": fails,
            "total": placed + fails,
            "description": "{} parts were placed. {} parts could not fit on the sheets".format(placed, fails),
        }

        print(result_object)
        print("DEBUG: Description" + str(result_object["description"]))

        # If partial_solution was False, then either every part is placed or none
        # are. Otherwise, as many as possible are placed. placed and fails denote
        # the number of parts that could be and could not be placed respectively
        return result_object