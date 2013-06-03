#!/usr/bin/env python
# -*- coding: utf8 -*-

# Render a page of a document to a PNG image.
# Usage: example.py document page_number scale PNG_filename

import sys
import fitz

def render(filename, page_idx, scale, output):
    ctx = fitz.Context(fitz.FZ_STORE_UNLIMITED)

    doc = ctx.open_document(filename)
    page = doc.load_page(page_idx-1)

    trans = fitz.scale_matrix(scale, scale)
    bbox = trans.transform_rect(page.bound_page()).round_rect()

    pix = ctx.new_pixmap_with_irect(fitz.fz_device_rgb, bbox)
    pix.clear_pixmap(255);
    data = pix.get_samples()

    dev = pix.new_draw_device()
    page.run_page(dev, trans, None)
    pix.write_png(output, 0)



if __name__ == '__main__':
    render(sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
