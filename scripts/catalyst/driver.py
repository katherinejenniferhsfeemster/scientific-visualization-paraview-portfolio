"""
Toy simulation driver demonstrating how to push fields into Catalyst on
each timestep. In a real solver this would be a thin Python wrapper around
the C++ simulation that exposes its grids via Conduit.

This script intentionally uses only numpy + the Catalyst Python bridge so
it can stand in for an arbitrary CFD/MHD solver in documentation.
"""
import argparse
import numpy as np
from paraview.catalyst import bridge                 # type: ignore
from paraview.modules.vtkPVCatalyst import vtkCPDataDescription   # type: ignore
from paraview.modules.vtkPVCatalyst import vtkCPInputDataDescription  # type: ignore

import vtk
from vtk.util import numpy_support as ns


def make_grid(n: int = 64) -> vtk.vtkImageData:
    img = vtk.vtkImageData()
    img.SetDimensions(n, n, n)
    img.SetSpacing(1.0 / n, 1.0 / n, 1.0 / n)
    return img


def update_field(img: vtk.vtkImageData, t: float) -> None:
    n = img.GetDimensions()[0]
    x = np.linspace(0, 1, n)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    src = np.array([0.3 + 0.4 * t, 0.5, 0.5])
    r = np.sqrt((X - src[0]) ** 2 + (Y - src[1]) ** 2 + (Z - src[2]) ** 2)
    field = np.exp(-r ** 2 / 0.04).astype(np.float32)
    arr = ns.numpy_to_vtk(field.reshape(-1, order="F"), deep=True,
                          array_type=vtk.VTK_FLOAT)
    arr.SetName("concentration")
    img.GetPointData().RemoveArray("concentration")
    img.GetPointData().AddArray(arr)
    img.GetPointData().SetActiveScalars("concentration")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--catalyst", required=True,
                    help="path to catalyst_adaptor.py")
    args = ap.parse_args()

    bridge.initialize()
    bridge.add_pipeline(args.catalyst)

    grid = make_grid()
    for cycle in range(args.steps):
        t = cycle / max(1, args.steps - 1)
        update_field(grid, t)

        desc = vtkCPDataDescription()
        desc.SetTimeData(t, cycle)
        desc.AddInput("input")
        desc.GetInputDescriptionByName("input").SetGrid(grid)

        bridge.coprocess(desc)

    bridge.finalize()


if __name__ == "__main__":
    main()
