# Ex1 - 3D Model Scaling

Compute 2D Cross-sections as a 3D Medical volume along arbitrary planes, and render a sequance of such slices as a video

## Problem

Medical scanners such as MRIs and CTs produce a 3D volume: as stack of 2d images that together form a a 3D Matrix of intensity values. A screen can only show 2D images, so the volume is viewed as slices. Third party programs such as 3DSlicer Typically show Three-axis aligned slices but anatomical stactures are rarely aligned with the scanner's axes. To see such stractures properly the volume must be sliced along **arbitrary (oblique) plane**.
This project takes a 3D Volume and a plane defined by 3 or 4 points and computes the 2D image of the volume's cross-section on that plane. Given a list of Planes, it produces a video with one frame per plane.

The Algorithm must be fast enough for interactive use: atleast 30FPS (target is 100+ fps) for a 500*500*500 volume

## Scope

### In scope

- Reading 3D Volumes in NRRD format(8, 16 and 32bit integers voxels)
- Planes defined by:
    - **3 points** `(a, b, c)` forming an isosceles triangle: `|dist(a, b) - dist(a, c) < EPS`
    - **4 points** `(a1, a2, b, c)` forming an isosceles trapzoid: `|dist(a1, b) - dist(a2, c) < EPS`, `|dist(a1, a2) <= dist(b, c)`, all points on the same plane.
    - Input validation of planes(`EPS = 0.001`).
    - Projecting the volume onto each plane as a 2D image.
    - Writing all projected images to an MP4 Video, in the order given in the CSV
    - a Command-line demo(`Ex0.py`).

### Out of scope

- a Graphical / Interactive user friendly interface.
- Physical (mm) coordinates: plane points are given in **voxel index coordinates** *(as implied by the problem definition and the sample CSV)*.
- 3D rendering (volume rendering, surface rendering).
- File formats other than NRRD for input and MP4 for output.

## Input/Output

## How to run

```bash 
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 Ex0.py filename.nrrd file.csv file.mp4
```

## Project Stracture

*TBD*

## Performance

Measured on a synthetic 500*500*500 `uint8` volume, output image 500x599, average of 50 runs on a Macbook Pro 14" M5:
Naive using Python loops - ~28 FPS *(on a smaller 238x237 image)*
Inner Loops vectorized using Numpy - ~120 FPS

## Documentation

- `docs/SRS.MD`: Software Requirments Specifications *TBD*
- `docs/ALGORITHM.md`: Detailed algorithm design decisions *TBD*
- `docs/TESTING.md`: Testing strategy *TBD*
