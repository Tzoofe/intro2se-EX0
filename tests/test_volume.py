import nrrd
import numpy as np
import pytest

from projection.volume import NrrdReader


def write_nrrd(tmp_path, data, name="v.nrrd"):
    path = str(tmp_path / name)
    nrrd.write(path, data)
    return path


@pytest.mark.parametrize("dtype", [np.int8, np.uint8, np.int16, np.uint16, np.int32, np.uint32])
def test_reads_supported_types(tmp_path, dtype):
    data = np.arange(24, dtype=dtype).reshape(2, 3, 4)
    volume = NrrdReader.read(write_nrrd(tmp_path, data))
    assert volume.shape == (2, 3, 4)
    assert volume.data.dtype == dtype
    assert (volume.min_value, volume.max_value) == (0, 23)


def test_signed_min_max(tmp_path):
    data = np.array([-5, 0, 7], dtype=np.int16).reshape(1, 1, 3)
    volume = NrrdReader.read(write_nrrd(tmp_path, data))
    assert (volume.min_value, volume.max_value) == (-5, 7)


def test_rejects_2d(tmp_path):
    with pytest.raises(ValueError, match="3D"):
        NrrdReader.read(write_nrrd(tmp_path, np.zeros((4, 4), np.uint8)))


def test_rejects_float(tmp_path):
    with pytest.raises(ValueError, match="float32"):
        NrrdReader.read(write_nrrd(tmp_path, np.zeros((2, 2, 2), np.float32)))


def test_rejects_size_1024(tmp_path):
    with pytest.raises(ValueError, match="out of range"):
        NrrdReader.read(write_nrrd(tmp_path, np.zeros((1024, 1, 1), np.uint8)))


def test_accepts_size_1023(tmp_path):
    assert NrrdReader.read(write_nrrd(tmp_path, np.zeros((1023, 1, 1), np.uint8))).shape == (1023, 1, 1)


def test_rejects_garbage(tmp_path):
    path = tmp_path / "bad.nrrd"
    path.write_text("garbage")
    with pytest.raises(ValueError, match="not a valid NRRD"):
        NrrdReader.read(str(path))


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        NrrdReader.read(str(tmp_path / "missing.nrrd"))
