# Testing Strategy

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-11-06 | Tzoofe | First version: approach, test levels, coverage by requirement group. |
| 1.1 | 2026-11-06 | Tzoofe | Test-case IDs, per-requirement traceability, environments, entry/exit criteria, code coverage, performance marker, manual test procedures. |

Requirement numbers (FR, NFR, DD) refer to [SRS.md](SRS.md).

## 1. Goals

1. **Correct:** every component does what the SRS specifies, including the corrections to the original algorithm ([ALGORITHM.md](ALGORITHM.md) §3).
2. **Stable:** no input, valid or invalid, ends in a crash (NFR5). Invalid input is reported, and invalid planes become error frames.
3. **Fast:** projection meets NFR1 (≥ 30 fps on 500³).
4. **Repeatable:** tests run on any machine after cloning, with no external data files, and give the same result every time.

## 2. How to run

```bash
pytest                          # all 88 tests, about 12 seconds
pytest -m "not performance"     # everything except the speed test (faster, not affected by machine load)
pytest -m performance -s        # only the speed test, printing the measured fps
pytest --cov                    # with line and branch coverage (settings in .coveragerc)
pytest tests/test_plane.py      # one component
```

`pytest.ini` adds the project root to the import path, so plain `pytest` works from the root.

## 3. Test environments

| Environment | OS | Python | Libraries | When |
|---|---|---|---|---|
| Development | macOS (Darwin 27), MacBook Pro 14" M5 | 3.12.9 | exact versions in [requirements.txt](../requirements.txt) | every change |
| CI | Ubuntu, Windows and macOS (latest), GitHub Actions | 3.12 | installed from `requirements.txt` only | every push and pull request ([.github/workflows/tests.yml](../.github/workflows/tests.yml)) |

CI installs only what `requirements.txt` lists, so a passing CI run also shows that the dependency list is complete (NFR8).

## 4. Entry and exit criteria

**Entry** (testing can start):
- The SRS is the agreed baseline for expected behaviour.
- Dependencies install from `requirements.txt` without errors.

**Exit** (testing is complete):
- All automated tests pass on all three CI operating systems.
- Line and branch coverage of `projection/` and `Ex0.py` is at least 95% (measured: 100%, see §8).
- Every requirement FR1 to FR43 and NFR1 to NFR12 is traced to at least one test case, an experiment, or a design review (§7).
- The manual test procedures (§6) have been run on the current version with the expected results.
- No known defects remain open, other than the limitations listed in §9.

## 5. Approach

- **Unit tests per component.** Each class has its own test file, matching the component split in NFR10. Components are tested in isolation: `Projector` is tested on in-memory NumPy arrays, not NRRD files (NFR11).
- **Synthetic data.** Tests build their volumes in memory or write small NRRD files to a temporary folder. Real volumes are not in the repository, so the tests never depend on them. Where it matters, a volume with no zero values is used, so a sampled pixel cannot be confused with background.
- **Oracle tests.** For a plane aligned with the axes, the correct answer is known exactly: a slice of the array. On a volume whose values are a linear function of x, y and z, trilinear interpolation must return that function exactly.
- **Reference implementation.** `RowLoopProjector` is a simpler version that stays close to the original algorithm. The fast `Projector` must produce exactly the same image and mask on a set of different planes.
- **Boundary values.** Limits are tested on both sides: size 1023 accepted and 1024 rejected; plane side 2048 accepted and 2049 rejected; a leg difference just under EPS accepted and just over rejected.
- **Error paths.** Every validation rule and every fatal error has a test that checks the error type and message, or the exit code.
- **End to end.** The command-line program is run through `main()` and as a separate process with the documented command, and the output video is read back and checked.
- **Performance** is a separate, marked test (`performance`), so it can be left out of quick runs and does not hide functional results.

## 6. Test cases

Each test case has an ID. One test case can run several times with different inputs (shown as "× n"). Test function names are in `tests/test_<component>.py`.

### Volume reading: `test_volume.py`

| ID | Test | Checks | Requirements |
|---|---|---|---|
| TC-VOL-01 | `test_reads_supported_types` × 6 | int8, uint8, int16, uint16, int32, uint32 load with the right shape, type and values | FR1, FR3 |
| TC-VOL-02 | `test_signed_min_max` | global min and max of a signed volume | FR3, FR36 |
| TC-VOL-03 | `test_rejects_2d` | a 2D file is rejected with a clear message | FR4, FR7 |
| TC-VOL-04 | `test_rejects_float` | a float volume is rejected | FR3, FR7 |
| TC-VOL-05 | `test_rejects_size_1024` | a size of 1024 is rejected | FR5, FR7 |
| TC-VOL-06 | `test_accepts_size_1023` | a size of 1023 is accepted | FR5 |
| TC-VOL-07 | `test_rejects_garbage` | a file that is not NRRD gives a clear `ValueError` | FR7 |
| TC-VOL-08 | `test_missing_file` | a missing file gives `FileNotFoundError` | FR7 |

### Plane validation: `test_plane.py`

| ID | Test | Checks | Requirements |
|---|---|---|---|
| TC-PL-01 | `test_valid_triangle_has_a1_equal_a2` | a valid triangle is stored as a trapezoid with `a1 = a2` | FR16, FR24 |
| TC-PL-02 | `test_valid_trapezoid` | a valid trapezoid is accepted | FR18 to FR21 |
| TC-PL-03 | `test_tolerance_within_eps_is_valid` | legs that differ by less than EPS are accepted | FR18 |
| TC-PL-04 | `test_invalid_triangles` × 4 | not isosceles (clearly, and just over EPS), all points equal, collinear | FR16, FR17, FR22 |
| TC-PL-05 | `test_invalid_trapezoids` × 5 | not isosceles, top base longer than bottom, not on one plane, degenerate, collinear | FR18 to FR22 |
| TC-PL-06 | `test_sample_csv_rows` | the rows of the sample plane list [Ex0.csv](../Ex0.csv): rows 1, 2, 4 valid, row 3 not isosceles | FR11, FR12, FR16, FR18 |
| TC-PL-07 | `test_row4_invalid_in_alternative_order` | sample row 4 read in the alternative order (a1, a2, b, c) is invalid, supporting DD2 | FR12 |
| TC-PL-08 | `test_largest_plane_is_valid` | a 2048 × 2048 plane is accepted | FR42 |
| TC-PL-09 | `test_too_large` × 3 | legs or base over 2048 voxels are rejected as too large | FR42 |

### CSV reading: `test_csv_reader.py`

| ID | Test | Checks | Requirements |
|---|---|---|---|
| TC-CSV-01 | `test_sample_csv` | `Ex0.csv` gives rows 1 to 4, valid/valid/invalid/valid, with the reason for row 3 | FR8, FR9, FR13, FR14 |
| TC-CSV-02 | `test_excel_export_format` | a file with a BOM and CRLF line endings (Excel export) is read | FR8, FR9 |
| TC-CSV-03 | `test_invalid_rows` × 7 | invalid N, non-number, missing value, too few and too many values, `nan`, invalid plane; each with its reason | FR14, FR22 |
| TC-CSV-04 | `test_decimals_negatives_and_float_n` | decimal and negative coordinates, N written as `3.0` | FR10 |
| TC-CSV-05 | `test_blank_lines_skipped_but_row_numbers_kept` | blank lines give no result; row numbers still match the file | FR9, FR14 |
| TC-CSV-06 | `test_header_only` | a file with only a header is a fatal error | FR15 |
| TC-CSV-07 | `test_missing_file` | a missing file gives `FileNotFoundError` | FR15 |
| TC-CSV-08 | `test_binary_file` | a binary (Excel) file gives a clear "not a text CSV file" error | FR15 |

### Sampling: `test_sampler.py`

| ID | Test | Checks | Requirements |
|---|---|---|---|
| TC-SMP-01 | `test_nearest_voxel` | the value of the nearest voxel | FR30 |
| TC-SMP-02 | `test_outside_is_zero` | points outside the volume give 0 and are marked outside | FR23, FR30 |
| TC-SMP-03 | `test_keeps_dtype` | the values keep the volume's type | FR33 |
| TC-SMP-04 | `test_sampler_is_abstract` | `Sampler` itself cannot be created | NFR12 |
| TC-SMP-05 | `test_trilinear_at_voxel_centers_equals_nearest` | trilinear equals the voxel at voxel centers | NFR12 |
| TC-SMP-06 | `test_trilinear_is_exact_on_linear_volume` | oracle: on `x + 2y + 3z`, 1000 random points are exact | NFR12 |
| TC-SMP-07 | `test_trilinear_midpoint` | the center of a cube is the average of its 8 corners | NFR12 |
| TC-SMP-08 | `test_trilinear_outside_and_edges` | the last voxel and an axis of size 1 are inside; points just outside are 0 | NFR12 |

### Projection: `test_projector.py`

| ID | Test | Checks | Requirements |
|---|---|---|---|
| TC-PRJ-01 | `test_oracle_axis_aligned_rectangle` | oracle: a rectangle in the plane `z = k` gives exactly `M[:, :, k]`, all pixels sampled | FR25 to FR32 |
| TC-PRJ-02 | `test_output_size` | E and mask have the size `floor(Dab) + 1` × `ceil(Dbc) + 1` | FR26 |
| TC-PRJ-03 | `test_apex_is_sampled` | row 0 of a triangle is one pixel, in the center column, with the apex value | FR27, FR28, DD6, DD7 |
| TC-PRJ-04 | `test_triangle_rows_are_centered` | every row is centered on the same column | FR29 |
| TC-PRJ-05 | `test_plane_outside_volume_is_empty` | a plane fully outside gives an empty mask and a zero image | FR23, FR30, FR31 |
| TC-PRJ-06 | `test_partly_outside` | only pixels inside the volume are marked as sampled | FR30, FR31, FR37 |
| TC-PRJ-07 | `test_keeps_dtype` | E has the volume's type | FR33 |
| TC-PRJ-08 | `test_sampler_is_injected` | with a fake sampler that always returns 7, every sampled pixel is 7 | NFR11, NFR12 |
| TC-PRJ-09 | `test_matches_row_loop_triangles` × 4 | vectorized equals row loop: axis-aligned, oblique, partly outside, smaller than one voxel | FR24 to FR32 |
| TC-PRJ-10 | `test_matches_row_loop_trapezoids` × 3 | vectorized equals row loop: rectangle, non-parallel bases, oblique | FR24 to FR32 |
| TC-PRJ-11 | `test_oracle_with_trilinear_sampler` | the axis-aligned oracle also holds with `TrilinearSampler` | NFR12 |
| TC-PRJ-12 | `test_performance_500_cubed` (marked `performance`) | average of 50 projections of a 559 × 501 triangle on a random 500³ `uint8` volume is at least 30 fps (measured about 167 fps) | NFR1, NFR3 |

### Normalization: `test_normalizer.py`

| ID | Test | Checks | Requirements |
|---|---|---|---|
| TC-NRM-01 | `test_global_scale_signed` | −100, 0, 50, 100 on a −100..100 volume give 0, 127, 191, 255 | FR36 |
| TC-NRM-02 | `test_background_is_black` | pixels outside the mask are 0 even when Mmin < 0 | FR37 |
| TC-NRM-03 | `test_constant_volume` | Mmax = Mmin maps everything to 0 | FR36 |
| TC-NRM-04 | `test_uint32_no_overflow` | the full `uint32` range maps to 0 and 255 | FR3, FR36 |

### Video writing: `test_video_writer.py`

| ID | Test | Checks | Requirements |
|---|---|---|---|
| TC-VID-01 | `test_even_size_and_frame_count` | odd sizes rounded up to even; frame count; codec H.264; 10 fps | FR34, FR35, FR38, FR39 |
| TC-VID-02 | `test_padding_centered_top_aligned` | a small image is centered horizontally and aligned to the top, black around it | FR38 |
| TC-VID-03 | `test_error_frame_not_black` | error frames are drawn, also with a reason too long for one line | FR41 |
| TC-VID-04 | `test_unwritable_path` | a folder that does not exist gives a clear `OSError` | FR40 |
| TC-VID-05 | `test_write_failure_mid_video` | an error while writing a frame (for example a full disk) gives a clear `OSError` | FR40 |

### Command line, end to end: `test_ex0.py`

These run on a synthetic 300³ `uint16` NRRD file.

| ID | Test | Checks | Requirements |
|---|---|---|---|
| TC-CLI-01 | `test_sample_csv_one_frame_per_row` | `Ex0.csv`: exit 0, **4 frames**, warning for row 3, projection time and fps printed | FR13, FR22, FR35, FR43 |
| TC-CLI-02 | `test_huge_plane_becomes_error_frame` | a plane 10,000,000 voxels long next to a normal plane: exit 0, 2 frames, "too large" warning | FR42, DD3 |
| TC-CLI-03 | `test_all_rows_invalid` | every row invalid: exit 0, one error frame per row (default frame size) | FR14, FR35, FR38 |
| TC-CLI-04 | `test_usage` × 2 | wrong number of arguments: exit 2 | NFR9 |
| TC-CLI-05 | `test_missing_inputs` | missing NRRD or CSV: exit 1 | FR7, FR15 |
| TC-CLI-06 | `test_unwritable_output` | output folder missing: exit 1 | FR40 |
| TC-CLI-07 | `test_command_line_as_a_process` | `python Ex0.py file.nrrd file.csv file.mp4` as a separate process: exit 0, video written; no arguments: exit 2 | NFR9 |
| TC-CLI-08 | `test_same_input_same_video` | two runs on the same input produce the same frames | NFR6 |

### Manual test procedures

Some properties are visual and are checked by a person.

| ID | Steps | Expected result | Requirements |
|---|---|---|---|
| TC-MAN-01 | `python Ex0.py data/MRHead_1.nrrd Ex0.csv out.mp4`, open `out.mp4` | 4 frames; frames 1, 2 and 4 show parts of the head (mostly black, the planes are sized for a 500³ volume); frame 3 is black with a white X, "Invalid plane: row 3" and "not isosceles: ..." | FR35, FR41 |
| TC-MAN-02 | `python Ex0.py data/<volume>.nrrd experiments/rotation.csv out.mp4` for each of the 4 dataset volumes | 60 frames; the plane turns smoothly. MRHead: sagittal view at frame 0, axial view through the eyes at frame 30. Onion: rings become circles. Swiss roll: the spiral becomes straight layers. | FR1 to FR3, FR6, FR24 to FR33 |
| TC-MAN-03 | Run the program on each dataset volume (int16, uint8, uint16, uint32) | each loads and runs, exit 0, the printed type matches the table in the README | FR1, FR3 |
| TC-MAN-04 | `python -m experiments.benchmark` | the 500³ rows are all above 30 fps; the printed tables match [EXPERIMENT.md](EXPERIMENT.md) within a few percent | NFR1 to NFR3 |

The last results of these procedures are in [EXPERIMENT.md](EXPERIMENT.md).

## 7. Requirements traceability

Every requirement and how it is verified. "Review" means it is checked by reading the design or code, not by a test.

| Requirement | Verified by |
|---|---|
| FR1 (single-file NRRD) | TC-VOL-01, TC-MAN-03 |
| FR2 (raw/gzip, both byte orders) | Not by an automated test, see §9 |
| FR3 (8/16/32-bit integer types) | TC-VOL-01, TC-VOL-02, TC-VOL-04, TC-NRM-04, TC-MAN-03 |
| FR4 (dimension 3) | TC-VOL-03 |
| FR5 (sizes 1 to 1023) | TC-VOL-05, TC-VOL-06 |
| FR6 (space directions ignored) | Review: no code reads these fields; TC-MAN-02 on MRHead, whose header has them |
| FR7 (input errors) | TC-VOL-03 to TC-VOL-08, TC-CLI-05 |
| FR8 (header row skipped) | TC-CSV-01, TC-CSV-02 |
| FR9 (row format, empty cells, blank lines) | TC-CSV-01, TC-CSV-02, TC-CSV-05 |
| FR10 (decimals, negatives) | TC-CSV-04 |
| FR11 (triangle order) | TC-PL-06 |
| FR12 (trapezoid order) | TC-PL-06, TC-PL-07 |
| FR13 (CSV order) | TC-CSV-01, TC-CLI-01 |
| FR14 (bad rows) | TC-CSV-01, TC-CSV-03, TC-CSV-05, TC-CLI-03 |
| FR15 (missing/empty/non-text CSV) | TC-CSV-06, TC-CSV-07, TC-CSV-08, TC-CLI-05 |
| FR16 (triangle isosceles) | TC-PL-01, TC-PL-04, TC-PL-06 |
| FR17 (triangle not degenerate) | TC-PL-04 |
| FR18 (trapezoid isosceles) | TC-PL-02, TC-PL-03, TC-PL-05, TC-PL-06 |
| FR19 (top base ≤ bottom base) | TC-PL-05 |
| FR20 (same plane) | TC-PL-05 |
| FR21 (trapezoid not degenerate) | TC-PL-05 |
| FR22 (invalid plane raises, error frame) | TC-PL-04, TC-PL-05, TC-CSV-03, TC-CLI-01 |
| FR23 (planes outside the volume are valid) | TC-SMP-02, TC-PRJ-05 |
| FR24 (triangle as trapezoid) | TC-PL-01, TC-PRJ-09, TC-PRJ-10 |
| FR25 (Dab, Dbc, v1, v2) | TC-PRJ-01, TC-PRJ-09, TC-PRJ-10 |
| FR26 (output size) | TC-PRJ-02 |
| FR27 (row endpoints, apex row) | TC-PRJ-03 |
| FR28 (samples per row, zero-width row) | TC-PRJ-03, TC-PRJ-09 |
| FR29 (centered rows) | TC-PRJ-04 |
| FR30 (nearest voxel, 0 outside) | TC-SMP-01, TC-SMP-02, TC-PRJ-05, TC-PRJ-06 |
| FR31 (pixels outside the shape are 0) | TC-PRJ-05, TC-PRJ-06 |
| FR32 (E[y][x]) | TC-PRJ-01 |
| FR33 (same type as M) | TC-SMP-03, TC-PRJ-07 |
| FR34 (H.264 MP4) | TC-VID-01 |
| FR35 (one frame per row) | TC-VID-01, TC-CLI-01, TC-CLI-03 |
| FR36 (global normalization) | TC-VOL-02, TC-NRM-01, TC-NRM-03, TC-NRM-04 |
| FR37 (black background) | TC-NRM-02, TC-PRJ-06 |
| FR38 (uniform even frame size, padding) | TC-VID-01, TC-VID-02, TC-CLI-03 |
| FR39 (10 fps) | TC-VID-01 |
| FR40 (output not writable) | TC-VID-04, TC-VID-05, TC-CLI-06 |
| FR41 (error frame) | TC-VID-03, TC-MAN-01 |
| FR42 (plane size limit) | TC-PL-08, TC-PL-09, TC-CLI-02 |
| FR43 (timing output) | TC-CLI-01 |
| NFR1 (≥ 30 fps on 500³) | TC-PRJ-12, TC-MAN-04 |
| NFR2 (target 100 fps) | Experiment ([EXPERIMENT.md](EXPERIMENT.md)): met for triangles, not for full 500×500 rectangles |
| NFR3 (how performance is measured) | TC-PRJ-12, [experiments/benchmark.py](../experiments/benchmark.py) |
| NFR4 (volume loaded once, frames streamed) | Review: [DESIGN.md](DESIGN.md) §4; the frame size comes from `Projector.output_size` before the first frame |
| NFR5 (no unhandled exception) | Every error-path test above; TC-CLI-02 to TC-CLI-06; last-resort handler in `Ex0.py` |
| NFR6 (deterministic) | TC-CLI-08 |
| NFR7 (Python 3.12+, macOS, Linux, Windows) | CI on all three operating systems |
| NFR8 (dependencies listed) | CI installs only from `requirements.txt` |
| NFR9 (command line) | TC-CLI-04, TC-CLI-07 |
| NFR10 (separate components) | One test file per component; each runs on its own |
| NFR11 (projection independent of file formats) | TC-PRJ-01 to TC-PRJ-11 use plain NumPy arrays; TC-PRJ-08 |
| NFR12 (replaceable sampling) | TC-SMP-04 to TC-SMP-08, TC-PRJ-08, TC-PRJ-11 |

## 8. Code coverage

Measured with `pytest --cov` (pytest-cov, settings in [.coveragerc](../.coveragerc)), line and branch coverage of `projection/` and `Ex0.py`:

| Module | Statements | Branches | Coverage |
|---|---|---|---|
| `Ex0.py` | 59 | 14 | 100% |
| `projection/csv_reader.py` | 61 | 18 | 100% |
| `projection/normalizer.py` | 13 | 2 | 100% |
| `projection/plane.py` | 54 | 18 | 100% |
| `projection/projector.py` | 63 | 4 | 100% |
| `projection/sampler.py` | 30 | 0 | 100% |
| `projection/video_writer.py` | 70 | 10 | 100% |
| `projection/volume.py` | 27 | 8 | 100% |
| **Total** | **377** | **74** | **100%** |

The small `if __name__ == "__main__":` example at the bottom of each module is excluded: it is a manual example, not part of the program. Full coverage shows that every line and branch runs in some test; it does not by itself show that every result is checked, which is what the test cases above are for.

## 9. Known limitations

- **FR2, `raw` encoding and big-endian files** are handled by pynrrd but not tested here: all test and sample files are gzip and little-endian.
- **The performance test depends on the machine.** On a slow or busy machine it could fail without a real regression; it is marked `performance` so it can be run separately. The measured value on the development machine (about 167 fps) is far above the 30 fps limit.
- **Visual quality** (TC-MAN-01, TC-MAN-02) is checked by a person, not automatically.
