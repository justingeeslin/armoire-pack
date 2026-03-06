import sys
import os

sys.path.append('/home/parallels/PycharmProjects/Packaide/python')
packaide_path = os.path.join('/app', 'Packaide', 'python')
if packaide_path not in sys.path:
    sys.path.append(packaide_path)

import packaide

class BinPack:
    def __init__(self):
        self.holes = None

        ## A default bin
        self.bin = """
           <svg width="300" height="300" viewBox="0 0 300 300">
           </svg>
        """

    def pack(self):
        if not isinstance(self.parts, str):
            return {"error": "Please provide at least one part."}

            # Example usage (from your previous cell)
            # Shapes are provided in SVG format

        # shapes = """
        #    <svg viewBox="0 0 432.13 593.04">
        #      <rect width="100" height="50" />
        #      <rect width="50" height="100" />
        #      <ellipse rx="20" ry="20" />
        #    </svg>
        #    """

        # The target sheet / material is also represented as an SVG
        # document. Shapes given on the sheet are interpreted as
        # holes that must be avoided when placing new parts. In this
        # case, a square in the upper-left-hand corner.

        # Adds holes to the bin when needed
        def add_children(svg_string, children):
            # children: list of '<rect ... />' strings
            insert = "\n".join(children)
            return svg_string.replace("</svg>", f"\n{insert}\n</svg>")

        if isinstance(self.holes, str):
            self.bin = add_children(
                self.bin,
                [
                    self.holes
                ]
            )

        print("Parts:")
        print(self.parts)

        print("Bin:")
        print(self.bin)

        # Attempts to pack as many of the parts as possible.
        result, placed, fails = packaide.pack(
            [self.bin],  # A list of sheets (SVG documents)
            self.parts,  # An SVG document containing the parts
            tolerance=2.5,  # Discretization tolerance
            offset=5,  # The offset distance around each shape (dilation)
            partial_solution=True,  # Whether to return a partial solution
            rotations=1,  # The number of rotations of parts to try
            persist=True  # Cache results to speed up next run
        )

        # If partial_solution was False, then either every part is placed or none
        # are. Otherwise, as many as possible are placed. placed and fails denote
        # the number of parts that could be and could not be placed respectively
        return {
            "result": result,
            "placed": placed,
            "fails": fails,
            "description": "{} parts were placed. {} parts could not fit on the sheets".format(placed, fails),
        }