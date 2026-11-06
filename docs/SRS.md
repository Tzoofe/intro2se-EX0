# Software Requirements Specification

## 1. Introduction
### 1.1 Purpose

This document specifies the requirements for a system that computes 2D Projections (cross-sections) of a 3D Volume along arbitrary planes and renders a sequence of such projections as a video
### 1.2 Definitions

Volume (M) - a 3D Matrix of size sx * sy * sz, where 1 <= sx, sy, sz < 2^10. Each entry M[x][y][z] is an integer value of 8, 16 or 32 bits.
Voxel - a Single entry M[x][y][z] of the volume.
Voxel index coordinates - a 3D Coordinate system where (x, y, z) refers directly to M[x][y][z]. Non-integer values fall between voxels.
Plane (p) - a Planar region in voxel index coordinates, defined by 3 points for triangles or 4 points for trapezoids.
Triangle plane - 3 points (a, b, c) with |dist(a,b) - dist(a,c)| < EPS.
Trapezoid plane - 4 points (a1, b, a2, c) with |dist(a1,b) - dist(a2,c)| < EPS and dist(a1,a2) <= dist(b,c), all on the same plane.
Projection (E) - The 2D images produced by sampling M along the plane p.
EPS - Tolerance for distance comparisons: 0.001.
Frame - a Single projection, written as one frame of the output video.

## 2. Functional Requirements
### 2.1 Input: NRRD
- FR1: The system shall read a 3D volume from a single NRRD file (`.nrrd`, header and data in the same file)
- FR2: The system shall support `raw` and `gzip` data-encodings, in both little and big endian byte order.
- FR3: The system shall support voxel types of 8, 16 and 32 bit integers, both signed and unsigned.
- FR4: The system shall accept only volumes with `dimension: 3`.
- FR5: The system shall accept only volumes where each size satisfies 1 <= s < 2^10.
- FR6: The system shall ignore `space directions` and `space origin` for the projection; all computation is done in voxel index coordinates.
- FR7: If the file is missing, malformed or violates FR3 to FR5, the system shall print a clear error and exit with a non-zero exit code, without crashing.

### 2.2 Input: CSV

- FR8: The system shall read a CSV file whose first row is a header row, which is skipped.
- FR9: Each following row shall define one plane: the first value is the number of points N (3 or 4), followed by 3·N coordinates `x1, y1, z1, ..., xN, yN, zN`. Empty trailing cells are ignored. Blank lines are skipped and do not produce a frame.
- FR10: Coordinates may be integers or decimals, and may be negative or outside the volume bounds.
- FR11: For N = 3, the points are interpreted as (a, b, c), where a is the apex.
- FR12: For N = 4, the points are interpreted as (a1, b, a2, c): two segments a1→b and a2→c.
- FR13: The planes shall be processed in the order they appear in the file.
- FR14: A row with an invalid N, a missing value, a non-numeric or non-finite value (nan, inf), or a wrong number of values for N shall be reported with its row number and the reason, and shall produce an error frame (FR41). Row numbers count data rows from 1.
- FR15: If the file is missing, is not a text file, or contains no data rows (only a header, or empty), the system shall print a clear error message and exit with a non-zero exit code.

### 2.3 Plane validation

- FR16: A triangle plane (a, b, c) is valid only if |dist(a,b) - dist(a,c)| < EPS.
- FR17: A triangle plane is valid only if it is non-degenerate: dist(a,b) > EPS and the points a, b, c are not collinear.
- FR18: A trapezoid plane (a1, b, a2, c) is valid only if |dist(a1,b) - dist(a2,c)| < EPS.
- FR19: A trapezoid plane is valid only if dist(a1,a2) <= dist(b,c) + EPS.
- FR20: A trapezoid plane is valid only if all four points lie on the same plane: the distance of a2 from the plane through a1, b, c is less than EPS.
- FR21: A trapezoid plane is valid only if it is non-degenerate: dist(a1,b) > EPS and a1, b, c are not collinear.
- FR22: A plane that fails validation shall raise an exception stating the failed condition. The CSV reader catches it and records the row number and the failed condition; the program reports it and produces an error frame (FR41).
- FR23: A plane that lies partially or fully outside the volume is valid; it is not rejected by validation.
- FR42: A plane whose legs or base are longer than 2048 voxels is invalid (too large), and is handled like any other invalid plane (FR22).

### 2.4 Projection

- FR24: A triangle plane (a, b, c) shall be treated as a trapezoid plane with a1 = a2 = a. All following requirements are defined for the trapezoid case (a1, b, a2, c).
- FR25: Let Dab = dist(a1, b) and Dbc = dist(b, c). Let v1 = (b - a1) / Dab and v2 = (c - a2) / Dab.
- FR26: The output image E shall have H = floor(Dab) + 1 rows and W = ceil(Dbc) + 1 columns.
- FR27: For each row y = 0 .. H-1, the row endpoints shall be p1(y) = a1 + y·v1 and p2(y) = a2 + y·v2. Row 0 lies on a1→a2 (the apex, for a triangle).
- FR28: Let d12 = dist(p1(y), p2(y)). If d12 >= EPS, the row shall be sampled at points p = p1(y) + x1·dp for x1 = 0 .. floor(d12), where dp = (p2(y) - p1(y)) / d12. If d12 < EPS, the row shall be sampled only at p1(y).
- FR29: Each sample shall be written to column x = round(Dbc/2 - d12/2 + x1), so every row is centered horizontally.
- FR30: Sampling shall use nearest-neighbor: the value of the voxel at round(p) (exact halves round to the nearest even integer). If round(p) is outside the volume, the value is 0.
- FR31: Pixels of E that are not written by FR28 to FR29 (outside the triangle or trapezoid) shall be 0.
- FR32: E shall be indexed as E[y][x] (row, column), with row 0 at the a1→a2 side.
- FR33: E shall have the same data type as M. Conversion to 8-bit is done only in the output stage (2.5).

### 2.5 Output Video

- FR34: The system shall write an MP4 video (H.264 codec) to the output path given on the command line.
- FR35: The video shall contain exactly one frame per CSV data row, in the order of FR13: the projection for a valid plane, or an error frame (FR41) for an invalid row or plane.
- FR36: Each frame shall be converted to 8-bit grayscale using a global linear normalization over the whole volume: v8 = round(255 · (v - Mmin) / (Mmax - Mmin)), where Mmin and Mmax are the minimum and maximum values of M. If Mmax = Mmin, all values map to 0.
- FR37: Background pixels (set to 0 by FR30 and FR31) shall be black in the output frame, regardless of FR36.
- FR38: All frames shall have the same size: the maximum width and maximum height of all projections, rounded up to an even number. Each projection shall be placed centered horizontally and aligned to the top, with the remaining area filled with black. If there are no valid planes, the frame size shall be 256×256.
- FR39: The video frame rate shall be 10 frames per second by default.
- FR40: If the output file cannot be written, the system shall print a clear error message and exit with a non-zero exit code.
- FR41: An error frame shall be a black frame of the uniform size (FR38) with a white X across it, the text "Invalid plane: row N" and the reason, so the failed row and its cause are visible in the video.
- FR43: After a run, the program shall print the volume's size, type and load time, the average projection time per plane (and fps), and the total time to write the video.

## 3. Non-Functional Requirements

### 3.1 Performance

- NFR1: Projecting a single plane on a 500×500×500 volume shall run at a minimum of 30 frames per second.
- NFR2: The target performance for NFR1 is 100 frames per second or more.
- NFR3: Performance shall be measured on the projection step only (excluding file reading, normalization and video encoding), as the average over at least 50 runs, on a stated reference machine.
- NFR4: The volume shall be loaded into memory once. Frames shall be written to the video as they are produced, and not all kept in memory at once.

### 3.2 Robustness

- NFR5: The system shall not terminate with an unhandled exception for any input; all errors are reported as defined in FR7, FR14, FR15, FR22, FR40 and FR41.
- NFR6: The system shall be deterministic: the same input files always produce the same output video.

### 3.3 Portability

- NFR7: The system shall run on Python 3.12 or newer, on macOS, Linux and Windows.
- NFR8: All third-party dependencies shall be listed in `requirements.txt`.
- NFR9: The system shall be run with the command `python Ex0.py file.nrrd file.csv file.mp4`. With a wrong number of arguments, the system shall print a usage message and exit with code 2.

### 3.4 Maintainability

- NFR10: Reading input, plane validation, projection, normalization and video writing shall be implemented as separate components, each testable on its own.
- NFR11: The projection component shall work on any 3D array and shall not depend on the NRRD or CSV formats.
- NFR12: The sampling method (FR30) shall be replaceable, for example with trilinear interpolation, without changing the projection component.

## 4. Design Decisions

Each decision resolves an ambiguity in the problem specification or a problem in the original algorithm ([ALGORITHM.md](ALGORITHM.md) §2).

### DD1: Voxel index coordinates (FR6, FR10)
- Decision: Plane points are in voxel index coordinates; `space directions` and `space origin` are ignored.
- Rationale: The problem defines M as a matrix with integer indices (`0 <= x < sx`), the algorithm accesses `M[p]` directly, and the sample CSV contains integer index-range values.
- Alternative: Physical (mm) coordinates. Rejected as out of scope; the cost is slight distortion on volumes with non-uniform spacing.

### DD2: Trapezoid point order (FR12)
- Decision: The 4 points are read as (a1, b, a2, c).
- Rationale: The problem specification describes the trapezoid by its two legs, a'→b and a''→c, so each leg's endpoints are listed together. Row 4 of the sample plane list is a valid trapezoid only in this order.
- Alternative: (a1, a2, b, c), listing the top base first. Rejected: sample row 4 is invalid in this order.

### DD3: Invalid rows and planes produce an error frame (FR14, FR22, FR35, FR41)
- Decision: Plane validation raises an exception. The CSV reader records it with the row number and the reason, and the program writes an error frame in place of the projection; all other rows are processed normally.
- Rationale: An invalid plane is an error and must be reported, but one bad row should not cost the whole video. Keeping one frame per row preserves the mapping between CSV row i and video frame i, and makes the error visible in the output instead of hiding it.
- Alternatives: Stop the program (one bad row should not prevent the video), or skip the row silently (breaks the row↔frame mapping and hides the error). Both rejected.

### DD4: Plane validation (FR16 to FR21)
- Decision: All geometric comparisons use the tolerance EPS. "Same plane" is checked as the distance of a2 from the plane through a1, b, c. Degenerate planes (collinear or coinciding points) are rejected. Trapezoid bases are not required to be parallel.
- Rationale: Exact comparison of floating-point values is unreliable, and degenerate planes cause division by zero in the algorithm. Parallel bases are not required by the problem specification, and the algorithm works without them.

### DD5: A triangle is a trapezoid with a1 = a2 (FR24)
- Decision: One algorithm handles both plane types.
- Rationale: Avoids duplicated code and keeps both cases consistent.

### DD6: The apex is sampled (FR27)
- Decision: Row y uses p1(y) = a1 + y·v1, so row 0 is the apex.
- Rationale: The original algorithm advances a1 and a2 before sampling, so the apex is never sampled.

### DD7: Rows of zero width (FR28)
- Decision: If d12 < EPS, only one point is sampled.
- Rationale: The original algorithm divides by d12, which is 0 at the apex.

### DD8: Output size (FR26)
- Decision: H = floor(Dab) + 1, W = ceil(Dbc) + 1.
- Rationale: The algorithm defines E as Dab × Dbc, but both are real numbers. H covers rows 0 to floor(Dab) without passing b; W fits the widest centered row.

### DD9: Nearest-neighbor sampling (FR30)
- Decision: The value of the nearest voxel is used.
- Rationale: Simplest and fastest; matches `M[p]` in the original algorithm.
- Alternative: Trilinear interpolation, which is smoother but slower. It is implemented as a second sampler (`TrilinearSampler`) through NFR12 and compared in the experiment: it is about 2.5 times slower, and the images differ by only 2.6 to 4.0 gray levels on average, so nearest-neighbor stays the default.

### DD10: E is indexed as E[y][x] (FR32)
- Decision: Row first, then column.
- Rationale: The original algorithm writes `E[x][y]`, but image and video libraries expect `[row][column]`.

### DD11: Global normalization, black background (FR3, FR36, FR37)
- Decision: Values are scaled to 0 to 255 by the minimum and maximum of the whole volume. Background is always black.
- Rationale: Per-frame normalization would make the same tissue change brightness between frames. Signed voxel types are supported because the reference MRI file is signed 16-bit, although the problem specification describes unsigned values; with signed data Mmin can be negative, so 0 would otherwise map to gray.

### DD12: Uniform frame size by padding (FR38)
- Decision: Each frame is padded with black to the largest projection size, rounded up to even.
- Alternative: Resizing. Rejected: it changes the scale between frames.
- Rationale: MP4 requires all frames to have the same size; H.264 requires even dimensions.

### DD13: Maximum plane size (FR42)
- Decision: A plane with a leg or base longer than 2048 voxels is invalid.
- Rationale: The coordinates in the CSV are not limited (FR10), so a single row can describe a plane millions of voxels long. Its image would not fit in memory, and the whole run would fail with no video, which contradicts DD3. The longest line inside the largest allowed volume (1023³) is 1023·√3 ≈ 1772 voxels, so a longer plane can only add empty pixels; 2048 leaves a margin.
- Alternative: Clip the plane to the volume. Rejected: it changes the plane the user asked for, and the image size would no longer follow FR26.