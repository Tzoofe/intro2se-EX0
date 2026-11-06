import imageio.v2 as imageio
import numpy as np
import pytest

from projection.video_writer import VideoWriter


def read_frames(path):
    return [frame[:, :, 0] for frame in imageio.get_reader(path)]


def test_even_size_and_frame_count(tmp_path):
    path = str(tmp_path / "out.mp4")
    with VideoWriter(path, 101, 51) as writer:
        writer.write_frame(np.full((101, 51), 200, dtype=np.uint8))
        writer.write_error_frame(2)
        writer.write_frame(np.full((10, 10), 200, dtype=np.uint8))
    frames = read_frames(path)
    assert len(frames) == 3
    assert frames[0].shape == (102, 52)
    meta = imageio.get_reader(path).get_meta_data()
    assert meta["codec"] == "h264"   # FR34
    assert meta["fps"] == 10         # FR39


def test_padding_centered_top_aligned(tmp_path):
    path = str(tmp_path / "out.mp4")
    with VideoWriter(path, 40, 40) as writer:
        writer.write_frame(np.full((10, 20), 255, dtype=np.uint8))
    frame = read_frames(path)[0].astype(int)
    assert frame[5, 20] > 200          # inside the image: top, center
    assert frame[30, 20] < 50          # below the image: black
    assert frame[5, 2] < 50            # left of the image: black


def test_error_frame_not_black(tmp_path):
    path = str(tmp_path / "out.mp4")
    with VideoWriter(path, 100, 100) as writer:
        writer.write_error_frame(3)
        writer.write_error_frame(4, "a long reason that does not fit on one line of a small frame")
    frames = read_frames(path)
    assert len(frames) == 2
    assert frames[0].max() > 200 and frames[1].max() > 200


def test_unwritable_path(tmp_path):
    with pytest.raises(OSError, match="cannot write video"):
        with VideoWriter(str(tmp_path / "no_dir" / "out.mp4"), 10, 10) as writer:
            writer.write_frame(np.zeros((10, 10), dtype=np.uint8))


def test_write_failure_mid_video(tmp_path):
    """FR40: an error while writing a frame (e.g. disk full) is reported as OSError."""
    def fail(frame):
        raise IOError("disk full")

    with pytest.raises(OSError, match="cannot write video .*disk full"):
        with VideoWriter(str(tmp_path / "out.mp4"), 10, 10) as writer:
            writer._writer.append_data = fail
            writer.write_frame(np.zeros((10, 10), dtype=np.uint8))
