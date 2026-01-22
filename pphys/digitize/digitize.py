import os
import re
import json
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

import numpy as np
import cv2
import pytesseract
import pypdfium2 as pdfium

pytesseract.pytesseract.tesseract_cmd = (r"C:\Users\Javid.Shiriyev\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")

@dataclass
class Cluster:
    x0: int
    x1: int
    score: float

def render_pdf_page(pdf_path: str, page_index: int = 0, scale: float = 2.0) -> np.ndarray:
    """Render a PDF page to a BGR image (OpenCV)."""
    pdf = pdfium.PdfDocument(pdf_path)
    page = pdf.get_page(page_index)
    # Render
    pil_img = page.render(scale=scale).to_pil()
    rgb = np.array(pil_img)
    if rgb.ndim == 2:
        bgr = cv2.cvtColor(rgb, cv2.COLOR_GRAY2BGR)
    else:
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return bgr

def hsv_red_mask(bgr: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    # Red wraps around hue. Use two bands.
    lower1 = np.array([0, 70, 50])
    upper1 = np.array([10, 255, 255])
    lower2 = np.array([160, 70, 50])
    upper2 = np.array([180, 255, 255])
    m1 = cv2.inRange(hsv, lower1, upper1)
    m2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(m1, m2)
    # Clean
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=1)
    return mask

def find_red_clusters(mask: np.ndarray, min_width: int = 30) -> List[Cluster]:
    """Find contiguous x-ranges with lots of red pixels."""
    col_sum = mask.sum(axis=0)  # 0..255 per pixel
    # Normalize to 0..1-ish
    col = col_sum / 255.0
    # Threshold based on percentile to adapt
    thr = np.percentile(col, 95) * 0.3
    thr = max(thr, np.percentile(col, 90) * 0.5)
    on = col > thr

    clusters: List[Cluster] = []
    start = None
    for i, val in enumerate(on):
        if val and start is None:
            start = i
        elif (not val) and start is not None:
            end = i - 1
            if end - start + 1 >= min_width:
                score = float(col[start:end + 1].sum())
                clusters.append(Cluster(start, end, score))
            start = None
    if start is not None:
        end = len(on) - 1
        if end - start + 1 >= min_width:
            score = float(col[start:end + 1].sum())
            clusters.append(Cluster(start, end, score))

    clusters.sort(key=lambda c: (c.x0, -(c.x1 - c.x0)))
    return clusters

def pick_right_track(clusters: List[Cluster]) -> Tuple[Cluster, Optional[Cluster]]:
    """Pick the right-most cluster as right track; return (right, left_candidate)."""
    if not clusters:
        raise RuntimeError("No red clusters detected. Try adjusting thresholds or scale.")
    clusters_sorted = sorted(clusters, key=lambda c: c.x0)
    right = clusters_sorted[-1]
    left = clusters_sorted[-2] if len(clusters_sorted) >= 2 else None
    return right, left

def crop_with_margin(img: np.ndarray, x0: int, x1: int, y0: int, y1: int, margin: int = 40) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
    H, W = img.shape[:2]
    x0m = max(0, x0 - margin)
    x1m = min(W - 1, x1 + margin)
    y0m = max(0, y0)
    y1m = min(H - 1, y1)
    roi = img[y0m:y1m + 1, x0m:x1m + 1].copy()
    return roi, (x0m, y0m, x1m, y1m)

def build_depth_strip_roi(img: np.ndarray, left: Optional[Cluster], right: Cluster, half_width: int = 110) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
    H, W = img.shape[:2]
    if left is not None:
        x_center = int((left.x1 + right.x0) / 2)
    else:
        x_center = int(right.x0 - 200)
    x0 = max(0, x_center - half_width)
    x1 = min(W - 1, x_center + half_width)
    roi = img[:, x0:x1 + 1].copy()
    return roi, (x0, 0, x1, H - 1)

def ocr_depth_points(depth_strip_bgr: np.ndarray) -> List[Tuple[float, float]]:
    """Return list of (y_px, depth_value).

    MVP approach: robust OCR on the depth column by chunking the tall strip.
    We use CLAHE + blackhat + Otsu threshold to emphasize digits, then run
    tesseract once per chunk and parse numeric tokens.
    """
    gray_full = cv2.cvtColor(depth_strip_bgr, cv2.COLOR_BGR2GRAY)
    H, W = gray_full.shape

    # In this template, depth numbers sit on the right side of the strip.
    gray_full = gray_full[:, int(W * 0.25):]
    H, W = gray_full.shape

    chunk_h = 4000
    overlap = 300
    config = "--psm 6 -c tessedit_char_whitelist=0123456789"

    pts: List[Tuple[float, float]] = []

    y0 = 0
    while y0 < H:
        y1 = min(H, y0 + chunk_h)
        chunk = gray_full[y0:y1, :]

        # Downscale for stability
        target_h = 1400
        scale = target_h / max(1, chunk.shape[0])
        if scale < 1.0:
            chunk_s = cv2.resize(chunk, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        else:
            chunk_s = chunk
            scale = 1.0

        # Enhance digits
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        c = clahe.apply(chunk_s)
        bh = cv2.morphologyEx(c, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)))
        _, bw = cv2.threshold(bh, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # text tends to become white
        inv = 255 - bw  # black text on white

        data = pytesseract.image_to_data(inv, output_type=pytesseract.Output.DICT, config=config)

        n = len(data.get('text', []))
        for i in range(n):
            txt = (data['text'][i] or '').strip()
            if not txt:
                continue
            txt = re.sub(r'\s+', '', txt)
            if not re.fullmatch(r"\d{2,6}", txt):
                continue
            conf = float(data['conf'][i]) if data['conf'][i] != '-1' else -1.0
            if conf < 35:
                continue
            top = data['top'][i]
            h = data['height'][i]
            y_center_small = top + h / 2.0
            y_center = y0 + (y_center_small / scale)
            pts.append((float(y_center), float(txt)))

        if y1 >= H:
            break
        y0 = y1 - overlap

    # Deduplicate depths by keeping median y for each value
    by_depth: Dict[float, List[float]] = {}
    for y, d in pts:
        by_depth.setdefault(d, []).append(y)
    merged = [(float(np.median(ys)), d) for d, ys in by_depth.items()]
    merged.sort(key=lambda t: t[0])

    # Filter monotonic increasing depth
    filtered: List[Tuple[float, float]] = []
    last_d = None
    for y, d in merged:
        if last_d is None or d >= last_d:
            filtered.append((y, d))
            last_d = d

    return filtered

def fit_depth_transform(points: List[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
    """Fit depth = a*y + b. Returns (a,b) or None."""
    if len(points) < 2:
        return None
    y = np.array([p[0] for p in points], dtype=float)
    d = np.array([p[1] for p in points], dtype=float)

    # Robust-ish: remove outliers by iterative fitting
    mask = np.ones_like(y, dtype=bool)
    for _ in range(3):
        if mask.sum() < 2:
            break
        a, b = np.polyfit(y[mask], d[mask], 1)
        pred = a * y + b
        resid = np.abs(pred - d)
        mad = np.median(resid[mask]) if mask.sum() else np.median(resid)
        tol = max(5.0, 3.0 * mad)
        mask = resid < tol

    if mask.sum() < 2:
        return None
    a, b = np.polyfit(y[mask], d[mask], 1)
    return float(a), float(b)

def extract_curve_x_by_row(curve_mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """For each row y, compute x (median of mask pixels) and confidence (#pixels)."""
    H, W = curve_mask.shape
    xs = np.full(H, np.nan, dtype=float)
    conf = np.zeros(H, dtype=float)

    for y in range(H):
        cols = np.where(curve_mask[y, :] > 0)[0]
        if cols.size == 0:
            continue
        xs[y] = float(np.median(cols))
        conf[y] = float(cols.size)
    return xs, conf

def map_x_to_value(x_px: np.ndarray, x_left: float, x_right: float, vmin: float, vmax: float) -> np.ndarray:
    val = (x_px - x_left) / (x_right - x_left)
    val = vmin + val * (vmax - vmin)
    return val

def resample_to_step(depth: np.ndarray, value: np.ndarray, step: float) -> Tuple[np.ndarray, np.ndarray]:
    """Resample to regular depth step using linear interpolation, keeping NaNs as gaps."""
    # Sort by depth
    order = np.argsort(depth)
    depth = depth[order]
    value = value[order]

    dmin = float(np.nanmin(depth))
    dmax = float(np.nanmax(depth))

    d_new = np.arange(dmin, dmax + 0.5 * step, step)

    # Interpolate only over valid points
    valid = np.isfinite(depth) & np.isfinite(value)
    if valid.sum() < 2:
        return d_new, np.full_like(d_new, np.nan, dtype=float)

    v_new = np.interp(d_new, depth[valid], value[valid])
    return d_new, v_new

def write_las(path: str, depth: np.ndarray, curve: np.ndarray, curve_mnemonic: str = 'QK',
              depth_unit: str = 'M', curve_unit: str = '', well_name: str = '2580',
              null_value: float = -999.25, note: str = '') -> None:
    def fmt(v: float) -> str:
        if not np.isfinite(v):
            return f"{null_value:.2f}"
        return f"{v:.6f}".rstrip('0').rstrip('.') if abs(v) < 1e6 else f"{v:.6e}"

    lines = []
    lines.append("~Version")
    lines.append(" VERS.                  2.0 : CWLS LOG ASCII STANDARD")
    lines.append(" WRAP.                  NO  : ONE LINE PER DEPTH STEP")
    lines.append("~Well")
    lines.append(f" STRT.{depth_unit:>4} {fmt(float(depth[0])):>12} : START DEPTH")
    lines.append(f" STOP.{depth_unit:>4} {fmt(float(depth[-1])):>12} : STOP DEPTH")
    step_est = float(np.median(np.diff(depth))) if len(depth) > 1 else 0.0
    lines.append(f" STEP.{depth_unit:>4} {fmt(step_est):>12} : STEP")
    lines.append(f" NULL.      {null_value:>12} : NULL VALUE")
    lines.append(f" WELL.      {well_name:>12} : WELL")
    if note:
        # keep single line note
        note1 = note.replace('\n', ' ')[:120]
        lines.append(f" NOTE.      {note1}")
    lines.append("~Curve")
    lines.append(f" DEPT.{depth_unit:>4}              : DEPTH")
    lines.append(f" {curve_mnemonic}.{curve_unit:>4}              : DIGITIZED CURVE")
    lines.append("~ASCII")
    for d, v in zip(depth, curve):
        lines.append(f"{fmt(float(d))} {fmt(float(v))}")

    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")

def save_overlay_curve(roi_bgr: np.ndarray, xs: np.ndarray, out_path: str) -> None:
    overlay = roi_bgr.copy()
    H, W = overlay.shape[:2]
    pts = []
    for y in range(H):
        if np.isfinite(xs[y]):
            pts.append((int(xs[y]), int(y)))
    for p in pts:
        cv2.circle(overlay, p, 1, (0, 255, 255), -1)  # cyan points
    cv2.imwrite(out_path, overlay)

def save_overlay_depth_strip(depth_strip_bgr: np.ndarray, points: List[Tuple[float, float]],
                            fit: Optional[Tuple[float, float]], out_path: str) -> None:
    overlay = depth_strip_bgr.copy()
    for y, d in points:
        cv2.circle(overlay, (10, int(y)), 3, (0, 255, 0), -1)
        cv2.putText(overlay, str(int(d)), (20, int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    if fit is not None:
        a, b = fit
        H = overlay.shape[0]
        # draw depth at top/bottom
        d_top = a * 0 + b
        d_bot = a * (H - 1) + b
        cv2.putText(overlay, f"fit: d={a:.5f}*y+{b:.2f}", (5, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.putText(overlay, f"top~{d_top:.1f}  bottom~{d_bot:.1f}", (5, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    cv2.imwrite(out_path, overlay)

def main():
    import argparse
    ap = argparse.ArgumentParser(description="MVP digitizer: PDF scanned log -> LAS (single curve)")
    ap.add_argument('--pdf', required=True)
    ap.add_argument('--outdir', default='mvp_out')
    ap.add_argument('--page', type=int, default=0)
    ap.add_argument('--scale', type=float, default=2.0)
    ap.add_argument('--curve', default='QK')
    ap.add_argument('--vmin', type=float, default=0.0)
    ap.add_argument('--vmax', type=float, default=8.0)
    ap.add_argument('--step', type=float, default=0.1524)
    ap.add_argument('--depth-top', type=float, default=None, help='Manual depth at top of page (m). If set with --depth-bottom, overrides OCR.')
    ap.add_argument('--depth-bottom', type=float, default=None, help='Manual depth at bottom of page (m). If set with --depth-top, overrides OCR.')
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    page_bgr = render_pdf_page(args.pdf, page_index=args.page, scale=args.scale)
    H, W = page_bgr.shape[:2]
    cv2.imwrite(os.path.join(args.outdir, 'page.jpg'), page_bgr)

    red_mask = hsv_red_mask(page_bgr)
    cv2.imwrite(os.path.join(args.outdir, 'red_mask.jpg'), red_mask)

    clusters = find_red_clusters(red_mask)
    if not clusters:
        raise RuntimeError('No red clusters detected. Try different render scale.')

    right, left = pick_right_track(clusters)

    # Crop left track ROI with margin
    track_roi, track_bbox = crop_with_margin(page_bgr, right.x0, right.x1, 0, H - 1, margin=60)
    # x0, y0, x1, y1 = track_bbox
    cv2.imwrite(os.path.join(args.outdir, 'track_right.jpg'), track_roi)

    # Depth strip ROI
    depth_strip, depth_bbox = build_depth_strip_roi(page_bgr, left, right, half_width=120)
    
    clusters_sorted = sorted(clusters, key=lambda c: c.x0)
    
    if len(clusters_sorted) < 2:
        raise RuntimeError("Need at least 2 red clusters (left and right tracks).")
    
    left_track  = clusters_sorted[0]
    right_track = clusters_sorted[-1]
    
    track_roi, track_bbox = crop_with_margin(page_bgr, left_track.x0, left_track.x1, 0, H - 1, margin=60)
    x0, y0, x1, y1 = track_bbox
    cv2.imwrite(os.path.join(args.outdir, 'track_left.jpg'), track_roi)

# Depth strip ROI between left and right tracks (keep this!)
    depth_strip, depth_bbox = build_depth_strip_roi(page_bgr, left_track, right_track, half_width=120)
    cv2.imwrite(os.path.join(args.outdir, 'depth_strip.jpg'), depth_strip)
    
    # OCR depths
    depth_points = ocr_depth_points(depth_strip)
    fit = fit_depth_transform(depth_points)

    # Save depth debug
    save_overlay_depth_strip(depth_strip, depth_points, fit, os.path.join(args.outdir, 'debug_depth_ocr.jpg'))

    # Curve extraction on right track
    track_mask = hsv_red_mask(track_roi)
    cv2.imwrite(os.path.join(args.outdir, 'track_red_mask.jpg'), track_mask)

    xs, conf = extract_curve_x_by_row(track_mask)
    save_overlay_curve(track_roi, xs, os.path.join(args.outdir, 'debug_curve_overlay.jpg'))

    # Map to values using full ROI width
    x_left = 0.0
    x_right = float(track_roi.shape[1] - 1)
    values = map_x_to_value(xs, x_left, x_right, args.vmin, args.vmax)

    # Map y to depth
    ys = np.arange(track_roi.shape[0], dtype=float)
    depth_in_m = False
    if args.depth_top is not None and args.depth_bottom is not None:
        # Linear mapping using page top/bottom depths (fast, reliable MVP)
        a = (args.depth_bottom - args.depth_top) / max(1.0, float(H - 1))
        b = args.depth_top
        depth = a * (ys + y0) + b
        depth_note = f'Depth derived from manual top/bottom: {args.depth_top}..{args.depth_bottom} m.'
        depth_in_m = True
    elif fit is not None:
        a, b = fit
        depth = a * (ys + y0) + b  # y0 is 0, but keep correct if changed
        depth_note = 'Depth derived from OCR (linear fit).'
        depth_in_m = True
    else:
        depth = ys
        depth_note = 'WARNING: Depth OCR failed; using pixel rows as depth.'

    # Keep only rows with curve present
    depth_valid = depth[np.isfinite(values)]
    values_valid = values[np.isfinite(values)]

    # Resample
    d_res, v_res = resample_to_step(depth_valid, values_valid, args.step)

    # QC
    coverage = float(np.isfinite(v_res).sum()) / float(len(v_res)) * 100.0 if len(v_res) else 0.0
    qc_txt = []
    qc_txt.append(f"PDF: {args.pdf}")
    qc_txt.append(f"Page size (px): {W} x {H}")
    qc_txt.append(f"Right track bbox (page coords): {track_bbox}")
    qc_txt.append(f"Depth strip bbox (page coords): {depth_bbox}")
    qc_txt.append(f"OCR depth points: {len(depth_points)}")
    qc_txt.append(f"Depth fit: {fit}")
    qc_txt.append(f"Curve mnemonic: {args.curve}")
    qc_txt.append(f"Value range: [{args.vmin}, {args.vmax}]")
    qc_txt.append(f"Resample step: {args.step}")
    qc_txt.append(f"Coverage after resample: {coverage:.1f}%")
    qc_txt.append(depth_note)

    with open(os.path.join(args.outdir, 'qc_report.txt'), 'w', encoding='utf-8') as f:
        f.write("\n".join(qc_txt) + "\n")

    # Write LAS
    las_path = os.path.join(args.outdir, '2580_mvp.las')
    write_las(
        las_path,
        d_res,
        v_res,
        curve_mnemonic=args.curve,
        depth_unit='M' if depth_in_m else 'PX',
        curve_unit='',
        well_name='2580',
        null_value=-999.25,
        note=f"Digitized from {os.path.basename(args.pdf)}. {depth_note}"
    )

    # Save extracted curve table
    np.savetxt(os.path.join(args.outdir, 'curve_depth_value.csv'), np.column_stack([depth_valid, values_valid]),
               delimiter=',', header='depth,value', comments='')

    # Save preset
    preset = {
        'pdf': args.pdf,
        'page': args.page,
        'render_scale': args.scale,
        'curve': args.curve,
        'vmin': args.vmin,
        'vmax': args.vmax,
        'step': args.step,
        'right_track_bbox': track_bbox,
        'depth_strip_bbox': depth_bbox,
        'red_clusters': [c.__dict__ for c in clusters],
        'depth_fit': (
            {'mode': 'manual_top_bottom', 'top_m': args.depth_top, 'bottom_m': args.depth_bottom,
             'a': float((args.depth_bottom - args.depth_top) / max(1.0, float(H - 1))), 'b': float(args.depth_top)}
            if (args.depth_top is not None and args.depth_bottom is not None)
            else ({'mode': 'ocr_linear', 'a': fit[0], 'b': fit[1]} if fit is not None else None)
        ),
    }
    with open(os.path.join(args.outdir, 'preset_2580.json'), 'w', encoding='utf-8') as f:
        json.dump(preset, f, indent=2)

    print('Done.')
    print('LAS:', las_path)


if __name__ == '__main__':
    main()
