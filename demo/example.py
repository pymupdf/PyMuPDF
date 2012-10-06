#!/usr/bin/env python
# -*- coding: utf8 -*-

# Render a page of a document to a PNG image.
# Usage: example.py document page_number scale PNG_filename

import sys
from fitz import *

def render(filename, page_idx, scale, output):
    ctx = new_context(FZ_STORE_UNLIMITED)

    doc = open_document(ctx, filename)
    page = doc.load_page(page_idx-1)

    trans = scale_matrix(scale, scale)
    bbox = trans.transform_rect(page.bound_page()).round_rect()

    pix = new_pixmap_with_bbox(ctx, fz_device_rgb, bbox)
    pix.clear_pixmap(255);

    dev = new_draw_device(pix)
    page.run_page(dev, trans, None)
    pix.write_png(output, 0)


if __name__ == '__main__':
    render(sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
