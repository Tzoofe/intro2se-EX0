"""Demo: python Ex0.py file.nrrd file.csv file.mp4

Projects the volume onto every plane in the CSV and writes one video frame
per CSV row: the projection for a valid plane, an error frame otherwise."""
import sys
import time

from projection.csv_reader import PlaneCsvReader
from projection.normalizer import Normalizer
from projection.projector import Projector
from projection.sampler import NearestSampler
from projection.video_writer import VideoWriter
from projection.volume import NrrdReader

DEFAULT_FRAME_SIZE = (256, 256)  # used when there are no valid planes (FR38)


def error(message):
    print(f"Error: {message}", file=sys.stderr)


def main(argv):
    if len(argv) != 4:
        error("usage: python Ex0.py file.nrrd file.csv file.mp4")
        return 2
    nrrd_path, csv_path, mp4_path = argv[1:]

    start = time.perf_counter()
    try:
        volume = NrrdReader.read(nrrd_path)
    except (OSError, ValueError) as e:
        error(e)
        return 1
    sx, sy, sz = volume.shape
    print(f"Loaded {nrrd_path}: {sx} x {sy} x {sz}, {volume.data.dtype} ({time.perf_counter() - start:.2f} s)")

    try:
        rows = PlaneCsvReader.read(csv_path)
    except (OSError, ValueError) as e:
        error(e)
        return 1

    for row in rows:
        if not row.is_valid:
            print(f"Warning: row {row.row_number}: {row.error}", file=sys.stderr)

    # Frame size is known from the geometry, so frames can be written one at a time (FR38, NFR4).
    sizes = [Projector.output_size(row.plane) for row in rows if row.is_valid]
    if sizes:
        height = max(h for h, w in sizes)
        width = max(w for h, w in sizes)
    else:
        height, width = DEFAULT_FRAME_SIZE

    projector = Projector(NearestSampler())
    normalizer = Normalizer(volume.min_value, volume.max_value)

    start = time.perf_counter()
    projection_time = 0.0
    try:
        with VideoWriter(mp4_path, height, width) as writer:
            for row in rows:
                if row.is_valid:
                    t = time.perf_counter()
                    E, mask = projector.project(volume.data, row.plane)
                    projection_time += time.perf_counter() - t
                    writer.write_frame(normalizer.normalize(E, mask))
                else:
                    writer.write_error_frame(row.row_number, row.error)
    except OSError as e:
        error(e)
        return 1

    valid = sum(row.is_valid for row in rows)
    if valid:
        average = projection_time / valid
        print(f"Projected {valid} plane(s): average {average * 1000:.2f} ms per plane ({1 / average:.0f} fps)")
    print(f"Wrote {len(rows)} frames ({valid} valid, {len(rows) - valid} invalid) "
          f"of size {writer.width}x{writer.height} to {mp4_path} ({time.perf_counter() - start:.2f} s)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:  # last resort: never end with a traceback (NFR5)
        error(f"unexpected error: {e}")
        sys.exit(1)
