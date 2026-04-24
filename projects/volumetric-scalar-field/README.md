# Volumetric scalar field — atmospheric plume

Reference setup for direct volume rendering of a 3D scalar field, the
canonical workload for ParaView in atmospheric, medical, and astrophysics
contexts.

## What this shows

- Procedural plume model: gaussian source advected in +x by a vertical
  shear, multiplied by a low-altitude stratification term
- 96³ structured grid exported as `.vti`
- Two GPU-friendly views:
  - Direct volume render with hand-tuned color + opacity transfer functions
  - Multiple isocontours at 0.15 / 0.35 / 0.65

## Designing the transfer function

The opacity ramp is intentionally non-linear:

| concentration | opacity  | meaning                                  |
|---------------|----------|------------------------------------------|
| 0.00 – 0.10   | 0.00     | clear air, fully transparent             |
| 0.30          | 0.40     | plume edge becomes visible               |
| 0.60          | 0.85     | dense plume body                         |
| 0.90 – 1.00   | 0.98+    | core, near-opaque                        |

Color ramp transitions teal → amber → ember to keep the
field perceptually ordered.

## Files

| Path                                       | Purpose                          |
|--------------------------------------------|----------------------------------|
| `scripts/python/volumetric_scalar.py`      | Field + both renders             |
| `scripts/pvpython/animate_volume.py`       | 60-frame ParaView turntable       |
| `assets/data/plume.vti`                    | 96³ scalar field                 |
| `assets/renders/volume_render.png`         | Direct volume rendering          |
| `assets/renders/isocontours.png`           | Three nested isosurfaces         |

[← back to portfolio](../../README.md)
