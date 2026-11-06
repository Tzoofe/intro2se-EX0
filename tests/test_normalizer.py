import numpy as np

from projection.normalizer import Normalizer


def test_global_scale_signed():
    E = np.array([[-100, 0, 50, 100]], dtype=np.int16)
    out = Normalizer(-100, 100).normalize(E, np.ones(E.shape, dtype=bool))
    assert out.dtype == np.uint8
    assert out.tolist() == [[0, 127, 191, 255]]


def test_background_is_black():
    E = np.array([[-100, 50]], dtype=np.int16)
    out = Normalizer(-100, 100).normalize(E, np.array([[False, True]]))
    assert out[0, 0] == 0


def test_constant_volume():
    E = np.full((2, 2), 5, dtype=np.int32)
    assert not Normalizer(5, 5).normalize(E, np.ones((2, 2), dtype=bool)).any()


def test_uint32_no_overflow():
    E = np.array([[0, 4294967295]], dtype=np.uint32)
    out = Normalizer(0, 4294967295).normalize(E, np.ones(E.shape, dtype=bool))
    assert out.tolist() == [[0, 255]]
