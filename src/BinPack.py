import sys
import os
import math
import xml.etree.ElementTree as ET

sys.path.append('/home/parallels/PycharmProjects/Packaide/python')
packaide_path = os.path.join('/app', 'Packaide', 'python')
if packaide_path not in sys.path:
    sys.path.append(packaide_path)

import packaide

import copy
import xml.etree.ElementTree as ET

standard_width = 1000
standard_height = 800

def combine_stock_garment_svg_strings(stock_svg: str, garment_pieces_svg: str) -> str:
    """
    Combine two SVG strings into a single SVG by placing their child elements
    under one new root SVG.

    This version overlays them in the same coordinate system.
    """

    root_stock_svg = ET.fromstring(stock_svg)
    root_garment_pieces_svg = ET.fromstring(garment_pieces_svg)

    # SVG namespace
    svg_ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", svg_ns)

    def strip_tag(tag: str) -> str:
        return tag.split("}", 1)[-1] if "}" in tag else tag

    if strip_tag(root_stock_svg.tag) != "svg" or strip_tag(root_garment_pieces_svg.tag) != "svg":
        raise ValueError("Both inputs must have an <svg> root element.")

    # Prefer viewBox from first SVG, then second, otherwise fallback
    width = root_stock_svg.get("width") or root_garment_pieces_svg.get("width") or standard_width
    height = root_stock_svg.get("height") or root_garment_pieces_svg.get("height") or standard_height
    viewbox = root_stock_svg.get("viewBox") or root_garment_pieces_svg.get("viewBox") or "0 0 {width} {height}"

    combined_root = ET.Element(
        f"{{{svg_ns}}}svg",
        {
            "viewBox": viewbox,
            "width": width,
            "height": height,
        },
    )

    # Copy children from both SVGs into the new root
    for child in list(root_stock_svg):
        new_child = copy.deepcopy(child)
        new_child.set("role", "stock")
        combined_root.append(new_child)

    for child in list(root_garment_pieces_svg):
        new_child = copy.deepcopy(child)
        new_child.set("role", "garment")
        combined_root.append(new_child)

    return ET.tostring(combined_root, encoding="unicode")

class BinPack:
    def __init__(self):
        self.parts = None

        ## Stock (the original bin to be packed with garment pieces)
        self.stock = """
           <svg width="300" height="300" viewBox="0 0 300 300">
           </svg>
        """

        ## Bin (changes throughout the various packing operations)
        self.bin = self.stock

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
        width, height = self._get_bin_svg_size()

        holes = f"""
            <svg xmlns="http://www.w3.org/2000/svg"
                 width="{width}px" height="{height}px"
                 viewBox="0.00 0.00 {width} {height}">"""

        # holes should be roughtly this percentage of the SVG
        # how many holes will fit across the image
        holes_across = 32
        hole_scale = 1/holes_across

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
            "parts": self.parts,
            "stock": self.stock,
            "bin": self.bin,
            "result": result[0][1],
            # Packed pieces plus the stock
            "garment_marker": combine_stock_garment_svg_strings(self.stock, result[0][1]),
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