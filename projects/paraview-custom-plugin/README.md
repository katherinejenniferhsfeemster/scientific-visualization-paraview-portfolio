# Custom ParaView plugin — vorticity + automatic seed points

Production-style ParaView server-manager plugin that adds a single new
filter to the GUI: **Vorticity + Auto Seeds**. It computes the vorticity
field of any vector array on any topology and emits a `vtkPolyData` of the
N highest-vorticity points, ready to feed `Stream Tracer With Custom Source`.

## Why this is useful

Default ParaView seeding is one of:
- a sphere of N points around a focal point (manual, often misses the action);
- a line/plane (great for boundary layers, blind elsewhere);
- a custom dataset (requires you to hand-build seeds).

`VorticityMagnitudeWithSeeds` automates the third option: seeds always
land where the vortices actually are, regardless of dataset topology or
camera position.

## How it works

```
input grid (vtkImageData / vtkUnstructuredGrid / vtkStructuredGrid)
      │
      ├─► vtkGradientFilter (ComputeVorticity = ON)
      │
      ├─► numpy: ‖ω‖, top-N argsort
      │
      └─► vtkPolyData of seed points + 'seed_strength' scalar
```

## Install

1. Copy `VorticityFilter.xml` and `vorticity_module.py` into a directory
2. **Tools → Manage Plugins → Load New** → pick `VorticityFilter.xml`
3. Set "Auto Load" so the filter is available on every launch
4. Apply to any dataset with a vector array. Connect output to
   `Stream Tracer With Custom Source` to get an instant flow visualization.

## Files

| Path                                  | Purpose                              |
|---------------------------------------|--------------------------------------|
| `scripts/plugin/VorticityFilter.xml`  | Server-manager XML proxy definition  |
| `scripts/plugin/vorticity_module.py`  | Python body of the filter            |

## Notes for hardening for production

- For large grids, replace the numpy sort with `numpy.partition` (O(n))
  before slicing top-N.
- If the input has multiple vector fields, the property `VectorArrayName`
  selects which one drives vorticity.
- Wrap the python body in a `try/except` and `paraview.print_warning(...)`
  on failure so the GUI doesn't go silent.

[← back to portfolio](../../README.md)
