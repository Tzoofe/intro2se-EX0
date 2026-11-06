import numpy as np
import pytest

from projection.sampler import Sampler, NearestSampler


def test_nearest_voxel():
    data = np.arange(27, dtype=np.uint8).reshape(3, 3, 3)
    values, inside = NearestSampler().sample(data, np.array([[0, 0, 0], [1.4, 1.6, 2.2]]))
    assert values.tolist() == [0, data[1, 2, 2]]
    assert inside.tolist() == [True, True]


def test_outside_is_zero():
    data = np.full((3, 3, 3), 9, dtype=np.int16)
    values, inside = NearestSampler().sample(data, np.array([[2.6, 0, 0], [-1, 0, 0], [0, 0, 3]]))
    assert values.tolist() == [0, 0, 0]
    assert not inside.any()


def test_keeps_dtype():
    data = np.zeros((2, 2, 2), dtype=np.uint32)
    values, _ = NearestSampler().sample(data, np.zeros((1, 3)))
    assert values.dtype == np.uint32


def test_sampler_is_abstract():
    with pytest.raises(TypeError):
        Sampler()
