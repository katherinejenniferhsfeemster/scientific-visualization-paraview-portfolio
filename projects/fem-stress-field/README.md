# FEM stress field visualization

End-to-end demonstration of how to take a finite-element solution
(unstructured mesh + tensor field) into ParaView for stress analysis.

## What this shows

- Construction of a notched-cantilever beam mesh, tetrahedralized to ~78k cells
- Synthetic but mechanically consistent stress field
  (My/I + shear distribution + Kt-style notch concentration)
- Per-point von Mises invariant
- Export to `.vtu` (XML unstructured grid, binary)
- Two renders:
  - Surface colored by von Mises with 5–95 percentile clipping
  - Warped-by-displacement view (cantilever bending shape)

## Why the percentile clip matters

A naive `mapper.SetScalarRange(arr.GetRange())` lets the singular peak at
the notch saturate the entire colormap. The 5–95 percentile clip keeps the
field readable while still highlighting the concentration zone.

## Pipeline

```
hex grid (vtkImageData) ──► extract cells (drop notch) ──► tetrahedralize
                                                       │
synthetic σ_ij + u(x) attached to points ◄─────────────┘
                                                       │
                                                       ├──► vtkXMLUnstructuredGridWriter
                                                       ├──► vtkDataSetSurfaceFilter ──► colored render
                                                       └──► vtkWarpVector ──► render
```

## Files

| Path                                       | Purpose                              |
|--------------------------------------------|--------------------------------------|
| `scripts/python/fem_stress_field.py`       | Mesh, fields, both renders           |
| `assets/data/notched_beam.vtu`             | 78,300 tets, σ_xx / τ_xy / vM / disp |
| `assets/renders/von_mises.png`             | Surface colored by von Mises         |
| `assets/renders/warp_by_vector.png`        | Warp filter (deflected shape)        |

[← back to portfolio](../../README.md)
