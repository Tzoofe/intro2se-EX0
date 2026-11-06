import numpy as np
import pytest

from projection.sampler import Sampler, NearestSampler, TrilinearSampler


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


def test_trilinear_at_voxel_centers_equals_nearest():
    data = np.random.default_rng(0).integers(0, 1000, (4, 5, 6), dtype=np.uint16)
    points = np.array([[0, 0, 0], [3, 4, 5], [1, 2, 3]], dtype=float)
    values, inside = TrilinearSampler().sample(data, points)
    assert values.tolist() == [data[0, 0, 0], data[3, 4, 5], data[1, 2, 3]]
    assert inside.all()


def test_trilinear_is_exact_on_linear_volume():
    """On a volume whose values are a linear function, interpolation gives that function."""
    data = np.fromfunction(lambda x, y, z: x + 2 * y + 3 * z, (5, 6, 7)).astype(np.int32)
    points = np.random.default_rng(1).uniform(0, [4, 5, 6], (1000, 3))
    values, inside = TrilinearSampler().sample(data, points)
    assert inside.all()
    assert np.array_equal(values, np.rint(points @ [1, 2, 3]).astype(np.int32))


def test_trilinear_midpoint():
    data = np.zeros((2, 2, 2), dtype=np.uint8)
    data[1, 1, 1] = 80
    values, _ = TrilinearSampler().sample(data, np.array([[0.5, 0.5, 0.5]]))
    assert values.tolist() == [10]


def test_trilinear_outside_and_edges():
    data = np.full((3, 1, 3), 9, dtype=np.int16)
    points = np.array([[2, 0, 2], [-0.1, 0, 0], [2.1, 0, 0], [1.5, 0, 0.5]])
    values, inside = TrilinearSampler().sample(data, points)
    assert inside.tolist() == [True, False, False, True]
    assert values.tolist() == [9, 0, 0, 9]
