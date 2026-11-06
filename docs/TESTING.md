# Testing Strategy

Requirement numbers (FR, NFR, DD) refer to [SRS.md](SRS.md).

## Goals

1. **Correct:** every component does what the SRS specifies, including the corrections to the given algorithm ([ALGORITHM.md](ALGORITHM.md) §3).
2. **Stable:** no input, valid or invalid, ends in a crash (NFR5). Invalid input is reported, and invalid planes become error frames.
3. **Fast:** projection meets NFR1 (≥ 30 fps on 500³).
4. **Repeatable:** tests run on any machine after cloning, with no external data files.

## How to run

```bash
pytest          # all 85 tests, about 9 seconds
pytest -s       # also prints the measured fps
pytest tests/test_plane.py    # one component
```

`pytest.ini` adds the project root to the import path, so plain `pytest` works from the root.

The same tests run automatically on every push and pull request on Linux, Windows and macOS (Python 3.12) with GitHub Actions; the result is the badge at the top of the README.

## Approach

- **Unit tests per component.** Each class has its own test file, matching the component split in NFR10. Components are tested in isolation: for example, `Projector` is tested on in-memory NumPy arrays, not NRRD files (NFR11).
- **Synthetic data.** Tests build their volumes in memory or write small NRRD files to a temporary folder. Real volumes are git-ignored, so the tests never depend on them. A volume with no zero values is used where it matters, so a sampled pixel cannot be confused with background.
- **Oracle test.** For a plane aligned with the axes, the correct answer is known exactly: it is a slice of the array. This checks the whole projection against an independent result.
- **Reference implementation.** `RowLoopProjector` is a simpler version that is close to the given algorithm. The fast `Projector` must produce exactly the same image and mask on a set of different planes.
- **Boundary values.** Limits are tested on both sides: size 1023 accepted, 1024 rejected; a leg difference just under EPS accepted, just over rejected.
- **Error paths.** Every validation rule and every fatal error has a test that checks the error type and message, or the exit code.
- **End to end.** The demo is run through its `main()` function with real files in a temporary folder, and the output video is read back.

## Test levels

### Unit tests

| File | Tests | What is checked |
|---|---|---|
| `test_volume.py` | 13 | All six integer voxel types load (FR3); signed min/max; rejects 2D (FR4), float, size 1024 (FR5); accepts 1023; garbage file and missing file give clear errors (FR7). |
| `test_plane.py` | 18 | Valid triangle (stored with `a1 = a2`, DD5) and trapezoid; values within EPS accepted; each invalid condition rejected with its reason: not isosceles, degenerate, collinear, top base longer than bottom, not on the same plane (FR16 to FR21); planes up to 2048 voxels accepted, longer ones rejected as too large (FR42). |
| `test_csv_reader.py` | 14 | One result per row with row numbers (FR8 to FR14); Excel export format (BOM, CRLF); seven kinds of bad rows (invalid N, non-number, missing value, too few or too many coordinates, `nan`, invalid plane); decimals and negatives (FR10); blank lines; header-only file (FR15); missing file; binary (Excel) file. |
| `test_sampler.py` | 8 | Nearest voxel; points outside the volume give 0 and are marked outside (FR30); voxel type kept; `Sampler` cannot be created (abstract). Trilinear: equals the voxel at voxel centers; exact on a volume whose values are a linear function of x, y, z; midpoint of a cube is the average of its 8 corners; edges and points just outside the volume. |
| `test_projector.py` | 17 | See below. |
| `test_normalizer.py` | 4 | Global scale for signed data (FR36); background black (FR37); constant volume maps to 0; no overflow for `uint32`. |
| `test_video_writer.py` | 4 | Frame size rounded to even and frame count (FR35, FR38); padding centered and top-aligned; error frames drawn, also with a reason too long for one line (FR41); unwritable path gives a clear error (FR40). |

### Projector tests

| Test | What it checks | SRS |
|---|---|---|
| Oracle: axis-aligned rectangle | A rectangle in the plane `z = k` gives exactly `M[:, :, k]`, with every pixel marked as sampled. | FR25 to FR32 |
| Output size | `E` and `mask` have the size from `output_size`, which matches `floor(Dab) + 1` × `ceil(Dbc) + 1`. | FR26 |
| Apex sampled | Row 0 of a triangle has exactly one sampled pixel, in the center column, with the apex voxel's value. | FR27, DD6 |
| Rows centered | The sampled pixels of every row are centered on the same column. | FR29 |
| Plane outside volume | All black, nothing marked as sampled. | FR23, FR30 |
| Plane partly outside | Pixels outside the volume are not marked; pixels inside are. | FR30, FR37 |
| Voxel type kept | `E` has the same type as the volume. | FR33 |
| Sampler injected | With a test sampler that always returns 7, every sampled pixel is 7, so `Projector` really uses the sampler it is given. | NFR12 |
| Oracle with trilinear | The axis-aligned oracle also holds with `TrilinearSampler`, since every sample falls exactly on a voxel. | NFR12 |
| Same as row loop (7 planes) | `Projector` equals `RowLoopProjector` on axis-aligned, oblique, partly outside and tiny (smaller than one voxel) triangles, and on rectangular, non-parallel and oblique trapezoids. | — |
| Performance | Average of 50 projections of a 559×501 triangle on a random 500³ `uint8` volume is at least 30 fps (measured ~167 fps). | NFR1, NFR3 |

### Sample data tests

The lecturer's sample CSV ([Ex0.csv](../Ex0.csv)) is used directly:

- Rows 1, 2 and 4 are valid; row 3 is not isosceles.
- Row 4 is valid only in the point order `(a1, b, a2, c)`. In the order `(a1, a2, b, c)` it is rejected, which supports design decision DD2.

### End-to-end tests (the demo)

`test_ex0.py` runs `Ex0.main()` on a synthetic 300³ `uint16` NRRD file:

| Test | Expected |
|---|---|
| Sample CSV | exit code 0; video with **4 frames** (one per row, FR35); warning for row 3 printed (FR22); projection time and fps printed (FR43). |
| All rows invalid | exit code 0; one error frame per row. |
| Huge plane (legs of 10,000,000 voxels) next to a normal plane | exit code 0; 2 frames: an error frame ("too large") and the normal projection, so one huge row does not stop the video (FR42, DD13). |
| Wrong number of arguments (2 cases) | exit code 2 with a usage message. |
| Missing NRRD, missing CSV | exit code 1 with a clear message (FR7, FR15). |
| Output folder does not exist | exit code 1 with a clear message (FR40). |

## Manual checks

Some properties are visual and are checked by looking at the output:

- The experiment videos ([EXPERIMENT.md](EXPERIMENT.md)) on four real volumes: the head, onion, biscuit cake and Swiss roll. The layered volumes make wrong geometry easy to spot: the onion's rings must turn into circles and the Swiss roll's spiral into straight layers as the plane rotates.
- The error frame shows a white X, `Invalid plane: row N` and the reason, wrapped to fit the frame.
- Every dataset volume loads and runs through the demo, covering int16, uint8, uint16 and uint32 in real files.

## Requirements coverage

| Requirements | Covered by |
|---|---|
| FR1 to FR7 (NRRD input) | `test_volume.py`, `test_ex0.py`, dataset run |
| FR8 to FR15 (CSV input) | `test_csv_reader.py`, `test_ex0.py` |
| FR16 to FR23, FR42 (validation) | `test_plane.py`, `test_csv_reader.py`, `test_projector.py` |
| FR24 to FR33 (projection) | `test_projector.py`, `test_sampler.py` |
| FR34 to FR41, FR43 (video, demo output) | `test_normalizer.py`, `test_video_writer.py`, `test_ex0.py` |
| NFR1 to NFR3 (performance) | `test_projector.py::test_performance_500_cubed`, [experiments/benchmark.py](../experiments/benchmark.py) |
| NFR5 (no crash) | error-path tests in every file, `test_ex0.py` |
| NFR7 (portability) | the whole suite runs on Linux, Windows and macOS on every push ([.github/workflows/tests.yml](../.github/workflows/tests.yml)) |
| NFR10 to NFR12 (design) | per-component tests, projector tests on plain arrays, sampler injection test, `TrilinearSampler` used through the same `Projector` |

Not covered by automated tests: `raw` encoding and big-endian NRRD files (FR2; both are handled by pynrrd, but all test and sample files are gzip, little-endian).
