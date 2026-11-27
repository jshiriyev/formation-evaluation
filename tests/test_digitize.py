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


def write_scan(path, *curves):
    """A white PDF page with one red polyline per curve (x per row)."""
    img = np.full((HEIGHT, WIDTH, 3), 255, np.uint8)
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
def two_tracks(tmp_path):
    return write_scan(tmp_path / "two.pdf", zigzag(100), zigzag(300))


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
        {"label_skip": 1.0},
        {"hue_bands": ((0, 200),)},
        {"hue_bands": ()},
        {"ocr_chunk_overlap": 5000},
        {"min_value": 300},
        {"track_margin": -1},
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


def test_fit_depth_transform_drops_an_outlier():
    points = [(y, 0.5 * y + 1000) for y in range(0, 1000, 100)] + [(450.0, 2000.0)]
    a, b = _digitize.fit_depth_transform(points)
    assert a == pytest.approx(0.5)
    assert b == pytest.approx(1000)


def test_fit_depth_transform_needs_two_points():
    assert _digitize.fit_depth_transform([(10.0, 1000.0)]) is None


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


def test_without_track_edges_the_scale_is_flagged(ramp):
    result = ramp_result(ramp, track_edges=None)
    assert len(result.qc.warnings) == 1
    assert "track_edges" in result.qc.warnings[0]


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

    assert len(track("left").tracks) == 2
    assert track("left").track[0] < 100 < track("left").track[1]
    assert track("right").track[0] < 300 < track("right").track[1]
    assert track(1).track == track("right").track
    with pytest.raises(DigitizeError, match="2 track"):
        track(5)
    with pytest.raises(ValueError):
        track("middle")


# depth from OCR (Tesseract replaced by a stub)


def labels(*rows):
    return [(float(r), 1000.0 + 0.1 * r) for r in rows]


def test_ocr_labels_calibrate_depth(two_tracks, monkeypatch):
    monkeypatch.setattr(
        _digitize,
        "ocr_depth_points",
        lambda strip, settings: labels(0, 100, 200, 300, 400),
    )
    result = digitize(two_tracks, curve="GR", vmin=0, vmax=1, settings=ONE)
    assert result.qc.depth_source == "ocr"
    assert result.qc.depth_fit == pytest.approx((0.1, 1000))
    assert result.qc.depth_strip[0] < 200 < result.qc.depth_strip[1]
    assert not any("labels" in w for w in result.qc.warnings)
    assert {"depth_strip", "depth_labels"} <= set(result.images)


def test_few_ocr_labels_are_flagged(two_tracks, monkeypatch):
    monkeypatch.setattr(
        _digitize, "ocr_depth_points", lambda strip, settings: labels(0, 250, 500)
    )
    result = digitize(two_tracks, curve="GR", vmin=0, vmax=1, settings=ONE)
    assert any("only 3 labels" in w for w in result.qc.warnings)


def test_ocr_failure_raises_with_the_qc_images(two_tracks, monkeypatch):
    monkeypatch.setattr(
        _digitize, "ocr_depth_points", lambda strip, settings: labels(10)
    )
    with pytest.raises(DepthCalibrationError, match="1 usable depth label") as info:
        digitize(two_tracks, curve="GR", vmin=0, vmax=1, settings=ONE)
    assert "depth_labels" in info.value.images


def test_ocr_needs_two_tracks(ramp):
    with pytest.raises(DepthCalibrationError, match="two tracks"):
        digitize(ramp, curve="GR", vmin=0, vmax=150, settings=ONE)


def test_missing_tesseract_is_reported(two_tracks, no_tesseract):
    with pytest.raises(DigitizeError, match="Tesseract"):
        digitize(two_tracks, curve="GR", vmin=0, vmax=1, settings=ONE)


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


def test_qc_summary_lists_the_warnings(ramp):
    summary = ramp_result(ramp, track_edges=None).qc.summary()
    assert "depth: manual" in summary
    assert "warning:" in summary


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
        "--scale",
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
    }
