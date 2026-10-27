# Software Requirements Specification

## 1. Introduction
### 1.1 Purpose

This document specifies the requirments for a system that computes 2D Projections (cross-sections) of a 3D Volume along arbitrary planes and renders a sequence of such projections as a video
### 1.2 Definitions

Volume (M) - a 3D Matrix of size sx * sy * sz, where 1 <= sx, sy, sz < 2^10. Each entry M[x][y][z] is an integer value of 8, 16 or 32 bits.
Voxel - a Single entry M[x][y][z] of the volume.
Voxel index coordinates - a 3D Coordinate system where (x, y, z) refers directly to M[x][y][z]. None integers values fall between voxels.
Plane (p) - a Planar region in voxel index coordinates, defined by 3 points for triangles or 4 points for trapezoids.
Triangle plane - 3 points (a, b, c) with |dist(a,b) - dist(a, c) < EPS.
Trapezoid plane - 4 points (a1, a2, b, c) with |dist(a1,b) - dist(a2, c) < EPS and |dist(a1, a2) <= dist(b, c), all on the same plane.
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
- FR7: If the file is missing, malformed or violates FR3 to FR5, the system shall print a clear error and exit with a none zero exit code, without crashing.

### 2.2 Input: CSV

- FR8: The system shall read a CSV file whose first row is a header row, which is skipped.
- FR9: Each following row shall define one plane: the first value is the number of points N (3 or 4), followed by 3·N coordinates `x1, y1, z1, ..., xN, yN, zN`. Empty trailing cells are ignored.
- FR10; Coordinates may be integers or decimals, and may be negative or outside the volume bounds.
- FR11: For N = 3, the points are interpreted as (a, b, c), where a is the apex.
- FR12: For N = 4, the points are interpreted as (a1, b, a2, c): two segments a1→b and a2→c.
- FR13: The planes shall be processed in the order they appear in the file.
- FR14: A row with an invalid N, a missing value or a non-numeric value shall be reported with its row number and skipped.
- FR15: If the file is missing or contains no valid rows, the system shall print a clear error message and exit with a non-zero exit code.

### 2.3 Plane validation

- FR16: A triangle plane (a, b, c) is valid only if |dist(a,b) - dist(a,c)| < EPS.
- FR17: A triangle plane is valid only if it is non-degenerate: dist(a,b) > EPS and the points a, b, c are not collinear.
- FR18: A trapezoid plane (a1, b, a2, c) is valid only if |dist(a1,b) - dist(a2,c)| < EPS.
- FR19: A trapezoid plane is valid only if dist(a1,a2) <= dist(b,c) + EPS.
- FR20: A trapezoid plane is valid only if all four points lie on the same plane: the distance of a2 from the plane through a1, b, c is less than EPS.
- FR21: A trapezoid plane is valid only if it is non-degenerate: dist(a1,b) > EPS and a1, b, c are not collinear.
- FR22: A plane that fails validation shall be reported with its row number and the failed condition, and skipped.
- FR23: A plane that lies partially or fully outside the volume is valid; it is not rejected by validation.

### 2.4 Projection

- FR24: A triangle plane (a, b, c) shall be treated as a trapezoid plane with a1 = a2 = a. All following requirements are defined for the trapezoid case (a1, b, a2, c).
- FR25: Let Dab = dist(a1, b) and Dbc = dist(b, c). Let v1 = (b - a1) / Dab and v2 = (c - a2) / Dab.
- FR26: The output image E shall have H = floor(Dab) + 1 rows and W = ceil(Dbc) + 1 columns.
- FR27: For each row y = 0 .. H-1, the row endpoints shall be p1(y) = a1 + y·v1 and p2(y) = a2 + y·v2. Row 0 lies on a1→a2 (the apex, for a triangle).
- FR28: Let d12 = dist(p1(y), p2(y)). If d12 >= EPS, the row shall be sampled at points p = p1(y) + x1·dp for x1 = 0 .. floor(d12), where dp = (p2(y) - p1(y)) / d12. If d12 < EPS, the row shall be sampled only at p1(y).
- FR29: Each sample shall be written to column x = round(Dbc/2 - d12/2 + x1), so every row is centered horizontally.
- FR30: Sampling shall use nearest-neighbor: the value of the voxel at round(p). If round(p) is outside the volume, the value is 0.
- FR31: Pixels of E that are not written by FR28 to FR29 (outside the triangle or trapezoid) shall be 0.
- FR32: E shall be indexed as E[y][x] (row, column), with row 0 at the a1→a2 side.
- FR33: E shall have the same data type as M. Conversion to 8-bit is done only in the output stage (2.5).

### 2.5 Output Video

- FR34: The system shall write an MP4 video (H.264 codec) to the output path given on the command line.
- FR35: The video shall contain one frame per valid plane, in the order of FR13.
- FR36: Each frame shall be converted to 8-bit grayscale using a global linear normalization over the whole volume: v8 = round(255 · (v - Mmin) / (Mmax - Mmin)), where Mmin and Mmax are the minimum and maximum values of M. If Mmax = Mmin, all values map to 0.
- FR37: Background pixels (set to 0 by FR30 and FR31) shall be black in the output frame, regardless of FR36.
- FR38: All frames shall have the same size: the maximum width and maximum height of all projections, rounded up to an even number. Each projection shall be placed centered horizontally and aligned to the top, with the remaining area filled with black.
- FR39: The video frame rate shall be 10 frames per second by default.
- FR40: If the output file cannot be written, the system shall print a clear error message and exit with a non-zero exit code.

## 3. Non-Functional Requirements

### 3.1 Performance

- NFR1: Projecting a single plane on a 500×500×500 volume shall run at a minimum of 30 frames per second.
- NFR2: The target performance for NFR1 is 100 frames per second or more.
- NFR3: Performance shall be measured on the projection step only (excluding file reading, normalization and video encoding), as the average over at least 50 runs, on a stated reference machine.
- NFR4: The volume shall be loaded into memory once. Frames shall be written to the video as they are produced, and not all kept in memory at once.

### 3.2 Robustness

- NFR5: The system shall not terminate with an unhandled exception for any input; all errors are reported as defined in FR7, FR14, FR15, FR22 and FR40.
- NFR6: The system shall be deterministic: the same input files always produce the same output video.

### 3.3 Portability

- NFR7: The system shall run on Python 3.10 or newer, on macOS, Linux and Windows.
- NFR8: All third-party dependencies shall be listed in `requirements.txt`.
- NFR9: The system shall be run with the command `python Ex0.py file.nrrd file.csv file.mp4`.

### 3.4 Maintainability

- NFR10: Reading input, plane validation, projection, normalization and video writing shall be implemented as separate components, each testable on its own.
- NFR11: The projection component shall work on any 3D array and shall not depend on the NRRD or CSV formats.
- NFR12: The sampling method (FR30) shall be replaceable, for example with trilinear interpolation, without changing the projection component.

## 4. Design Decisions

Each decision resolves an ambiguity in the assignment or a problem in the given algorithm.

### DD1: Voxel index coordinates (FR6, FR10)
- Decision: Plane points are in voxel index coordinates; `space directions` and `space origin` are ignored.
- Rationale: The problem defines M as a matrix with integer indices (`0 <= x < sx`), the algorithm accesses `M[p]` directly, and the sample CSV contains integer index-range values.
- Alternative: Physical (mm) coordinates. Rejected as out of scope; the cost is slight distortion on volumes with non-uniform spacing.

### DD2: Trapezoid point order (FR12)
- Decision: The 4 points are read as (a1, b, a2, c).
- Rationale: The assignment describes the trapezoid as two vectors a'→b and a''→c, and row 4 of the sample CSV is a valid trapezoid only in this order.
- Note: This differs from the order (a1, a2, b, c) given in the Q&A.

### DD3: Invalid rows and planes are skipped (FR14, FR22)
- Decision: An invalid row is reported with its row number and the reason, and skipped.
- Alternatives: Stop the program, or output a black frame. Rejected: one bad row should not prevent the video from being created, and a black frame would hide the error.

### DD4: Plane validation (FR16 to FR21)
- Decision: All geometric comparisons use the tolerance EPS. "Same plane" is checked as the distance of a2 from the plane through a1, b, c. Degenerate planes (collinear or coinciding points) are rejected. Trapezoid bases are not required to be parallel.
- Rationale: Exact comparison of floating-point values is unreliable, and degenerate planes cause division by zero in the algorithm. Parallel bases are not required by the Q&A, and the algorithm works without them.

### DD5: A triangle is a trapezoid with a1 = a2 (FR24)
- Decision: One algorithm handles both plane types.
- Rationale: Avoids duplicated code and keeps both cases consistent.

### DD6: The apex is sampled (FR27)
- Decision: Row y uses p1(y) = a1 + y·v1, so row 0 is the apex.
- Rationale: The given algorithm advances a1 and a2 before sampling, so the apex is never sampled.

### DD7: Rows of zero width (FR28)
- Decision: If d12 < EPS, only one point is sampled.
- Rationale: The given algorithm divides by d12, which is 0 at the apex.

### DD8: Output size (FR26)
- Decision: H = floor(Dab) + 1, W = ceil(Dbc) + 1.
- Rationale: The algorithm defines E as Dab × Dbc, but both are real numbers. H covers rows 0 to floor(Dab) without passing b; W fits the widest centered row.

### DD9: Nearest-neighbor sampling (FR30)
- Decision: The value of the nearest voxel is used.
- Rationale: Simplest and fastest; matches `M[p]` in the given algorithm.
- Alternative: Trilinear interpolation, which is smoother but slower. Supported as a future option through NFR12.

### DD10: E is indexed as E[y][x] (FR32)
- Decision: Row first, then column.
- Rationale: The given algorithm writes `E[x][y]`, but image and video libraries expect `[row][column]`.

### DD11: Global normalization, black background (FR3, FR36, FR37)
- Decision: Values are scaled to 0 to 255 by the minimum and maximum of the whole volume. Background is always black.
- Rationale: Per-frame normalization would make the same tissue change brightness between frames. Signed voxel types are supported because the reference MRI file is signed 16-bit, although the assignment specifies unsigned; with signed data Mmin can be negative, so 0 would otherwise map to gray.

### DD12: Uniform frame size by padding (FR38)
- Decision: Each frame is padded with black to the largest projection size, rounded up to even.
- Alternative: Resizing. Rejected: it changes the scale between frames.
- Rationale: MP4 requires all frames to have the same size; H.264 requires even dimensions.