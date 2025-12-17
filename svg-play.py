def outside_region_svg(svg, width, height, fill="#000", opacity=1.0):
    # Outer rectangle path for the full canvas
    outer_rect = f"M 0,0 H {width} V {height} H 0 Z"
    inner_hole = svg

    d = f"{outer_rect} {inner_hole}"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <path d="{d}" fill="{fill}" fill-opacity="{opacity}" fill-rule="evenodd"/>
</svg>"""
    return svg

tshirtbin = '''
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="1350px" height="1428px"
     viewBox="0.00 0.00 1350.00 1428.00">
  <polygon id="full" points="256.00,101.00 14.00,445.00 0.00,499.00 246.00,674.00 305.00,627.00 298.00,1428.00 1028.00,1421.00 1033.00,623.00 1093.00,652.00 1350.00,513.00 1120.00,119.00 932.00,29.00 824.00,0.00 759.00,34.00 646.00,45.00 535.00,0.00" fill="none" stroke="#0091EA" stroke-width="3"/>
</svg>
'''

