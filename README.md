# Scientific Visualization (ParaView) — Portfolio

Senior portfolio for a Scientific Visualization (ParaView) Specialist role.
Live site: **https://katherinejenniferhsfeemster.github.io/scientific-visualization-paraview-portfolio/**

Every figure on the live site is regenerated headlessly from VTK on every
push — no patient data, no proprietary solver outputs, no
commercial-license dependencies. Clone, install `vtk`, get the same PNGs.

## Projects

1. **[Turbulent flow visualization (Taylor-Green vortex)](projects/turbulent-flow-visualization/)** — analytic 3D vortex field, Q-criterion, RK4 streamlines, exported to `.vti`.
2. **[FEM stress field](projects/fem-stress-field/)** — notched-cantilever beam tetrahedralised to 78k cells, σ + displacement attached, von Mises and warp-by-vector renders, exported to `.vtu`.
3. **[Volumetric scalar field](projects/volumetric-scalar-field/)** — 96³ procedural atmospheric plume, GPU volume render with hand-tuned transfer function, isocontour view.
4. **[ParaView custom plugin](projects/paraview-custom-plugin/)** — server-manager XML proxy + Python module: vorticity magnitude + automatic top-N seed extraction for Stream Tracer With Custom Source.
5. **[Catalyst in-situ pipeline](projects/catalyst-in-situ/)** — Catalyst v2 adaptor with a toy time-stepping driver that contours, color-maps, and screenshots in-process.

## Repository layout

```
.
├── docs/                            # GitHub Pages site (style.css, index.html, assets/)
├── projects/                        # one README per project, links into scripts/ and assets/
│   ├── turbulent-flow-visualization/
│   ├── fem-stress-field/
│   ├── volumetric-scalar-field/
│   ├── paraview-custom-plugin/
│   └── catalyst-in-situ/
├── scripts/
│   ├── python/                      # pure VTK — runs in CI, no ParaView needed
│   ├── pvpython/                    # ParaView batch scripts (need pvpython/pvbatch)
│   ├── plugin/                      # ParaView server-manager plugin
│   └── catalyst/                    # Catalyst v2 adaptor + driver
├── assets/
│   ├── data/                        # generated .vti / .vtu (drop into ParaView)
│   └── renders/                     # PNGs produced by scripts/python/render_figures.py
└── .github/workflows/               # CI: install vtk, regenerate figures, deploy Pages
```

## Quickstart

```bash
pip install vtk numpy
python3 scripts/python/render_figures.py
open assets/renders/q_isosurface.png
```

To open the generated datasets in ParaView:

```bash
paraview assets/data/taylor_green.vti
paraview assets/data/notched_beam.vtu
paraview assets/data/plume.vti
```

## Stack

ParaView · VTK · Catalyst v2 · pvpython / pvbatch · OpenFOAM / SU2 / CGNS / EnSight Gold · XDMF · Python · C++17 · MPI · OSMesa / EGL · GitHub Actions · Docker.

## License

MIT for code, CC-BY-4.0 for figures.
