import xml.etree.ElementTree as ET
from typing import List, Tuple
import copy

class SVGTool:

    @staticmethod
    def _strip_namespace(elem: ET.Element) -> ET.Element:
        """Remove namespace from all tags and attributes in-place."""
        for el in elem.iter():
            if isinstance(el.tag, str) and "}" in el.tag:
                el.tag = el.tag.split("}", 1)[1]

            new_attrib = {}
            for key, value in el.attrib.items():
                clean_key = key.split("}", 1)[-1] if "}" in key else key
                new_attrib[clean_key] = value
            el.attrib.clear()
            el.attrib.update(new_attrib)

        return elem

    @staticmethod
    def extract(svg_string):
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
            shape_clone = copy.deepcopy(shape)

            existing_transform = shape_clone.get("transform", "")
            translate = f"translate({-min_x},{-min_y})"


            if "transform" in shape_clone.attrib:
                ## The transformation becomes a data-attribute for purposes of packing. The polygon will be invisible to the pack if it is transformed outside of its new view box, etc.
                shape_clone.set("data-transform", f"{translate} {existing_transform}".strip())
                del shape_clone.attrib["transform"]

            # Remove namespaces from the cloned shape
            SVGTool._strip_namespace(shape_clone)

            new_svg.append(shape_clone)

            svg_outputs.append(ET.tostring(new_svg, encoding="unicode"))

        return svg_outputs

    @staticmethod
    def combine(svg_strings: List[str]) -> str:
        """
        Combine multiple SVG strings into a single SVG.

        - Preserves existing attributes (including data-*)
        - Preserves existing `role` attributes
        - Removes all namespaces from output
        """

        if not svg_strings:
            raise ValueError("Must provide at least one SVG string.")

        parsed_roots = []

        for svg in svg_strings:
            if not isinstance(svg, str):
                raise ValueError(f"Tried to combine, but Not a SVG string {type(svg)} {svg}")

            root = ET.fromstring(svg)
            SVGTool._strip_namespace(root)

            if root.tag != "svg":
                raise ValueError("All inputs must have an <svg> root.")

            parsed_roots.append(root)

        # Infer dimensions from first available SVG
        width = next((r.get("width") for r in parsed_roots if r.get("width")), "100%")
        height = next((r.get("height") for r in parsed_roots if r.get("height")), "100%")
        viewbox = next(
            (r.get("viewBox") for r in parsed_roots if r.get("viewBox")),
            f"0 0 {width} {height}",
        )

        combined_root = ET.Element(
            "svg",
            {
                "width": width,
                "height": height,
                "viewBox": viewbox,
            },
        )

        for i, root in enumerate(parsed_roots):

            for child in list(root):
                new_child = copy.deepcopy(child)
                SVGTool._strip_namespace(new_child)

                combined_root.append(new_child)

        SVGTool._strip_namespace(combined_root)

        return ET.tostring(combined_root, encoding="unicode")


    @staticmethod
    def apply_attribute_to_shapes(svg_string: str, attribute: str, property: str) -> str:
        """
        Applies an attribute to all the elements in an SVG string.

        Parameters
        ----------
        svg_string : str
            The SVG as a string.

        Returns
        -------
        str
            The updated SVG string.
        """
        root = ET.fromstring(svg_string)

        for elem in root:
            elem.set(attribute, property)

        return ET.tostring(root, encoding="unicode")

    @staticmethod
    def get_size(svg_string: str) -> Tuple[float, float]:
        root = ET.fromstring(svg_string)

        width = float(root.get("width").replace("px", "").strip())
        height = float(root.get("height").replace("px", "").strip())

        return width, height