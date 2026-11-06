"""End-to-end tests of the demo (Ex0.main), on a synthetic volume."""
import imageio.v2 as imageio
import nrrd
import numpy as np
import pytest

from Ex0 import main


@pytest.fixture
def volume_path(tmp_path):
    path = str(tmp_path / "volume.nrrd")
    data = np.random.default_rng(0).integers(0, 1000, (300, 300, 300), dtype=np.uint16)
    nrrd.write(path, data)
    return path


def count_frames(path):
    return sum(1 for _ in imageio.get_reader(path))


def test_sample_csv_one_frame_per_row(volume_path, tmp_path, capsys):
    out = str(tmp_path / "out.mp4")
    assert main(["Ex0.py", volume_path, "Ex0.csv", out]) == 0
    assert count_frames(out) == 4
    output = capsys.readouterr()
    assert "row 3" in output.err
    assert "Projected 3 plane(s)" in output.out and "fps" in output.out


def test_huge_plane_becomes_error_frame(volume_path, tmp_path, capsys):
    """One plane too large for memory must not stop the video (DD3, FR42)."""
    csv_path = tmp_path / "huge.csv"
    csv_path.write_text("header\n3,0,0,0,10000000,0,0,0,10000000,0\n3,0,30,10,40,0,10,40,60,10\n")
    out = str(tmp_path / "out.mp4")
    assert main(["Ex0.py", volume_path, str(csv_path), out]) == 0
    assert count_frames(out) == 2
    assert "too large" in capsys.readouterr().err


def test_all_rows_invalid(volume_path, tmp_path):
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("header\n5,1,2,3\nx\n")
    out = str(tmp_path / "out.mp4")
    assert main(["Ex0.py", volume_path, str(csv_path), out]) == 0
    assert count_frames(out) == 2


@pytest.mark.parametrize("args", [
    ["Ex0.py"],
    ["Ex0.py", "a.nrrd", "b.csv"],
])
def test_usage(args):
    assert main(args) == 2


def test_missing_inputs(volume_path, tmp_path):
    out = str(tmp_path / "out.mp4")
    assert main(["Ex0.py", str(tmp_path / "missing.nrrd"), "Ex0.csv", out]) == 1
    assert main(["Ex0.py", volume_path, str(tmp_path / "missing.csv"), out]) == 1


def test_unwritable_output(volume_path, tmp_path):
    assert main(["Ex0.py", volume_path, "Ex0.csv", str(tmp_path / "no_dir" / "out.mp4")]) == 1


def test_command_line_as_a_process(volume_path, tmp_path):
    """NFR9: the exact command of the assignment, run as a separate process."""
    import subprocess
    import sys

    out = tmp_path / "out.mp4"
    result = subprocess.run([sys.executable, "Ex0.py", volume_path, "Ex0.csv", str(out)],
                            capture_output=True, text=True)
    assert result.returncode == 0
    assert out.exists()
    assert subprocess.run([sys.executable, "Ex0.py"], capture_output=True).returncode == 2


def test_same_input_same_video(volume_path, tmp_path):
    """NFR6: two runs on the same input give the same frames."""
    first, second = str(tmp_path / "1.mp4"), str(tmp_path / "2.mp4")
    assert main(["Ex0.py", volume_path, "Ex0.csv", first]) == 0
    assert main(["Ex0.py", volume_path, "Ex0.csv", second]) == 0
    frames_1 = [frame for frame in imageio.get_reader(first)]
    frames_2 = [frame for frame in imageio.get_reader(second)]
    assert len(frames_1) == len(frames_2)
    assert all(np.array_equal(f1, f2) for f1, f2 in zip(frames_1, frames_2))
