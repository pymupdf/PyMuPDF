import os
import pathlib

import pymupdf

import gentle_compare


def test_5118():
    print()
    out = pathlib.Path(os.path.normpath(f'{__file__}/../../tests/test_5118_out'))
    print(f'{out=}')
    out.mkdir(exist_ok=True)
    
    def svg(body):
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'width="400" height="200" viewBox="0 0 400 200">'
            + body
            + '</svg>'
        )


    gradient = svg('''
      <defs>
        <linearGradient id="bg" x1="0" x2="1">
          <stop offset="0" stop-color="#05f8ff"/>
          <stop offset="1" stop-color="#eefbf6"/>
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="398" height="198"
            fill="url(#bg)" stroke="#cbd6e4"/>
    ''')

    text_attributes = (
        'text-anchor="middle" font-family="Arial, sans-serif" font-size="20"'
    )
    cases = {
        "gradient": gradient,
        "gradient_percent_stops": gradient.replace(
            'offset="0"', 'offset="0%"'
        ).replace('offset="1"', 'offset="100%"'),
        "gradient_percent_coordinates": gradient.replace(
            'x1="0" x2="1"', 'x1="0%" y1="0%" x2="100%" y2="0%"'
        ),
        "gradient_stop_style": gradient.replace(
            'stop-color="#f5f8ff"', 'style="stop-color:#f5f8ff"'
        ).replace('stop-color="#eefbf6"', 'style="stop-color:#eefbf6"'),
        "gradient_user_space": gradient.replace(
            'x1="0" x2="1"',
            'gradientUnits="userSpaceOnUse" x1="1" y1="1" x2="399" y2="1"',
        ),
        "solid_fill_control": gradient.replace('url(#bg)', '#f5f8ff'),
        "text_direct": svg(
            f'<text x="200" y="60" {text_attributes}>middle label</text>'
        ),
        "text_group": svg(
            f'<g {text_attributes}>'
            '<text x="200" y="60">middle label</text></g>'
        ),
        "text_inline": svg(
            '<text x="200" y="60" '
            'style="text-anchor:middle;font-family:Arial, sans-serif;font-size:20">'
            'middle label</text>'
        ),
        "text_anchor_group_only": svg(
            '<g text-anchor="middle">'
            '<text x="200" y="60" font-family="Arial, sans-serif" font-size="20">'
            'middle label</text></g>'
        ),
        "text_family_group_only": svg(
            '<g font-family="Arial, sans-serif">'
            '<text x="200" y="60" text-anchor="middle" font-size="20">'
            'middle label</text></g>'
        ),
        "class_fill": svg(
            '<style>.c { fill: #ff0000; }</style>'
            '<rect class="c" x="50" y="50" width="300" height="100"/>'
        ),
        "element_fill": svg(
            '<style>rect { fill: #ff0000; }</style>'
            '<rect x="50" y="50" width="300" height="100"/>'
        ),
        "inline_fill_control": svg(
            '<rect x="50" y="50" width="300" height="100" style="fill:#ff0000"/>'
        ),
    }
    cases["text_edge_direct"] = cases["text_direct"].replace('x="200"', 'x="320"')
    cases["text_edge_group"] = cases["text_anchor_group_only"].replace(
        'x="200"', 'x="320"'
    )

    png_names = list()
    
    for name, content in cases.items():
        svg_bytes = content.encode("utf-8")
        (out / f"{name}.svg").write_bytes(svg_bytes)
        with pymupdf.open(stream=svg_bytes, filetype="svg") as doc:
            page = doc[0]
            pix = page.get_pixmap(alpha=False)
            png_name = f"{name}.png"
            pix.save(out / png_name)
            png_names.append(png_name)
            print(name, "center RGB", pix.pixel(200, 100))
            for block in page.get_text("dict")["blocks"]:
                if block["type"] != 0:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        print(
                            "  text", repr(span["text"]),
                            "font", span["font"],
                            "size", span["size"],
                            "origin", tuple(round(v, 2) for v in span["origin"]),
                        )
    
    # Check .png files.
    num_errors = 0
    for png_name in png_names:
        expected = os.path.normpath(f'{__file__}/../../tests/resources/test_5118_expected_{png_name}')
        actual = str(out / png_name)
        rms = gentle_compare.pixmaps_rms(expected, actual, verbose=0)
        print(f'{png_name=}: {rms=}')
        if rms > 1:
            num_errors += 1
    
    # Confirm the same problems through Markdown-to-PDF conversion.
    for name in ("gradient", "text_direct", "text_group", "class_fill"):
        markdown_path = out / f"{name}.md"
        markdown_path.write_text(f"![SVG example]({name}.svg)\n", encoding="utf-8")
        with pymupdf.open(
            markdown_path,
            rect=pymupdf.paper_rect("A4"),
            archive=pymupdf.Archive(str(out)),
        ) as doc:
            doc.ez_save(out / f"{name}_from_markdown.pdf")
        
    print(f'{num_errors=}')

    if pymupdf.mupdf_version_tuple >= (1, 29):
        assert not num_errors, f'{num_errors=}'
    else:
        # 2026-10-09.
        # num_errors = 9 with mupdf-1.28.x 393e18b3c66c4 `When adding colorspace do not write Device colorspaces as ICC.`.
        # num_errors = 10 with pymupdf-1.28.2.
        assert num_errors
