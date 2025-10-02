"""
Determine reading order of layout boxes on a document page.

Layout boxes are defined as classified bounding boxes, with class info as
provided by pymupdf_layout. Each box is a tuple (x0, y0, x1, y1, "class").

The main function is "find_reading_order()".
"""


def cluster_stripes(boxes, vertical_gap: float = 12):
    """
    Divide page into horizontal stripes based on vertical gaps.

    Args:
        boxes (list): List of bounding boxes, each defined as (x0, y0, x1, y1).
        vertical_gap (float): Minimum vertical gap to separate stripes.

    Returns:
        List of disjoint horizontal stripes. Each stripe is a list of boxes.
    """
    # Sort top to bottom
    sorted_boxes = sorted(boxes, key=lambda b: b[1])
    stripes = []
    current_stripe = [sorted_boxes[0]]

    for box in sorted_boxes[1:]:
        prev_bottom = max(b[3] for b in current_stripe)
        if box[1] - prev_bottom > vertical_gap:
            stripes.append(current_stripe)
            current_stripe = [box]
        else:
            current_stripe.append(box)

    stripes.append(current_stripe)
    return stripes


def cluster_columns_in_stripe(stripe: list):
    """
    Within a stripe, group boxes into columns based on horizontal proximity.

    Args:
        stripe (list): List of boxes within a stripe.

    Returns:
        list: List of columns, each column is a list of boxes.
    """
    # Sort left to right
    sorted_boxes = sorted(stripe, key=lambda b: b[0])
    columns = []
    current_column = [sorted_boxes[0]]

    for box in sorted_boxes[1:]:
        prev_right = max([b[2] for b in current_column])
        if box[0] - prev_right >= -1:
            columns.append(sorted(current_column, key=lambda b: b[1]))
            current_column = [box]
        else:
            current_column.append(box)

    columns.append(sorted(current_column, key=lambda b: b[1]))
    return columns


def compute_reading_order(boxes, vertical_gap: float = 12):
    """
    Compute reading order of boxes delivered by PyMuPDF-Layout.

    Args:
        boxes (list): List of bounding boxes.
        vertical_gap (float): Minimum vertical gap to separate stripes.

    Returns:
        list: List of boxes in reading order.
    """
    stripes = cluster_stripes(boxes, vertical_gap=vertical_gap)
    ordered = []
    for stripe in stripes:
        columns = cluster_columns_in_stripe(stripe)
        for col in columns:
            ordered.extend(col)
    return ordered


def find_reading_order(boxes, vertical_gap: float = 12) -> list:
    """Given page layout information, return the boxes in reading order.

    Args:
        boxes: List of classified bounding boxes with class info as defined
               by pymupdf_layout: (x0, y0, x1, y1, "class").
        vertical_gap: Minimum vertical gap to separate stripes. The default
                      value of 12 works well for most documents.

    Returns:
        List of boxes in reading order.
    """

    def is_contained(inner, outer) -> bool:
        """Check if inner box is fully contained within outer box."""
        return (
            1
            and outer[0] <= inner[0]
            and outer[1] <= inner[1]
            and outer[2] >= inner[2]
            and outer[3] >= inner[3]
            and inner != outer
        )

    def filter_contained(boxes) -> list:
        """Remove boxes that are fully contained within another box."""
        # Sort boxes by descending area
        sorted_boxes = sorted(
            boxes, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]), reverse=True
        )
        result = []
        for r in sorted_boxes:
            if not any(is_contained(r, other) for other in result):
                result.append(r)
        return result

    """
    We expect being passed raw 'layout_information' as provided by
    pymupdf_layout. We separate page headers, footers, footnotes from the
    body, bring body boxes into reading order and concatenate the final list.
    """
    filtered = filter_contained(boxes)  # remove nested boxes first
    page_headers = []  # for page headers
    page_footers = []  # for page footers
    footnotes = []  # for footnotes
    body_boxes = []  # for main body boxes

    # separate boxes by type
    for box in filtered:
        x0, y0, x1, y1, bclass = box
        if bclass == "page-header":
            page_headers.append(box)
        elif bclass == "page-footer":
            page_footers.append(box)
        elif bclass == "footnote":
            footnotes.append(box)
        else:
            body_boxes.append(box)

    # bring body into reading order
    ordered = compute_reading_order(body_boxes, vertical_gap=vertical_gap)

    # Final full boxes list. We do simple sorts for non-body boxes.
    final = (
        sorted(page_headers, key=lambda r: (r[1], r[0]))
        + ordered
        + sorted(footnotes, key=lambda r: (r[1], r[0]))
        + sorted(page_footers, key=lambda r: (r[1], r[0]))
    )
    return final
