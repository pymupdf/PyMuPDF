"""
TableGridExtractorV4.py

Loads exported GridModelV4 and ConnClassifier ONNX models and predicts
table grid structure (line positions + cell connectivity) from a cropped
table image.

Post-processing pipeline
------------------------
1. Resize input image to GridModelV4 input size.
2. Run GridModelV4 ONNX inference.
   Outputs: h_on_logit, h_offset, v_on_logit, v_offset, feature_map
3. Decode anchor outputs -> normalized line positions using 1D NMS.
   score = sigmoid(on_logit); line_pos = anchor + offset * anchor_step
4. Convert normalized line positions to input image pixel coordinates.
5. Optionally filter empty lines and snap to bbox gaps.
6. Run ConnClassifier ONNX inference on cell features.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import numpy as np
import onnxruntime as ort

import pymupdf

# ---------------------------------------------------------------------------
# Inline GridPrediction / CellInfo (standalone mode)
# ---------------------------------------------------------------------------


@dataclass
class GridPrediction:  # type: ignore[no-redef]
    h_lines: list
    v_lines: list
    h_heatmap: object = None
    v_heatmap: object = None
    h_confidences: object = None
    v_confidences: object = None
    db_prob_map: object = None
    h_on_prob: object = None
    v_on_prob: object = None
    h_lines_norm: object = None
    v_lines_norm: object = None
    h_cls: object = None
    connectivity: object = None


@dataclass
class CellInfo:  # type: ignore[no-redef]
    bbox_idx: int
    row_start: int
    row_end: int
    col_start: int
    col_end: int
    row: int = 0
    col: int = 0
    text: str = ""

    @property
    def row_span(self) -> int:
        return self.row_end - self.row_start

    @property
    def col_span(self) -> int:
        return self.col_end - self.col_start


# ---------------------------------------------------------------------------
# Anchor decode helper
# ---------------------------------------------------------------------------


def _decode_anchors(
    on_logits: np.ndarray,
    offsets: np.ndarray,
    threshold: float,
    nms_min_dist: float = 0.0,
) -> tuple:
    """
    Decode anchor-based line predictions to normalized positions.

    offset is anchor_step-normalized: anchor + offset * anchor_step to decode.
    score = sigmoid(on_logit).
    """
    max_n = len(on_logits)
    on_prob = (1.0 / (1.0 + np.exp(-on_logits.astype(np.float64)))).astype(np.float32)
    anchors = np.linspace(0.0, 1.0, max_n, dtype=np.float32)
    mask = on_prob >= threshold

    anchor_step = 1.0 / (max_n - 1) if max_n > 1 else 1.0
    candidates = (anchors + offsets * anchor_step)[mask]
    scores = on_prob[mask]

    if nms_min_dist > 0.0 and len(candidates) > 0:
        order = np.argsort(-scores)
        suppressed = np.zeros(len(candidates), dtype=bool)
        keep = []
        for i in order:
            if suppressed[i]:
                continue
            keep.append(i)
            for j in range(len(candidates)):
                if not suppressed[j] and j != i:
                    if abs(float(candidates[j]) - float(candidates[i])) < nms_min_dist:
                        suppressed[j] = True
        positions = np.sort(candidates[np.array(keep, dtype=np.int32)])
    else:
        positions = np.sort(candidates)

    return positions, on_prob, mask


# ---------------------------------------------------------------------------
# Cell feature extractor
# ---------------------------------------------------------------------------


def _extract_cell_features(
    feature_map: np.ndarray,
    h_lines_norm: np.ndarray,
    v_lines_norm: np.ndarray,
) -> np.ndarray:
    """Pool feature_map regions defined by detected line positions."""
    C, H, W = feature_map.shape
    N = len(h_lines_norm)
    M = len(v_lines_norm)

    if N < 2 or M < 2:
        return np.zeros((max(N - 1, 1), max(M - 1, 1), C), dtype=np.float32)

    ys = np.clip((h_lines_norm * H).astype(np.int32), 0, H)
    xs = np.clip((v_lines_norm * W).astype(np.int32), 0, W)

    cell_feat = np.zeros((N - 1, M - 1, C), dtype=np.float32)
    for i in range(N - 1):
        y1 = ys[i]
        y2 = max(y1 + 1, ys[i + 1])
        y2 = min(y2, H)
        if y1 >= H:
            continue
        for j in range(M - 1):
            x1 = xs[j]
            x2 = max(x1 + 1, xs[j + 1])
            x2 = min(x2, W)
            if x1 >= W:
                continue
            region = feature_map[:, y1:y2, x1:x2]
            if region.size == 0:
                continue
            cell_feat[i, j] = region.mean(axis=(1, 2))

    return cell_feat


# ---------------------------------------------------------------------------
# Main extractor class
# ---------------------------------------------------------------------------


class TableGridExtractorV4:
    """ONNX-based table grid extractor using the V4 anchor-Transformer model."""

    def __init__(
        self,
        grid_onnx_path,
        conn_onnx_path=None,
        h_on_threshold: float = 0.25,
        v_on_threshold: float = 0.2,
        conn_threshold: float = 0.2,
        nms_min_dist: float = 0.02,
        filter_empty_lines: bool = True,
        snap_to_bbox_gaps: bool = False,
        header_type: str = "1-Row",
        merge_type: str = "BBox",
        providers: Optional[list] = None,
    ) -> None:
        if providers is None:
            providers = ["CPUExecutionProvider"]

        self.grid_onnx_path = Path(grid_onnx_path)
        self.conn_onnx_path = Path(conn_onnx_path) if conn_onnx_path else None
        self.h_on_threshold = h_on_threshold
        self.v_on_threshold = v_on_threshold
        self.conn_threshold = conn_threshold
        self.nms_min_dist = nms_min_dist
        self.filter_empty_lines = filter_empty_lines
        self.snap_to_bbox_gaps = snap_to_bbox_gaps
        self.header_type = header_type
        self.merge_type = merge_type

        self._grid_sess = ort.InferenceSession(
            str(self.grid_onnx_path), providers=providers
        )
        self._conn_sess = (
            ort.InferenceSession(str(self.conn_onnx_path), providers=providers)
            if self.conn_onnx_path and self.conn_onnx_path.exists()
            else None
        )

        inp = self._grid_sess.get_inputs()[0]
        self._input_h = int(inp.shape[2])
        self._input_w = int(inp.shape[3])

        dummy = np.zeros((1, 3, self._input_h, self._input_w), dtype=np.float32)
        outputs = self._grid_sess.run(None, {"image": dummy})
        self._max_h = int(outputs[0].shape[1])
        self._max_v = int(outputs[2].shape[1])

    # ------------------------------------------------------------------
    # Post-processing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _filter_empty_lines(
        lines: list,
        centers: list,
        image_size: float,
    ) -> list:
        """
        Merge adjacent line pairs that have no bbox center between them.
        CCL-style convergence. Leading/trailing empty gaps are removed.
        """
        if not lines:
            return lines

        current = sorted(lines)
        changed = True

        while changed:
            changed = False
            if len(current) < 2:
                break
            result = [current[0]]
            for i in range(1, len(current)):
                lo_y, lo_score, lo_cls = result[-1]
                hi_y, hi_score, hi_cls = current[i]
                has_center = any(lo_y <= c <= hi_y for c in centers)
                if not has_center:
                    if hi_score >= lo_score:
                        result[-1] = (hi_y, hi_score, hi_cls)
                    changed = True
                else:
                    result.append(current[i])
            current = result

        return current

    @staticmethod
    def _snap_lines_to_bbox_gaps(
        h_lines: list,
        bboxes_crop: np.ndarray,
        snap_threshold: float = 0.0,
    ) -> list:
        """Snap h_lines crossing a bbox to nearest inter-row gap center."""
        if len(bboxes_crop) == 0 or len(h_lines) == 0:
            return h_lines

        bottoms = np.sort(bboxes_crop[:, 3])
        tops = np.sort(bboxes_crop[:, 1])

        gap_lines = []
        for bot in bottoms:
            candidates = tops[tops > bot]
            if len(candidates) > 0:
                gap_lines.append((bot + float(candidates[0])) / 2.0)

        if not gap_lines:
            return h_lines

        gap_arr = np.array(
            sorted(set(round(g, 4) for g in gap_lines)), dtype=np.float32
        )
        used_gaps: set = set()
        result = []
        for y in h_lines:
            crosses = np.any((bboxes_crop[:, 1] < y) & (y < bboxes_crop[:, 3]))
            if crosses:
                dists = np.abs(gap_arr - y)
                order = np.argsort(dists)
                snapped = False
                for idx in order:
                    nearest = float(gap_arr[idx])
                    dist = float(dists[idx])
                    if nearest in used_gaps:
                        continue
                    if snap_threshold <= 0.0 or dist <= snap_threshold:
                        result.append(nearest)
                        used_gaps.add(nearest)
                        snapped = True
                        break
                if not snapped:
                    result.append(y)
            else:
                result.append(y)
        return result

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict_grid(self, pixmap) -> GridPrediction:
        orig_h, orig_w = pixmap.h, pixmap.w
        pix_resized = pymupdf.Pixmap(pixmap, self._input_w, self._input_h)
        if pix_resized.alpha:  # If alpha channel was created,
            pix_resized = pymupdf.Pixmap(pix_resized, 0)  # remove it
        img_rgb = np.frombuffer(pix_resized.samples, dtype=np.uint8).reshape(
            pix_resized.height, pix_resized.width, pix_resized.n
        )
        img = img_rgb.astype(np.float32) / 255.0
        inp = img.transpose(2, 0, 1)[np.newaxis]

        outputs = self._grid_sess.run(None, {"image": inp})
        h_on_logit = outputs[0][0]  # (max_h,)
        h_offset = outputs[1][0]  # (max_h,)
        v_on_logit = outputs[2][0]  # (max_v,)
        v_offset = outputs[3][0]  # (max_v,)
        feature_map = outputs[4][0]  # (C, H', W')

        h_lines_norm, h_on_prob, h_mask = _decode_anchors(
            h_on_logit, h_offset, self.h_on_threshold, self.nms_min_dist
        )
        v_lines_norm, v_on_prob, _ = _decode_anchors(
            v_on_logit, v_offset, self.v_on_threshold, self.nms_min_dist
        )

        h_cls = np.ones(len(h_lines_norm), dtype=np.int32)
        h_lines = [float(y) * orig_h for y in h_lines_norm]
        v_lines = [float(x) * orig_w for x in v_lines_norm]

        connectivity = None
        if (
            self._conn_sess is not None
            and len(h_lines_norm) >= 2
            and len(v_lines_norm) >= 2
        ):
            cell_feat = _extract_cell_features(feature_map, h_lines_norm, v_lines_norm)
            if np.isfinite(cell_feat).all():
                cell_inp = cell_feat.transpose(2, 0, 1)[np.newaxis].astype(np.float32)
                conn_out = self._conn_sess.run(None, {"cell_features": cell_inp})
                conn_logits = conn_out[0][0]
                conn_prob = 1.0 / (1.0 + np.exp(-conn_logits.astype(np.float64)))
                connectivity = conn_prob.transpose(1, 2, 0).astype(np.float32)

        return GridPrediction(
            h_lines=sorted(h_lines),
            v_lines=sorted(v_lines),
            h_on_prob=h_on_prob,
            v_on_prob=v_on_prob,
            h_lines_norm=h_lines_norm,
            v_lines_norm=v_lines_norm,
            h_cls=h_cls,
            connectivity=connectivity,
        )

    def predict(
        self,
        pixmap,
        bboxes=None,
        texts=None,
        span_threshold: float = 0.1,
    ) -> tuple:
        """
        Predict grid boundaries and optionally assign bboxes to grid cells.

        Parameters
        ----------
        image_bgr      : cropped table BGR image (any size)
        bboxes         : (N, 4) array-like of [x0, y0, x1, y1] in crop space.
                         If None or empty, only grid prediction is performed.
        texts          : list of text strings aligned with bboxes.
        span_threshold : fractional overlap to trigger span expansion (default 0.1)

        Returns
        -------
        (GridPrediction, list[CellInfo])
        CellInfo list is empty when bboxes is None or empty.
        """
        grid = self.predict_grid(pixmap)

        if not bboxes:
            return grid, []

        img_rgb = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
            pixmap.height, pixmap.width, pixmap.n
        )

        bboxes_arr = np.asarray(bboxes, dtype=np.float32)
        crop_h = float(pixmap.h)
        crop_w = float(pixmap.w)

        bboxes_crop = bboxes_arr
        cx_list = sorted((float(b[0]) + float(b[2])) / 2.0 for b in bboxes_arr)
        cy_list = sorted((float(b[1]) + float(b[3])) / 2.0 for b in bboxes_arr)

        max_h = len(grid.h_on_prob)
        anchors = np.linspace(0.0, 1.0, max_h, dtype=np.float32)
        orig_h = float(pixmap.h)

        h_tuples = []
        h_cls_list = (
            grid.h_cls.tolist() if grid.h_cls is not None else [1] * len(grid.h_lines) # pylint: disable=no-member
        )
        for y, c in zip(grid.h_lines, h_cls_list):
            y_norm = y / orig_h
            idx = int(np.argmin(np.abs(anchors - y_norm)))
            score = float(grid.h_on_prob[idx])
            h_tuples.append((y, score, c))

        max_v = len(grid.v_on_prob)
        anchors_v = np.linspace(0.0, 1.0, max_v, dtype=np.float32)
        orig_w = float(pixmap.w)

        v_tuples = []
        for x in grid.v_lines:
            x_norm = x / orig_w
            idx = int(np.argmin(np.abs(anchors_v - x_norm)))
            score = float(grid.v_on_prob[idx])
            v_tuples.append((x, score, 0))

        if self.filter_empty_lines:
            h_tuples = self._filter_empty_lines(h_tuples, cy_list, crop_h)
            v_tuples = self._filter_empty_lines(v_tuples, cx_list, crop_w)
            while h_tuples and not any(0.0 <= c <= h_tuples[0][0] for c in cy_list):
                h_tuples = h_tuples[1:]
            while v_tuples and not any(0.0 <= c <= v_tuples[0][0] for c in cx_list):
                v_tuples = v_tuples[1:]
            while h_tuples and not any(h_tuples[-1][0] <= c <= crop_h for c in cy_list):
                h_tuples = h_tuples[:-1]
            while v_tuples and not any(v_tuples[-1][0] <= c <= crop_w for c in cx_list):
                v_tuples = v_tuples[:-1]

        filtered_h = [y for y, _, _ in h_tuples]
        filtered_v = [x for x, _, _ in v_tuples]
        filtered_h_cls = np.array([c for _, _, c in h_tuples], dtype=np.int32)

        if self.snap_to_bbox_gaps:
            snapped = self._snap_lines_to_bbox_gaps(filtered_h, bboxes_crop)
            h_tuples = [(sy, sc, c) for sy, (_, sc, c) in zip(snapped, h_tuples)]
            filtered_h = [y for y, _, _ in h_tuples]

        filtered_h_norm = np.array([y / orig_h for y in filtered_h], dtype=np.float32)
        filtered_v_norm = np.array([x / orig_w for x in filtered_v], dtype=np.float32)

        grid = GridPrediction(
            h_lines=sorted(filtered_h),
            v_lines=sorted(filtered_v),
            h_on_prob=grid.h_on_prob,
            v_on_prob=grid.v_on_prob,
            h_lines_norm=filtered_h_norm,
            v_lines_norm=filtered_v_norm,
            h_cls=filtered_h_cls,
            connectivity=grid.connectivity,
        )

        cells = self._post_process_grid(
            bboxes_page=bboxes_arr,
            grid=grid,
            span_threshold=span_threshold,
        )

        if texts is not None:
            for cell in cells:
                if 0 <= cell.bbox_idx < len(texts):
                    cell.text = texts[cell.bbox_idx]

        return grid, cells

    # ------------------------------------------------------------------
    # Grid-based bbox assignment
    # ------------------------------------------------------------------

    def _post_process_grid(
        self,
        bboxes_page: np.ndarray,
        grid: GridPrediction,
        span_threshold: float,
    ) -> list:
        if grid.h_lines:
            last_h = sorted(grid.h_lines)[-1]
            row_edges = [0.0] + sorted(grid.h_lines) + [max(last_h * 2, last_h + 1)]
        else:
            row_edges = [0.0, 1.0]

        if grid.v_lines:
            last_v = sorted(grid.v_lines)[-1]
            col_edges = [0.0] + sorted(grid.v_lines) + [max(last_v * 2, last_v + 1)]
        else:
            col_edges = [0.0, 1.0]

        def find_cell_idx(pos, edges):
            for i in range(len(edges) - 1):
                if edges[i] <= pos < edges[i + 1]:
                    return i
            return max(0, len(edges) - 2)

        results = []
        for i, bbox in enumerate(bboxes_page):
            x0 = float(bbox[0])
            y0 = float(bbox[1])
            x1 = float(bbox[2])
            y1 = float(bbox[3])
            cx = (x0 + x1) / 2.0
            cy = (y0 + y1) / 2.0

            base_row = find_cell_idx(cy, row_edges)
            base_col = find_cell_idx(cx, col_edges)
            row_start = base_row
            row_end = base_row + 1
            col_start = base_col
            col_end = base_col + 1

            r = base_row
            while r > 0:
                h = row_edges[r] - row_edges[r - 1]
                if h > 0 and (row_edges[r] - y0) / h > span_threshold:
                    row_start = r - 1
                    r -= 1
                else:
                    break
            r = base_row
            while r < len(row_edges) - 2:
                h = row_edges[r + 1] - row_edges[r]
                if h > 0 and (y1 - row_edges[r + 1]) / h > span_threshold:
                    row_end = r + 2
                    r += 1
                else:
                    break
            c = base_col
            while c > 0:
                w = col_edges[c] - col_edges[c - 1]
                if w > 0 and (col_edges[c] - x0) / w > span_threshold:
                    col_start = c - 1
                    c -= 1
                else:
                    break
            c = base_col
            while c < len(col_edges) - 2:
                w = col_edges[c + 1] - col_edges[c]
                if w > 0 and (x1 - col_edges[c + 1]) / w > span_threshold:
                    col_end = c + 2
                    c += 1
                else:
                    break

            results.append(
                CellInfo(
                    bbox_idx=i,
                    row_start=row_start,
                    row_end=row_end,
                    col_start=col_start,
                    col_end=col_end,
                    row=base_row,
                    col=base_col,
                )
            )

        return results
