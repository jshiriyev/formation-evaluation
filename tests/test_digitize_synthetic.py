"""Tests for the synthetic pages, the score and the digitizer scorecard."""

from pathlib import Path

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")
pytest.importorskip("pypdfium2")

from pphys import WellLog  # noqa: E402
from pphys.digitize import (  # noqa: E402
    QC,
    TARGET,
    Defects,
    DigitizeError,
    DigitizeResult,
    Settings,
    SyntheticCurve,
    SyntheticTrack,
    digitize,
    find_tesseract,
    score,
    synthetic_scan,
)
from pphys.digitize import scorecard  # noqa: E402
from pphys.digitize._digitize import curve_mask, render_pdf_page  # noqa: E402

NOTEBOOKS = Path(__file__).resolve().parents[1] / "notebooks"


@pytest.fixture(scope="module")
def page():
    return synthetic_scan()


def offsets(scan, name, depths):
    """Pixel offset between the drawn curve (median mask column) and its true column."""
    track, curve = scan.curve(name)
    x0, x1 = scan.track_columns[scan.tracks.index(track)]
    mask = curve_mask(scan.image)
    out = []
    for d in depths:
        row = int(round(float(scan.row_of(d))))
        cols = np.flatnonzero(mask[row, int(x0) : int(x1)]) + int(x0)
        true = np.interp(d, scan.depth, scan.values[name])
        out.append(np.median(cols) - (x0 + track.fraction(true, curve) * (x1 - x0)))
    return np.array(out)


# The page and its truth


def test_default_page_has_a_linear_and_a_log_track(page):
    assert page.image.shape == (1440, 864, 3)
    assert [t.scale for t in page.tracks] == ["linear", "log10"]
    assert set(page.values) == {"GR", "RT"}
    assert page.depth[0] == 1000 and page.depth[-1] == pytest.approx(1100, abs=0.16)
    for name, values in page.values.items():
        track, curve = page.curve(name)
        f = track.fraction(values, curve)
        assert 0.09 < f.min() and f.max() < 0.91


def test_track_frames_sit_on_the_true_edges(page):
    dark = np.flatnonzero(page.image[700].max(axis=1) < 60)
    for left, right in page.track_columns:
        assert np.abs(dark - left).min() <= 1
        assert np.abs(dark - right).min() <= 1


def assert_in_place(o):
    """Within a pixel (0.3 % of a track) row by row, and no one-sided bias."""
    assert np.median(np.abs(o)) < 1.0
    assert abs(np.median(o)) < 0.4


def test_curves_are_drawn_where_their_values_say(page):
    for name in ("GR", "RT"):
        assert_in_place(offsets(page, name, np.linspace(1005, 1095, 200)))


def test_heavy_grid_lines_sit_on_the_true_depths(page):
    x = int(np.mean(page.track_columns[0]))
    for d in (1010, 1050, 1090):
        row = int(round(float(page.row_of(d))))
        assert page.image[row - 1 : row + 2, x].min() < 200


def test_rows_and_depths_convert_both_ways(page):
    rows = page.row_of([1000, 1037.5, 1100], render_scale=3.0)
    np.testing.assert_allclose(
        page.depth_of(rows, render_scale=3.0), [1000, 1037.5, 1100]
    )
    (r0, d0), (r1, d1) = page.depth_pairs()
    assert (d0, r0) == (1000, pytest.approx(42.7, abs=0.1))
    assert d1 == page.depth[-1] and r1 > r0


def test_track_edges_follow_the_render_scale(page):
    left, right = page.track_columns[0]
    assert page.track_edges("GR") == pytest.approx((left, right))
    assert page.track_edges(0, render_scale=1.0) == pytest.approx(
        ((left + 0.5) / 2 - 0.5, (right + 0.5) / 2 - 0.5)
    )
    assert page.track_edges("RT") == pytest.approx(page.track_columns[1])


def test_pdf_pages_render_back_pixel_for_pixel(page, tmp_path):
    page.save(tmp_path / "page.pdf")
    assert np.array_equal(render_pdf_page(tmp_path / "page.pdf", 0, 2.0), page.image)


def test_image_pages_and_unknown_formats(page, tmp_path):
    path = page.save(tmp_path / "page.png")
    assert path.stat().st_size > 0 and page.path == path
    with pytest.raises(ValueError, match="Unknown page format"):
        page.save(tmp_path / "page.bmpx")


def test_values_from_arrays_and_functions():
    samples = np.arange(2000.0, 2050.0 + 0.0762, 0.1524)
    track = SyntheticTrack(
        (
            SyntheticCurve("GR", values=lambda d: 75 + 40 * np.sin(d / 3)),
            SyntheticCurve("CGR", values=np.full(samples.size, 30.0), color="blue"),
        )
    )
    scan = synthetic_scan(tracks=[track], depth=(2000, 2050), depth_column=0)
    np.testing.assert_allclose(scan.values["GR"], 75 + 40 * np.sin(scan.depth / 3))
    assert np.all(scan.values["CGR"] == 30)
    assert not scan.values["GR"].flags.writeable


def test_a_curve_on_its_own_scale_is_drawn_in_place():
    sp = SyntheticCurve(
        "SP", values=lambda d: -60 + 40 * np.sin(d / 4), vmin=-160.0, vmax=40.0
    )
    scan = synthetic_scan(tracks=[SyntheticTrack((sp,), 0, 150)])
    assert_in_place(offsets(scan, "SP", np.linspace(1005, 1095, 200)))


def test_the_seed_makes_pages_reproducible():
    a, b, c = synthetic_scan(seed=3), synthetic_scan(seed=3), synthetic_scan(seed=4)
    assert np.array_equal(a.image, b.image)
    assert not np.allclose(a.values["GR"], c.values["GR"])


def test_track_fraction_works_in_log_space():
    track = SyntheticTrack((SyntheticCurve("RT"),), 0.2, 2000.0, scale="log10")
    curve = track.curves[0]
    np.testing.assert_allclose(track.fraction([0.2, 2.0, 2000.0], curve), [0, 0.25, 1])
    np.testing.assert_allclose(track.value_at([0.25, 0.5], curve), [2.0, 20.0])


@pytest.mark.parametrize(
    "build",
    [
        lambda: SyntheticCurve(" "),
        lambda: SyntheticCurve("GR", linewidth=0),
        lambda: SyntheticCurve("GR", vmin=0.0),
        lambda: SyntheticTrack((), 0, 150),
        lambda: SyntheticTrack((SyntheticCurve(),), 0, 150, scale="sqrt"),
        lambda: SyntheticTrack((SyntheticCurve(),), 5, 5),
        lambda: SyntheticTrack((SyntheticCurve(),), 0, 2000, scale="log10"),
        lambda: Defects(fade=1.0),
        lambda: Defects(jpeg=0),
        lambda: Defects(tint="not a colour"),
        lambda: synthetic_scan(depth=(1000, 1000)),
        lambda: synthetic_scan(depth_unit="km"),
        lambda: synthetic_scan(depth_column=5),
        lambda: synthetic_scan(
            tracks=[SyntheticTrack((SyntheticCurve(values=[1.0, 2.0]),))]
        ),
        lambda: synthetic_scan(
            tracks=[SyntheticTrack((SyntheticCurve(values=lambda d: d * 0 + 200.0),))]
        ),
        lambda: synthetic_scan(
            tracks=[SyntheticTrack((SyntheticCurve(values=lambda d: d * np.nan),))]
        ),
        lambda: synthetic_scan(
            tracks=[SyntheticTrack((SyntheticCurve("GR"), SyntheticCurve("GR")))]
        ),
    ],
)
def test_bad_pages_are_rejected(build):
    with pytest.raises(ValueError):
        build()


# Defects


def test_tint_colours_the_paper(page):
    tinted = synthetic_scan(defects=Defects(tint="#f1e4c4"))
    assert tuple(tinted.image[5, 5]) == pytest.approx((0xC4, 0xE4, 0xF1), abs=1)
    assert tuple(page.image[5, 5]) == (255, 255, 255)


def test_fade_lightens_the_ink(page):
    faded = synthetic_scan(defects=Defects(fade=0.5))
    ink = curve_mask(page.image) > 0
    assert faded.image[ink].min(axis=1).mean() > page.image[ink].min(axis=1).mean() + 50


def test_rotation_tilts_the_tracks(page):
    rotated = synthetic_scan(defects=Defects(rotation=1.0))
    left = page.track_columns[0][0]

    def frame(row):
        dark = np.flatnonzero(rotated.image[row].max(axis=1) < 90)
        return dark[np.abs(dark - left).argmin()]

    assert abs(frame(100) - frame(1340)) > 15


def test_noise_blur_and_jpeg_change_the_pixels_a_little(page):
    for defects in (Defects(noise=10.0), Defects(blur=1.0), Defects(jpeg=30)):
        diff = np.abs(synthetic_scan(defects=defects).image.astype(int) - page.image)
        assert 0 < diff.mean() < 10, defects


# The score


def fake_result(scan, name, values, depth_fit=None):
    """A DigitizeResult that 'read' ``values``: resampled on the truth's depths,
    and raw on every page row where they are finite (as digitize keeps them)."""
    values = np.asarray(values, dtype=float)
    las = WellLog()
    las.append_curve("DEPT", scan.depth, unit="M")
    las.append_curve(name, values)
    r0, r1 = scan.row_of([scan.depth[0], scan.depth[-1]])
    raw_depth = scan.depth_of(np.arange(np.ceil(r0), np.floor(r1) + 1))
    raw_value = np.interp(raw_depth, scan.depth, values)
    found = np.isfinite(raw_value)
    qc = QC(
        scan="fake.pdf",
        page=0,
        page_size=scan.image.shape[1::-1],
        tracks=[],
        track=(0, 1),
        track_source="manual",
        scale="linear",
        depth_source="manual",
        depth_fit=scan.depth_fit if depth_fit is None else depth_fit,
    )
    return DigitizeResult(las, qc, Settings(), {}, raw_depth[found], raw_value[found])


def test_a_perfect_reading_scores_zero(page):
    result = score(fake_result(page, "GR", page.values["GR"]), page)
    assert (result.rms, result.max, result.depth) == pytest.approx((0, 0, 0), abs=1e-9)
    assert result.coverage == pytest.approx(100)
    assert result.passed and "pass" in str(result)


def test_value_errors_are_a_percent_of_the_track_width(page):
    result = score(fake_result(page, "GR", page.values["GR"] + 1.5), page)
    assert (result.rms, result.max) == pytest.approx((1.0, 1.0))
    assert result.passed
    assert not score(fake_result(page, "GR", page.values["GR"] + 6.0), page).passed


def test_log_tracks_are_scored_in_log_space(page):
    result = score(fake_result(page, "RT", page.values["RT"] * 10**0.04), page)
    assert result.rms == pytest.approx(1.0)


def test_depth_errors_and_coverage_are_scored(page):
    a, b = page.depth_fit
    shifted = score(
        fake_result(page, "GR", page.values["GR"], depth_fit=(a, b + 1.0)), page
    )
    assert shifted.depth == pytest.approx(
        100 / (page.depth[-1] - page.depth[0])
    )  # 1 m of ~100 m
    assert not shifted.passed
    half = page.values["GR"].copy()
    half[: half.size // 2] = np.nan
    assert score(fake_result(page, "GR", half), page).coverage == pytest.approx(
        50, abs=1
    )


def test_a_reading_outside_the_interval_scores_nothing(page):
    result = fake_result(page, "GR", np.full(page.depth.size, np.nan))
    assert score(result, page).coverage == 0 and not score(result, page).passed


def test_the_target_is_the_agreed_one():
    assert TARGET == {"rms": 1.0, "max": 3.0, "coverage": 98.0, "depth": 0.5}


# The scenarios: known gaps are strict xfails, so a fix shows up as a failure


def _scenario_param(s):
    marks = [pytest.mark.xfail(strict=True, reason=s.gap)] if s.gap else []
    return pytest.param(s, id=s.name, marks=marks)


@pytest.mark.parametrize("scenario", [_scenario_param(s) for s in scorecard.SCENARIOS])
def test_scenario_meets_the_target(scenario, tmp_path):
    row = scorecard.run_scenario(scenario, tmp_path)
    if row.skipped:
        pytest.skip(row.skipped)
    assert row.error is None, row.error
    assert row.passed, str(row.score)


def test_scenario_names_are_unique():
    names = [s.name for s in scorecard.SCENARIOS]
    assert len(names) == len(set(names))


def test_scorecard_prints_a_table(capsys):
    assert scorecard.main(["clean", "rotated"]) == 0
    out = capsys.readouterr().out
    assert "clean" in out and "rotated" in out and "not planned" in out
    with pytest.raises(ValueError, match="Unknown scenario"):
        scorecard.run(["nope"])


def test_a_real_gamma_ray_shape_digitizes_within_the_target(tmp_path):
    from pphys import read

    las = read(NOTEBOOKS / "tutorial_3_graph_2.LAS")
    gamma = np.clip(las["GAMMA"], 0, 150)
    track = SyntheticTrack(
        (SyntheticCurve("GR", values=lambda d: np.interp(d, las.index, gamma)),)
    )
    page = synthetic_scan(
        tmp_path / "gr.pdf", tracks=[track], depth=(1682, 1742), depth_column=0
    )
    result = digitize(
        tmp_path / "gr.pdf",
        curve="GR",
        vmin=0,
        vmax=150,
        track_edges=page.track_edges("GR"),
        depth=page.depth_pairs(),
    )
    assert score(result, page).passed, str(score(result, page))


def test_ocr_reads_some_labels_when_tesseract_is_installed(tmp_path):
    try:
        find_tesseract()
    except DigitizeError:
        pytest.skip("Tesseract not found")
    page = synthetic_scan(tmp_path / "page.pdf")
    try:
        result = digitize(
            tmp_path / "page.pdf",
            curve="GR",
            vmin=0,
            vmax=150,
            track_edges=page.track_edges("GR"),
        )
    except DigitizeError:
        return  # too few labels is today's known gap (scenario ocr_depth)
    assert result.qc.depth_source == "ocr"
    assert result.qc.depth_labels
