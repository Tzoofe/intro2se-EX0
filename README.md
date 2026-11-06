# Ex1 - Plane Projection of a 3D Volume

Compute 2D cross-sections of a 3D medical volume along arbitrary planes, and render a sequence of such slices as a video.

## Problem

Medical scanners such as MRI and CT produce a 3D volume: a stack of 2D images that together form a 3D matrix of intensity values. A screen can only show 2D images, so the volume is viewed as slices. Programs such as 3D Slicer typically show three axis-aligned slices, but anatomical structures are rarely aligned with the scanner's axes. To see such structures properly, the volume must be sliced along an **arbitrary (oblique) plane**.

This project takes a 3D volume and a plane defined by 3 or 4 points, and computes the 2D image of the volume's cross-section on that plane. Given a list of planes, it produces a video with one frame per plane.

The algorithm must be fast enough for interactive use: at least 30 fps (target 100+ fps) for a 500×500×500 volume.

## Scope

### In scope

- Reading 3D volumes in NRRD format (8, 16 and 32-bit integer voxels, signed or unsigned).
- Planes defined by:
    - **3 points** `(a, b, c)` forming an isosceles triangle: `|dist(a, b) - dist(a, c)| < EPS`.
    - **4 points** `(a1, b, a2, c)` forming an isosceles trapezoid with legs `a1→b` and `a2→c`: `|dist(a1, b) - dist(a2, c)| < EPS`, `dist(a1, a2) <= dist(b, c)`, all points on the same plane.
- Validation of planes (`EPS = 0.001`). An invalid plane raises an exception; the demo shows it as an error frame.
- Projecting the volume onto each plane as a 2D image.
- Writing all projections to an MP4 video, in the order given in the CSV.
- A command-line demo (`Ex0.py`).

### Out of scope

- A graphical or interactive user interface.
- Physical (mm) coordinates: plane points are given in **voxel index coordinates** (as implied by the problem definition and the sample CSV).
- 3D rendering (volume rendering, surface rendering).
- File formats other than NRRD for input and MP4 for output.

## Input / Output

```bash
python Ex0.py file.nrrd file.csv file.mp4
```

- **`file.nrrd`**: a 3D volume in a single NRRD file (raw or gzip). Each size must be 1 to 1023.
- **`file.csv`**: a header row, then one plane per row. The first value is the number of points N (3 or 4), followed by 3·N coordinates. Empty trailing cells are ignored. Example ([Ex0.csv](Ex0.csv)):

  ```
  Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4
  3,200,200,0,0,200,400,400,200,400,,,
  4,200,0,0,200,0,500,200,400,0,200,400,500
  ```

  For N = 3 the points are `(a, b, c)` with `a` the apex. For N = 4 they are `(a1, b, a2, c)`: the trapezoid's two legs `a1→b` and `a2→c` (see SRS DD2).
- **`file.mp4`**: an H.264 video at 10 fps with **exactly one frame per CSV row**:
    - a valid plane gives its projection, in 8-bit grayscale (global min/max of the volume), with a black background;
    - an invalid row or plane gives an **error frame**: black, with a white X and the text `Invalid plane: row N`. The reason is printed to the terminal.

  All frames have the same size (the largest projection, rounded up to even); smaller projections are centered horizontally and aligned to the top.

Exit codes: `0` success, `1` fatal error (missing or invalid NRRD, missing or empty CSV, output not writable), `2` wrong arguments.

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python Ex0.py data/MRHead_1.nrrd Ex0.csv out.mp4
```

Requires Python 3.10+. Dependencies: NumPy, [pynrrd](https://github.com/mhe/pynrrd) (NRRD reading), imageio + imageio-ffmpeg (MP4 writing, ffmpeg included), Pillow (error-frame text), pytest (tests).

## How to test

```bash
pytest          # all tests
pytest -s       # also prints the measured fps of the performance test
```

The tests use synthetic volumes, so they do not need any NRRD file. See [docs/TESTING.md](docs/TESTING.md).

## Dataset

NRRD files go in [data/](data/). They are not committed (`.gitignore`); download them and place them there.

| File | Content | Shape | Voxel type | Encoding | Source |
|---|---|---|---|---|---|
| `MRHead_1.nrrd` | MRI of a head | 256×256×130 | int16 (signed) | gzip, little-endian | 3D Slicer sample data (Sample Data module) |
| `onion.nrrd` | onion: concentric layers | 256×256×130 | uint8 | gzip | Open dataset shared by classmates in the course |
| `biscuit_cake.nrrd` | layered biscuit cake | 256×256×130 | uint16 | gzip, little-endian | Open dataset shared by classmates in the course |
| `swiss_roll.nrrd` | Swiss roll: spiral layers | 256×256×130 | uint32 | gzip, little-endian | Open dataset shared by classmates in the course |

Together they cover 8, 16 and 32-bit voxels, signed and unsigned. The three food volumes have layered, curved structures, which make it easy to see whether an oblique slice is correct.

Other data:

- **Synthetic volumes**: random and known-pattern volumes created by the tests, including 500×500×500 `uint8` for the performance requirement.
- **Ex0.csv**: the lecturer's sample planes. Row 3 is intentionally invalid (not isosceles). The planes are sized for a ~500³ volume, so on MRHead most of each frame is outside the volume.

## Project Structure

```
├── Ex0.py                  # demo CLI: arguments, flow, error handling, exit codes
├── Ex0.csv                 # sample planes
├── projection/
│   ├── volume.py           # Volume, NrrdReader (+ validation)
│   ├── plane.py            # Plane (triangle / trapezoid), InvalidPlaneError
│   ├── csv_reader.py       # PlaneCsvReader -> one PlaneRow per CSV row
│   ├── sampler.py          # Sampler (abstract), NearestSampler
│   ├── projector.py        # Projector (vectorized), RowLoopProjector (reference)
│   ├── normalizer.py       # Normalizer: global 8-bit scaling, black background
│   └── video_writer.py     # VideoWriter: padding, error frames, MP4
├── tests/                  # pytest suite
└── docs/                   # SRS, algorithm, testing strategy
```

Flow: `NrrdReader → Volume`, `PlaneCsvReader → [PlaneRow]`, then for each row `Projector(NearestSampler) → (E, mask) → Normalizer → VideoWriter`.

Design notes:
- Each component is a separate class, testable on its own.
- `Projector` works on any 3D NumPy array and knows nothing about NRRD or CSV.
- The sampling method is injected into `Projector` (Strategy pattern), so nearest-neighbor can be replaced, e.g. with trilinear interpolation, without changing `Projector`.
- `Plane.from_triangle` / `Plane.from_trapezoid` are factory methods that validate the points; a triangle is stored as a trapezoid with `a1 = a2`, so one algorithm handles both.

## Performance

Projection step only, synthetic 500×500×500 `uint8` volume, average of 50 runs, MacBook Pro 14" M5:

| Plane | Output (H×W) | Row loop (`RowLoopProjector`) | Fully vectorized (`Projector`) |
|---|---|---|---|
| Triangle, axis-aligned | 559×501 | 105 fps | **169 fps** |
| Triangle, oblique | 749×501 | 78 fps | **127 fps** |
| Rectangle, axis-aligned | 500×500 | 81 fps | **83 fps** |

- An earlier version with plain Python loops for every pixel ran at ~28 fps, even on a smaller 238×237 image.
- The rectangle samples a full 500×500 frame with large memory strides, so it is limited by memory access rather than by Python overhead, and vectorizing does not help.

## Documentation

- [docs/SRS.md](docs/SRS.md): Software Requirements Specification (functional and non-functional requirements, design decisions).
- `docs/ALGORITHM.md`: detailed algorithm *(TBD)*.
- [docs/TESTING.md](docs/TESTING.md): testing strategy *(TBD)*.
