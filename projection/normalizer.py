import numpy as np


class Normalizer:
    """Converts projections to 8-bit grayscale with one global scale for the
    whole volume, so the same tissue keeps the same brightness in every frame (FR36, DD11)."""

    def __init__(self, min_value, max_value):
        self.min_value = min_value
        self.max_value = max_value

    def normalize(self, E, mask):
        """E: projection image; mask: True where the pixel was sampled from the volume.
        Returns a uint8 image; pixels outside the mask are black (FR37)."""
        out = np.zeros(E.shape, dtype=np.uint8)
        value_range = self.max_value - self.min_value
        if value_range == 0:
            return out

        scaled = (E[mask].astype(np.float64) - self.min_value) * (255 / value_range)
        out[mask] = np.rint(scaled).astype(np.uint8)
        return out


if __name__ == "__main__":
    E = np.array([[-100, 0, 50], [100, 0, 7]], dtype=np.int16)
    mask = np.array([[True, True, True], [True, False, False]])
    print(Normalizer(-100, 100).normalize(E, mask))
