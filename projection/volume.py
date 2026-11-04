import nrrd
import numpy as np

MAX_SIZE = 1023
ALLOWED_DTYPES = ("int8", "uint8", "int16", "uint16", "int32", "uint32")


class Volume:
    """A 3D volume M, indexed as data[x, y, z] (voxel index coordinates)."""

    def __init__(self, data):
        self.data = data
        # Python ints, so later arithmetic (max - min) cannot overflow the voxel type.
        self.min_value = int(data.min())
        self.max_value = int(data.max())

    @property
    def shape(self):
        return self.data.shape


class NrrdReader:
    """Reads a single-file NRRD into a Volume and validates it (FR1 to FR5)."""

    @staticmethod
    def read(path):
        try:
            data, header = nrrd.read(path)
        except nrrd.NRRDError as e:
            raise ValueError(f"{path}: not a valid NRRD file ({e})")

        if data.ndim != 3:
            raise ValueError(f"{path}: expected a 3D volume, got dimension {data.ndim}")

        for size in data.shape:
            if size < 1 or size > MAX_SIZE:
                raise ValueError(f"{path}: size {data.shape} out of range, each size must be 1..{MAX_SIZE}")

        if data.dtype.name not in ALLOWED_DTYPES:
            raise ValueError(f"{path}: voxel type {data.dtype.name} not supported, expected one of {ALLOWED_DTYPES}")

        return Volume(data)


if __name__ == "__main__":
    volume = NrrdReader.read("MRHead_1.nrrd")
    print(volume.shape, volume.data.dtype, volume.min_value, volume.max_value)
