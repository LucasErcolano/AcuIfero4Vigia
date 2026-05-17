from __future__ import annotations

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from acuifero_vigia.services.deterministic_firewall import analyze_frames


def _write_frame(tmp_path, idx: int, waterline_row: int, width: int = 320, height: int = 240):
    image = np.full((height, width, 3), 220, dtype=np.uint8)
    image[waterline_row:, :, :] = 40
    image[waterline_row - 1 : waterline_row + 1, :, :] = 0
    path = tmp_path / f"frame_{idx:03d}.png"
    cv2.imwrite(str(path), image)
    return str(path)


def test_static_low_water(tmp_path):
    paths = [_write_frame(tmp_path, i, waterline_row=210) for i in range(3)]
    result = analyze_frames(paths, sample_seconds=1.0)
    assert result.opencv_used is True
    assert result.water_level in {"low", "elevated"}
    assert result.rise_velocity == pytest.approx(0.0, abs=0.02)
    assert all(f.brightness > 0 for f in result.frames)


def test_rising_water_crosses_critical(tmp_path):
    rows = [220, 170, 110, 70]
    paths = [_write_frame(tmp_path, i, waterline_row=r) for i, r in enumerate(rows)]
    result = analyze_frames(paths, sample_seconds=1.0, critical_line_ratio=0.5)
    assert result.opencv_used is True
    assert result.rise_velocity > 0
    assert result.crossed_critical_line is True
    assert result.water_level == "critical"


def test_elevated_without_crossing(tmp_path):
    rows = [220, 190, 165]
    paths = [_write_frame(tmp_path, i, waterline_row=r) for i, r in enumerate(rows)]
    result = analyze_frames(paths, sample_seconds=1.0, critical_line_ratio=0.5)
    assert result.crossed_critical_line is False
    assert result.water_level in {"elevated", "low"}
    assert result.rise_velocity > 0


def test_empty_frame_list():
    result = analyze_frames([], sample_seconds=1.0)
    assert result.frames == []
