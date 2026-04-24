# Turbulent flow visualization (Taylor-Green vortex)

Reference visualization of a 3D incompressible vortex field used as a
benchmark for CFD post-processing pipelines.

## What this shows

- Generation of an analytic 3D velocity field on a 64³ uniform grid
- Q-criterion derivation from velocity gradients (numpy + finite differences)
- Export to ParaView-native `.vti` (XML image data, binary)
- Two production-quality renders driven entirely from headless VTK:
  - Q-criterion isosurface for vortex core extraction
  - RK4 streamline integration with custom transfer function

## Files

| Path                                                            | Purpose                                  |
|-----------------------------------------------------------------|------------------------------------------|
| `scripts/python/taylor_green_vortex.py`                         | Field generation, Q-criterion, renders   |
| `scripts/pvpython/load_taylor_green.py`                         | ParaView batch script (state in code)    |
| `assets/data/taylor_green.vti`                                  | 64³ velocity + Q field                   |
| `assets/renders/q_isosurface.png`, `.../streamlines.png`        | Reference renders                        |

## Pipeline

```
analytic field   ─┐
                  ├──► vtkImageData ──► vtkXMLImageDataWriter (.vti)
Q = ½(‖Ω‖² − ‖S‖²)─┘                          │
                                              ├──► vtkContourFilter ──► render
                                              └──► vtkStreamTracer ──► tubes ──► render
```

## Reproducibility

```bash
pip install vtk numpy
python3 scripts/python/render_figures.py   # regenerates all three projects
```

[← back to portfolio](../../README.md)
