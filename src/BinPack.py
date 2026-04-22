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
from copy import deepcopy

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

def strip_namespace(elem):
    """Remove namespace from all tags in-place."""
    for el in elem.iter():
        if "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return elem

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
        self.parts = None

        ## Stock (the original bin to be packed with garment pieces)
        """
                   <svg width="300" height="300" viewBox="0 0 300 300">
                   </svg>
                """
        self.stock = []

        ## For debug purposes
        self.garment_shaped_hole_tesselation = None

        ## Bin (changes throughout the various packing operations)
        self.bin = self.stock

    def _detect_irregular_stock(self):
        # Assume its all irregular for now.
        return True



    def _extract_shapes_as_svgs(self, svg_string):
        print(f" DEBUG Extracting shapes as svgs {svg_string}")
        root = ET.fromstring(svg_string)

        # Handle namespace
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        def parse_points(points_str):
            pts = []
            for pair in points_str.strip().split():
                x, y = pair.split(",")
                pts.append((float(x), float(y)))
            return pts

        def get_bbox(elem):
            tag = elem.tag.replace(ns, "")

            if tag == "rect":
                x = float(elem.get("x", 0))
                y = float(elem.get("y", 0))
                w = float(elem.get("width", 0))
                h = float(elem.get("height", 0))
                return x, y, x + w, y + h

            elif tag == "circle":
                cx = float(elem.get("cx", 0))
                cy = float(elem.get("cy", 0))
                r = float(elem.get("r", 0))
                return cx - r, cy - r, cx + r, cy + r

            elif tag == "ellipse":
                cx = float(elem.get("cx", 0))
                cy = float(elem.get("cy", 0))
                rx = float(elem.get("rx", 0))
                ry = float(elem.get("ry", 0))
                return cx - rx, cy - ry, cx + rx, cy + ry

            elif tag == "line":
                x1 = float(elem.get("x1", 0))
                y1 = float(elem.get("y1", 0))
                x2 = float(elem.get("x2", 0))
                y2 = float(elem.get("y2", 0))
                return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)

            elif tag in ("polygon", "polyline"):
                pts = parse_points(elem.get("points", ""))
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                return min(xs), min(ys), max(xs), max(ys)

            elif tag == "path":
                # Simple path bbox (handles M/L/H/V only)
                import re
                nums = list(map(float, re.findall(r"[-+]?\d*\.?\d+", elem.get("d", ""))))
                xs = nums[0::2]
                ys = nums[1::2]
                return min(xs), min(ys), max(xs), max(ys)

            else:
                return None

        shape_tags = [
            f"{ns}path",
            f"{ns}rect",
            f"{ns}circle",
            f"{ns}ellipse",
            f"{ns}line",
            f"{ns}polyline",
            f"{ns}polygon",
        ]

        shapes = [e for e in root.iter() if e.tag in shape_tags]

        svg_outputs = []

        for shape in shapes:
            bbox = get_bbox(shape)
            if bbox is None:
                continue

            min_x, min_y, max_x, max_y = bbox
            width = max_x - min_x
            height = max_y - min_y

            # Create new SVG
            new_svg = ET.Element("svg", xmlns="http://www.w3.org/2000/svg")
            new_svg.set("viewBox", f"0 0 {width} {height}")
            new_svg.set("width", str(width))
            new_svg.set("height", str(height))

            # Clone shape and translate to origin
            shape_clone = deepcopy(shape)

            existing_transform = shape_clone.get("transform", "")
            translate = f"translate({-min_x},{-min_y})"


            if "transform" in shape_clone.attrib:
                ## The transformation becomes a data-attribute for purposes of packing. The polygon will be invisible to the pack if it is transformed outside of its new view box, etc.
                shape_clone.set("data-transform", f"{translate} {existing_transform}".strip())
                del shape_clone.attrib["transform"]

            # Remove namespaces from the cloned shape
            strip_namespace(shape_clone)

            new_svg.append(shape_clone)

            svg_outputs.append(ET.tostring(new_svg, encoding="unicode"))

        return svg_outputs

    def make_irregular_stock_then_pack(self):
        # An array of garment-shaped hole tesslations
        garment_tesselations = []
        # Get the various "bins" from the stock.
        self.bin = self._extract_shapes_as_svgs(self.bin)

        print(f"DEBUG: New Array Bins: {self.bin}")

        for bin in self.bin:
            # Doesn't return just sets a new self.bin
            bin_tesslation = self._make_irregular_stock_with_packed_holes(bin)
            garment_tesselations.append(bin_tesslation)

        # Replace the SVG stock with these garment-shaped hole tesselations
        self.garment_shaped_hole_tesselation = garment_tesselations
        self.bin = garment_tesselations

        print(f"DEBUG: New Array Bin (post-tesselation): {self.bin}")

        return self.pack()

    def _get_bin_svg_size(self, bin):
        root = ET.fromstring(bin)

        width = float(root.get("width").replace("px", "").strip())
        height = float(root.get("height").replace("px", "").strip())

        return width, height

    def _make_irregular_stock_with_packed_holes(self, bin):
        discritization_tolerence_holes = 2.5
        width, height = self._get_bin_svg_size(bin)

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

        print("DEBUG numberOfHoles: ", numberOfHoles)
        for i in range(numberOfHoles):
            holes = holes + f'<circle r="{holeWidth / 2}" />'

        holes = holes + "</svg>"

        print(f"DEBUG: Creating a hole tesselation around: {bin}")

        # print(f"DEBUG: Holes SVG: {holes}")

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
        print(f"DEBUG: result: {result}")
        print(f"DEBUG: placed: {placed}")
        print(f"DEBUG: fails: {fails}")

        packed_result = result[0][1]
        # Re-instate the transforms
        packed_placed = restore_data_attributes(packed_result)

        # The result is the new bin with packed shapes interpreted as "holes" by packaide during self.pack()
        return packed_placed

    def pack(self):
        if not isinstance(self.parts, str):
            return {"error": "Please provide at least one part."}


        # Attempts to pack as many of the parts as possible.
        result, placed, fails = packaide.pack(
            self.bin,  # A list (array) of sheets (SVG documents)
            self.parts,  # An SVG document containing the parts
            tolerance=2.5,  # Discretization tolerance
            offset=0,  # The offset distance around each shape (dilation)
            partial_solution=True,  # Whether to return a partial solution
            rotations=1,  # The number of rotations of parts to try
            persist=True  # Cache results to speed up next run
        )

        print(f"DEBUG: result: {result}")

        result_object = {
            "stock": self.stock,
            "parts": self.parts,
            "bin": self.bin,
            "garment_shaped_hole_tesselation": self.garment_shaped_hole_tesselation,
            "result": result,
            # Packed pieces plus the stock
            # "garment_marker": combine_stock_garment_svg_strings(self.stock, result[0][1]),
            "placed": placed,
            "fails": fails,
            "total": placed + fails,
            "description": "{} parts were placed. {} parts could not fit on the sheets".format(placed, fails),
        }

        # If partial_solution was False, then either every part is placed or none
        # are. Otherwise, as many as possible are placed. placed and fails denote
        # the number of parts that could be and could not be placed respectively
        return result_object