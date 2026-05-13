import sys
import os
import math
import xml.etree.ElementTree as ET
import SVGTool
sys.path.append('/home/parallels/PycharmProjects/Packaide/python')
packaide_path = os.path.join('/app', 'Packaide', 'python')
if packaide_path not in sys.path:
    sys.path.append(packaide_path)

try:
    import packaide
except ModuleNotFoundError:
    shouldUsePackaideMock = True
    print('Packaide not found, using packaide mock')

import copy
from copy import deepcopy

standard_width = 1000
standard_height = 800

import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"

def strip_namespaces(elem):
    for el in elem.iter():
        if "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return elem


def restore_data_attributes(svg_string, merge_transforms=True, remove_namespaces=True):
    """
    Restore data-* attributes back to normal SVG attributes.

    Parameters
    ----------
    svg_string : str
        The SVG as a string.
    merge_transforms : bool
        If True, restored transform is prepended to any existing transform.
    remove_namespaces : bool
        If True, removes namespace prefixes like ns0: from tags.

    Returns
    -------
    str
        The updated SVG string.
    """
    root = ET.fromstring(svg_string)

    for elem in root.iter():
        attribs = list(elem.attrib.items())

        for key, value in attribs:
            if not key.startswith("data-"):
                continue

            if key.startswith("data-original-"):
                real_attr = key[len("data-original-"):]
            else:
                real_attr = key[len("data-"):]

            if real_attr == "transform":
                if merge_transforms and "transform" in elem.attrib:
                    elem.set("transform", f"{value} {elem.attrib['transform']}".strip())
                else:
                    elem.set("transform", value)
            else:
                elem.set(real_attr, value)

            del elem.attrib[key]

    if remove_namespaces:
        strip_namespaces(root)
        root.set("xmlns", SVG_NS)
    else:
        ET.register_namespace("", SVG_NS)

    return ET.tostring(root, encoding="unicode")

class BinPack:
    def __init__(self):
        # Garment stock
        self.stock = None

        self.default_bin = """<svg width="3000" height="3000" viewBox="0 0 3000 3000"></svg>"""

        self.parts = None


        self.willExtractBinsAndPackSeperately = False

        ## For debug purposes
        self.garment_shaped_hole_tesselation = None

    def _detect_irregular_stock(self):
        # Assume its all irregular for now.
        return True

    def make_irregular_stock(self, bin, parts):
        if not isinstance(bin, str) or len(bin) == 0:
            raise TypeError(f"The make irregular stock process needs a bin. Bin: {bin} {type(bin)}")

        # An array of garment-shaped hole tesslations
        irregular_stock_bins = []
        # Get the various "bins" from the stock.
        extracted_bins = SVGTool.SVGTool.extract(bin)

        # print(f"DEBUG: New Array Bins: {extracted_bins}")

        for extracted_bin in extracted_bins:
            irregular_stock_bin = self._make_irregular_stock_with_packed_holes(extracted_bin)
            irregular_stock_bins.append(irregular_stock_bin)

        # Replace the SVG stock with these garment-shaped hole tesselations
        self.garment_shaped_hole_tesselation = irregular_stock_bins

        # print(f"DEBUG: New Array Bin (post-tesselation): {irregular_stock_bins}")

        return irregular_stock_bins, parts

    def _make_irregular_stock_with_packed_holes(self, bin):
        discritization_tolerence_holes = 2.5
        width, height = SVGTool.SVGTool.get_size(bin)

        holes = f"""
            <svg xmlns="http://www.w3.org/2000/svg"
                 width="{width}px" height="{height}px"
                 viewBox="0.00 0.00 {width} {height}">"""

        # holes should be roughtly this percentage of the SVG
        # how many holes will fit across the image
        holes_across = 32
        hole_scale = 1/holes_across

        holeWidth = width * hole_scale

        # Ensure the hole size is not smaller than the discritization tolerance
        holeWidth = max(math.ceil(discritization_tolerence_holes), int(holeWidth))

        # how many holes will fit vertically?
        holes_down = height / holeWidth

        # Total number of holes to fill the image should be a *max* of down x across
        numberOfHoles = holes_across * holes_down
        # Assume only 20% of the image will be empty.
        numberOfHoles = int(math.ceil(numberOfHoles * 0.2))

        # print("DEBUG numberOfHoles: ", numberOfHoles)
        for i in range(numberOfHoles):
            holes = holes + f'<circle r="{holeWidth / 2}" />'

        holes = holes + "</svg>"

        # print(f"DEBUG: Creating a hole tesselation around: {bin}")

        # print(f"DEBUG: Holes SVG: {holes}")

        if shouldUsePackaideMock:
            return None

        # Pack holds around the bin
        result, placed, fails = packaide.pack(
            [bin],
            holes,
            tolerance=discritization_tolerence_holes,  # Discretization tolerance
            # Would dialating the holes give you more of an edge buffer?
            offset=0,  # The offset distance around each shape (dilation)
            partial_solution=True,  # Whether to return a partial solution
            rotations=1,  # The number of rotations of parts to try
            persist=False  # Cache results to speed up next run
        )
        # print(f"DEBUG: result: {result}")
        # print(f"DEBUG: placed: {placed}")
        # print(f"DEBUG: fails: {fails}")

        packed_result = result[0][1]
        # Re-instate the transforms
        packed_placed = restore_data_attributes(packed_result)

        # The result is the new bin with packed shapes interpreted as "holes" by packaide during self.pack()
        return packed_placed

    def pack(self, bins = None, parts = None):

        if not isinstance(parts, str):
            return {"error": f"Please provide at least one part. {parts} {isinstance(parts, str)}"}

        if bins is None or len(bins) == 0:
            bins = [self.default_bin]

        # Attempts to pack as many of the parts as possible.

        # print(f"DEBUG: Bin: {bins}")

        if shouldUsePackaideMock:
            placed = 8
            fails = 8
            result = self.mock_result
        else:
            result, placed, fails = packaide.pack(
                bins,  # A list (array) of sheets (SVG documents)
                parts,  # An SVG document containing the parts
                tolerance=2.5,  # Discretization tolerance
                offset=0,  # The offset distance around each shape (dilation)
                partial_solution=True,  # Whether to return a partial solution
                rotations=1,  # The number of rotations of parts to try
                persist=True  # Cache results to speed up next run
            )

        parts_packed = [svg for _, svg in result]

        ## Apply important attributes "role" & data-draggable
        parts_packed = [SVGTool.SVGTool.apply_attribute_to_shapes(elem, "data-draggable", "true") for elem in parts_packed]
        parts_packed = [SVGTool.SVGTool.apply_attribute_to_shapes(elem, "role", "garment") for elem in
                        parts_packed]

        result_object = {
            ## Input
            "parts": parts,
            ## DEBUG : Tesselation
            "bin_local": bins,
            "parts_local": parts,
            "parts_packed": parts_packed,
            ## Output
            "result": result,
            "placed": placed,
            "fails": fails,
            "total": placed + fails,
            "description": "{} parts were placed. {} parts could not fit on the sheets".format(placed, fails),
        }

        # iff stock is supplied..
        if self.stock is not None:
            result_object["stock"] = self.stock
            # Supply a garment marker - Packed pieces plus the stock
            result_object["garment_marker"] = SVGTool.SVGTool.combine(parts_packed + [self.stock])

        # If partial_solution was False, then either every part is placed or none
        # are. Otherwise, as many as possible are placed. placed and fails denote
        # the number of parts that could be and could not be placed respectively
        return result_object