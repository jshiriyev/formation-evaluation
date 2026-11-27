"""Tests for pphys.digitize on synthetic scans; Tesseract is never needed."""

import json
import subprocess
import sys

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")
pytest.importorskip("pypdfium2")
Image = pytest.importorskip("PIL.Image")

import pphys  # noqa: E402
from pphys import digitize as dz  # noqa: E402
from pphys.digitize import (  # noqa: E402
    DepthCalibrationError,
    DigitizeError,
    Settings,
    digitize,
    find_tesseract,
)
from pphys.digitize import _digitize  # noqa: E402
from pphys.digitize._cli import main  # noqa: E402

WIDTH, HEIGHT = 400, 600
ONE = Settings(render_scale=1.0)  # rendered page pixels == drawing pixels
ROWS = np.arange(HEIGHT)


def write_scan(path, *curves, frames=()):
    """A white PDF page with black track frames at ``frames`` (left, right
    columns) and one red polyline per curve (x per row)."""
    img = np.full((HEIGHT, WIDTH, 3), 255, np.uint8)
    for left, right in frames:
        img[:, left : left + 2] = 0
        img[:, right : right + 2] = 0
    for xs in curves:
        pts = np.column_stack([xs, ROWS]).round().astype(np.int32).reshape(-1, 1, 2)
        cv2.polylines(img, [pts], False, (0, 0, 230), 3)  # BGR red
    Image.fromarray(img[..., ::-1]).save(path, "PDF", resolution=72)
    return path


def zigzag(center, half=40, period=40):
    """A triangle wave that visits every column of its band equally often."""
    phase = (ROWS / period) % 2
    return center - half + 2 * half * np.abs(phase - 1)


@pytest.fixture
def ramp(tmp_path):
    """One curve from column 50 (top) to 350 (bottom): 0..150 across edges 50-350."""
    return write_scan(tmp_path / "ramp.pdf", 50 + 300 * ROWS / (HEIGHT - 1))


@pytest.fixture
def framed_ramp(tmp_path):
    """The ramp inside a track framed at columns 50-51 and 350-351 (centres 50.5, 350.5)."""
    return write_scan(
        tmp_path / "framed.pdf", 50.5 + 300 * ROWS / (HEIGHT - 1), frames=[(50, 350)]
    )


@pytest.fixture
def two_tracks(tmp_path):
    """Zigzags around columns 100 and 300, in tracks framed at 40-160 and 240-360."""
    return write_scan(
        tmp_path / "two.pdf", zigzag(100), zigzag(300), frames=[(40, 160), (240, 360)]
    )


@pytest.fixture
def no_tesseract(monkeypatch, tmp_path):
    monkeypatch.delenv("TESSERACT_CMD", raising=False)
    monkeypatch.setattr(_digitize.shutil, "which", lambda name: None)
    for var in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        monkeypatch.setenv(var, str(tmp_path / "empty"))


def ramp_result(scan, **kwargs):
    kwargs = {
        "curve": "GR",
        "vmin": 0,
        "vmax": 150,
        "unit": "gAPI",
        "depth": (1000, 1060),
        "track_edges": (50, 350),
        "settings": ONE,
        **kwargs,
    }
    return digitize(scan, **kwargs)


# Settings and helpers


@pytest.mark.parametrize(
    "kwargs",
    [
        {"render_scale": 0},
        {"min_labels": 1},
        {"hue_bands": ((0, 200),)},
        {"hue_bands": ()},
        {"max_label_height": 2},
        {"min_value": 300},
        {"min_line_fraction": 0},
        {"frame_tolerance": 1.0},
        {"ink_contrast": 0},
    ],
)
def test_settings_reject_bad_values(kwargs):
    with pytest.raises(ValueError):
        Settings(**kwargs)


def test_settings_normalize_hue_bands():
    assert Settings(hue_bands=[(100.0, 130.0)]).hue_bands == ((100, 130),)


def test_map_x_to_value_is_linear_and_follows_reversed_scales():
    x = np.array([10.0, 60.0, 110.0])
    np.testing.assert_allclose(
        _digitize.map_x_to_value(x, 10, 110, 0, 150), [0, 75, 150]
    )
    np.testing.assert_allclose(
        _digitize.map_x_to_value(x, 10, 110, 0.45, -0.15), [0.45, 0.15, -0.15]
    )


def test_fit_depth_ignores_misreads():
    points = [(y, 0.5 * y + 1000) for y in range(0, 1000, 100)]
    points += [(450.0, 2000.0), (150.0, 1610.0)]  # two misreads
    a, b, keep = _digitize.fit_depth(points)
    assert (a, b) == pytest.approx((0.5, 1000))
    assert keep.tolist() == [True] * 10 + [False, False]


def test_fit_depth_needs_two_points_and_depth_growing_downward():
    assert _digitize.fit_depth([(10.0, 1000.0)]) is None
    assert _digitize.fit_depth([(10.0, 1000.0), (20.0, 990.0)]) is None


def test_fit_depth_tolerance_is_in_rows():
    # Five labels 100 rows apart; the last sits 12 rows off the line.
    points = [(100.0 * i, 1000.0 + 10 * i) for i in range(4)] + [(412.0, 1040.0)]
    assert _digitize.fit_depth(points, tolerance=3.0)[2].tolist() == [True] * 4 + [
        False
    ]
    assert _digitize.fit_depth(points, tolerance=15.0)[2].all()


@pytest.mark.parametrize(
    "text, number",
    [
        ("1000", 1000.0),
        ("1002.5", 1002.5),
        ("-3", -3.0),
        ("12-5", None),
        (".", None),
        ("", None),
    ],
)
def test_parse_number(text, number):
    assert _digitize._parse_number(text) == number


def test_label_bands_are_outside_the_tracks():
    tracks = [_digitize.Track(40.0, 380.0), _digitize.Track(480.0, 820.0)]
    assert _digitize.label_bands(tracks, 864) == [
        (0.0, 40.0),
        (380.0, 480.0),
        (820.0, 863.0),
    ]
    assert _digitize.label_bands(tracks, 864, columns=(500, 400)) == [(400.0, 500.0)]
    assert _digitize.label_bands([_digitize.Track(3.0, 860.0)], 864) == []


# digitize with manual depths


def test_ramp_with_track_edges_reads_the_values(ramp):
    result = ramp_result(ramp)
    las, qc = result.las, result.qc

    expected = 150 * (las.index - 1000) / 60
    inner = (las.index > 1001) & (las.index < 1059)
    np.testing.assert_allclose(las["GR"][inner], expected[inner], atol=1.5)

    assert las.index[0] == pytest.approx(1000, abs=0.2)
    np.testing.assert_allclose(np.diff(las.index), 0.1524)
    assert las.curves[0].unit == "M"
    assert (las.curves[1].mnemonic, las.curves[1].unit) == ("GR", "gAPI")
    assert las.well["WELL"].value == "ramp"
    assert "ramp.pdf" in las.other
    assert qc.page_size == (WIDTH, HEIGHT)
    assert qc.track == (50, 350)
    assert qc.depth_source == "manual"
    assert qc.coverage == pytest.approx(100)
    assert qc.warnings == []
    assert {"page", "mask", "track", "track_mask", "curve_overlay"} <= set(
        result.images
    )


def test_without_frames_or_track_edges_digitize_raises(ramp):
    with pytest.raises(DigitizeError, match="track_edges") as info:
        ramp_result(ramp, track_edges=None)
    assert "page" in info.value.images


def test_framed_track_edges_are_found(framed_ramp):
    result = ramp_result(framed_ramp, track_edges=None)
    qc = result.qc
    assert qc.track_source == "detected"
    assert qc.track == pytest.approx((50.5, 350.5), abs=0.01)
    assert qc.tracks == [pytest.approx((50.5, 350.5), abs=0.01)]
    inner = (result.las.index > 1001) & (result.las.index < 1059)
    expected = 150 * (result.las.index - 1000) / 60
    np.testing.assert_allclose(result.las["GR"][inner], expected[inner], atol=1.5)
    assert qc.warnings == []


def test_log10_scale_maps_in_log_space(framed_ramp):
    las = ramp_result(
        framed_ramp, track_edges=None, vmin=0.2, vmax=2000, scale="log10"
    ).las
    middle = np.argmin(np.abs(las.index - 1030))  # half way across the track
    assert las["GR"][middle] == pytest.approx(
        20, rel=0.03
    )  # 10**((log 0.2 + log 2000) / 2)
    assert "log10 scale" in las.curves[1].descr


def test_map_x_to_value_log10():
    x = np.array([0.0, 50.0, 100.0])
    np.testing.assert_allclose(
        _digitize.map_x_to_value(x, 0, 100, 1, 1000, "log10"), [1, 31.6227766, 1000]
    )


def test_grid_kind_reads_even_and_decade_spacing():
    linear = _digitize.Track(0.0, 100.0, [10.0 * i for i in range(1, 10)])
    decades = [25 * (k + np.log10(m)) for k in range(4) for m in range(1, 10)][1:]
    log = _digitize.Track(0.0, 100.0, decades)
    assert _digitize.grid_kind(linear) == "linear"
    assert _digitize.grid_kind(log) == "log10"
    assert _digitize.grid_kind(_digitize.Track(0.0, 100.0, [30.0, 70.0])) is None


def test_depth_as_row_pairs_matches_top_and_base(ramp):
    pairs = ramp_result(ramp, depth=[(0, 1000), (HEIGHT - 1, 1060)]).las
    top_base = ramp_result(ramp).las
    np.testing.assert_allclose(pairs.index, top_base.index)
    np.testing.assert_allclose(pairs["GR"], top_base["GR"])


def test_feet_use_a_half_foot_step(ramp):
    las = ramp_result(ramp, depth=(3000, 3200), depth_unit="ft").las
    assert las.curves[0].unit == "FT"
    np.testing.assert_allclose(np.diff(las.index), 0.5)


@pytest.mark.parametrize("depth", [(1000, 1000), (1000,), [(5, 1000), (5, 1010)]])
def test_bad_manual_depths_are_rejected(ramp, depth):
    with pytest.raises(ValueError):
        ramp_result(ramp, depth=depth)


def test_track_selection(two_tracks):
    def track(choice):
        kwargs = {
            "curve": "GR",
            "vmin": 0,
            "vmax": 1,
            "depth": (0, 100),
            "settings": ONE,
        }
        return digitize(two_tracks, track=choice, **kwargs).qc

    assert track("left").tracks == [
        pytest.approx((40.5, 160.5)),
        pytest.approx((240.5, 360.5)),
    ]
    assert track("left").track == pytest.approx((40.5, 160.5))
    assert track("right").track == pytest.approx((240.5, 360.5))
    assert track(1).track == track("right").track
    auto = track("auto")
    assert any("both hold the curve colour" in w for w in auto.warnings)
    with pytest.raises(DigitizeError, match="2 track"):
        track(5)
    with pytest.raises(ValueError):
        track("middle")


def test_auto_picks_the_track_holding_the_curve(tmp_path):
    scan = write_scan(tmp_path / "one.pdf", zigzag(300), frames=[(40, 160), (240, 360)])
    qc = digitize(scan, curve="GR", vmin=0, vmax=1, depth=(0, 100), settings=ONE).qc
    assert qc.track == pytest.approx((240.5, 360.5))
    assert qc.warnings == []


def test_a_grid_unlike_the_scale_is_flagged(tmp_path):
    from pphys.digitize import synthetic_scan

    page = synthetic_scan(tmp_path / "page.pdf")
    kwargs = {"curve": "RT", "depth": page.depth_pairs(), "track": "right"}
    linear = digitize(
        tmp_path / "page.pdf", vmin=0.2, vmax=2000, scale="linear", **kwargs
    ).qc
    assert linear.grid == "log10"
    assert any("grid looks log10" in w for w in linear.warnings)
    log = digitize(
        tmp_path / "page.pdf", vmin=0.2, vmax=2000, scale="log10", **kwargs
    ).qc
    assert not any("grid looks" in w for w in log.warnings)


# depth from OCR (Tesseract replaced by a stub)


COLUMNS = (170.0, 230.0)  # the gap between the two framed tracks


def labels(*rows, misread=()):
    """Labels on depth = 0.1 * row + 1000, plus ``misread`` (row, depth) pairs."""
    found = [(float(r), 1000.0 + 0.1 * r) for r in rows] + list(misread)
    return [
        _digitize.Label(
            row, depth, f"{depth:g}", 90.0, (180, int(row) - 4, 220, int(row) + 4)
        )
        for row, depth in sorted(found)
    ]


def stub_labels(monkeypatch, found):
    monkeypatch.setattr(
        _digitize,
        "find_depth_labels",
        lambda page, tracks, settings, columns: (COLUMNS, found),
    )


def ocr(page):
    return digitize(page, curve="GR", vmin=0, vmax=1, track="left", settings=ONE)


def test_ocr_labels_calibrate_depth(two_tracks, monkeypatch):
    stub_labels(monkeypatch, labels(0, 100, 200, 300, 400))
    qc = ocr(two_tracks).qc
    assert qc.depth_source == "ocr"
    assert qc.depth_fit == pytest.approx((0.1, 1000))
    assert qc.label_columns == COLUMNS
    assert qc.depth_inliers == [True] * 5
    assert qc.depth_residuals == pytest.approx([0] * 5, abs=1e-9)
    assert qc.depth_rms == pytest.approx(0, abs=1e-9)
    assert not any("label" in w for w in qc.warnings)
    assert "5 of 5 on the line" in qc.summary()


def test_misread_labels_are_ignored_and_listed(two_tracks, monkeypatch):
    stub_labels(monkeypatch, labels(0, 100, 200, 300, 400, misread=[(150.0, 1610.0)]))
    result = ocr(two_tracks)
    assert result.qc.depth_fit == pytest.approx((0.1, 1000))
    assert result.qc.depth_inliers == [True, True, False, True, True, True]
    assert any("'1610' at row 150" in w for w in result.qc.warnings)
    assert "depth_labels" in result.images


def test_few_ocr_labels_are_flagged(two_tracks, monkeypatch):
    stub_labels(monkeypatch, labels(0, 250, 500))
    assert any("only 3 labels" in w for w in ocr(two_tracks).qc.warnings)


def test_scattered_labels_are_flagged(two_tracks, monkeypatch):
    found = labels(0, 100, 200, 300, 400)
    for label, shift in zip(found, (2.5, -2.5, 2.5, -2.5, 2.5)):
        label.row += shift
    stub_labels(monkeypatch, found)
    # With a 3-row tolerance three collinear labels would win; at 6 rows all five
    # stay on the line, 2.5 rows off it.
    loose = Settings(render_scale=1.0, label_tolerance=6.0)
    qc = digitize(
        two_tracks, curve="GR", vmin=0, vmax=1, track="left", settings=loose
    ).qc
    assert all(qc.depth_inliers)
    assert qc.depth_rms > 1.5
    assert any("stretched" in w for w in qc.warnings)


def test_too_few_agreeing_labels_raise(two_tracks, monkeypatch):
    stub_labels(monkeypatch, labels(10, 300, misread=[(150.0, 1610.0)]))
    with pytest.raises(
        DepthCalibrationError, match="2 agree on one line, but 3"
    ) as info:
        ocr(two_tracks)
    assert "depth_labels" in info.value.images


def test_a_page_without_labels_raises(ramp):
    with pytest.raises(DepthCalibrationError, match="Found 0 depth label"):
        digitize(
            ramp, curve="GR", vmin=0, vmax=150, track_edges=(50, 350), settings=ONE
        )


def test_missing_tesseract_is_reported(tmp_path, no_tesseract):
    from pphys.digitize import synthetic_scan

    page = synthetic_scan(tmp_path / "page.pdf")
    with pytest.raises(DigitizeError, match="Tesseract"):
        digitize(
            tmp_path / "page.pdf",
            curve="GR",
            vmin=0,
            vmax=150,
            track_edges=page.track_edges("GR"),
        )


# Tesseract lookup


def test_find_tesseract_prefers_the_explicit_path(tmp_path):
    exe = tmp_path / "tesseract.exe"
    exe.write_text("")
    assert find_tesseract(exe) == str(exe)
    with pytest.raises(DigitizeError, match="not found at"):
        find_tesseract(tmp_path / "missing.exe")


def test_find_tesseract_reads_the_environment(tmp_path, no_tesseract, monkeypatch):
    exe = tmp_path / "tess.exe"
    exe.write_text("")
    monkeypatch.setenv("TESSERACT_CMD", str(exe))
    assert find_tesseract() == str(exe)


def test_find_tesseract_explains_the_alternatives(no_tesseract):
    with pytest.raises(DigitizeError, match=r"depth=\(top, base\)"):
        find_tesseract()


# Inputs


def test_rejects_missing_files_and_non_pdf_scans(tmp_path):
    with pytest.raises(FileNotFoundError):
        digitize(tmp_path / "none.pdf", curve="GR", vmin=0, vmax=1)
    image = tmp_path / "scan.png"
    image.write_bytes(b"")
    with pytest.raises(DigitizeError, match="only PDF"):
        digitize(image, curve="GR", vmin=0, vmax=1)


def test_rejects_a_missing_page(ramp):
    with pytest.raises(DigitizeError, match="page 3"):
        ramp_result(ramp, page=3)


def test_a_page_without_the_curve_colour_raises(tmp_path):
    with pytest.raises(DigitizeError, match="No curve"):
        ramp_result(write_scan(tmp_path / "blank.pdf"))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"curve": " "},
        {"vmax": 0},
        {"depth_unit": "km"},
        {"step": 0},
        {"track_edges": (50, 900)},
        {"scale": "sqrt"},
        {"scale": "log10"},  # vmin = 0 cannot be on a log scale
    ],
)
def test_bad_arguments_are_rejected(ramp, kwargs):
    with pytest.raises(ValueError):
        ramp_result(ramp, **kwargs)


# Output


def test_save_writes_las_csv_images_and_qc(ramp, tmp_path):
    result = ramp_result(ramp)
    las_path = result.save(tmp_path / "out")

    assert las_path == tmp_path / "out" / "ramp.las"
    np.testing.assert_allclose(pphys.read(las_path)["GR"], result.las["GR"], atol=1e-4)
    rows = np.loadtxt(tmp_path / "out" / "ramp.csv", delimiter=",", skiprows=1)
    assert rows.shape == (len(result.depth), 2)
    for name in result.images:
        assert (tmp_path / "out" / f"{name}.png").stat().st_size > 0
    report = json.loads((tmp_path / "out" / "qc.json").read_text(encoding="utf-8"))
    assert report["qc"]["track"] == [50, 350]
    assert report["settings"]["render_scale"] == 1.0


def test_qc_summary_lists_the_warnings(two_tracks):
    qc = digitize(
        two_tracks, curve="GR", vmin=0, vmax=1, depth=(0, 100), settings=ONE
    ).qc
    summary = qc.summary()
    assert "depth: manual" in summary
    assert "detected" in summary and "linear scale" in summary
    assert "warning:" in summary  # two tracks hold the curve colour


def test_cli_writes_the_outputs(ramp, tmp_path, capsys):
    out = tmp_path / "cli"
    args = [
        str(ramp),
        "--curve",
        "GR",
        "--vmin",
        "0",
        "--vmax",
        "150",
        "--unit",
        "gAPI",
    ]
    args += [
        "--depth",
        "1000",
        "1060",
        "--track-edges",
        "50",
        "350",
        "--render-scale",
        "1",
        "--out",
        str(out),
    ]
    assert main(args) == 0
    assert pphys.read(out / "ramp.las").curves[1].unit == "gAPI"
    assert "LAS:" in capsys.readouterr().out


def test_cli_reports_errors_without_a_traceback(tmp_path, capsys):
    assert (
        main(
            [str(tmp_path / "none.pdf"), "--curve", "GR", "--vmin", "0", "--vmax", "1"]
        )
        == 1
    )
    assert "pphys-digitize:" in capsys.readouterr().err


def test_module_runs_as_a_command():
    result = subprocess.run(
        [sys.executable, "-m", "pphys.digitize", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "pphys-digitize" in result.stdout


def test_package_exports():
    assert set(dz.__all__) == {
        "QC",
        "DepthCalibrationError",
        "DigitizeError",
        "DigitizeResult",
        "Settings",
        "digitize",
        "find_tesseract",
        "TARGET",
        "Defects",
        "Score",
        "SyntheticCurve",
        "SyntheticScan",
        "SyntheticTrack",
        "score",
        "synthetic_scan",
    }
    assert all(hasattr(dz, name) for name in dz.__all__)
