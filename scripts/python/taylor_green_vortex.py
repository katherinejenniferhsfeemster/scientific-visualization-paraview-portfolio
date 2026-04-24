"""
Taylor-Green vortex: synthetic 3D turbulent flow field on a structured grid.

Generates the analytic Taylor-Green vortex velocity field on a 64^3 uniform
grid, derives the Q-criterion (vortex identification), and writes the dataset
to VTK XML format (.vti) so it can be inspected directly in ParaView.

Outputs
-------
    assets/data/taylor_green.vti        Image data with velocity + Q
    assets/renders/q_isosurface.png     Q-criterion isosurface render
    assets/renders/streamlines.png      Streamline integration

Run
---
    python3 scripts/python/taylor_green_vortex.py
"""
from __future__ import annotations

import os
import numpy as np
import vtk
from vtk.util import numpy_support as ns


# ---------------------------------------------------------------------------
# Analytic field
# ---------------------------------------------------------------------------
def taylor_green(n: int = 64, L: float = 2.0 * np.pi) -> tuple[np.ndarray, np.ndarray]:
    """Return (coords, velocity) on an n^3 grid covering [0, L]^3."""
    x = np.linspace(0, L, n)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    u = np.sin(X) * np.cos(Y) * np.cos(Z)
    v = -np.cos(X) * np.sin(Y) * np.cos(Z)
    w = np.zeros_like(u)
    vel = np.stack([u, v, w], axis=-1).astype(np.float32)
    return x, vel


def q_criterion(vel: np.ndarray, dx: float) -> np.ndarray:
    """Compute Q = 0.5 (||Omega||^2 - ||S||^2) on the structured grid."""
    u, v, w = vel[..., 0], vel[..., 1], vel[..., 2]
    du = np.gradient(u, dx)
    dv = np.gradient(v, dx)
    dw = np.gradient(w, dx)
    grad = np.stack([du, dv, dw], axis=0)  # (3, 3, nx, ny, nz)
    S = 0.5 * (grad + grad.transpose(1, 0, 2, 3, 4))
    O = 0.5 * (grad - grad.transpose(1, 0, 2, 3, 4))
    Q = 0.5 * ((O ** 2).sum(axis=(0, 1)) - (S ** 2).sum(axis=(0, 1)))
    return Q.astype(np.float32)


# ---------------------------------------------------------------------------
# VTK image data + renders
# ---------------------------------------------------------------------------
def build_image_data(coords: np.ndarray, vel: np.ndarray, Q: np.ndarray) -> vtk.vtkImageData:
    n = coords.size
    dx = float(coords[1] - coords[0])

    img = vtk.vtkImageData()
    img.SetDimensions(n, n, n)
    img.SetSpacing(dx, dx, dx)
    img.SetOrigin(coords[0], coords[0], coords[0])

    vel_flat = vel.reshape(-1, 3, order="F")
    vtk_vel = ns.numpy_to_vtk(vel_flat, deep=True, array_type=vtk.VTK_FLOAT)
    vtk_vel.SetName("velocity")
    vtk_vel.SetNumberOfComponents(3)
    img.GetPointData().AddArray(vtk_vel)
    img.GetPointData().SetActiveVectors("velocity")

    q_flat = Q.reshape(-1, order="F")
    vtk_q = ns.numpy_to_vtk(q_flat, deep=True, array_type=vtk.VTK_FLOAT)
    vtk_q.SetName("Q")
    img.GetPointData().AddArray(vtk_q)
    img.GetPointData().SetActiveScalars("Q")
    return img


def write_vti(img: vtk.vtkImageData, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    w = vtk.vtkXMLImageDataWriter()
    w.SetFileName(path)
    w.SetInputData(img)
    w.SetDataModeToBinary()
    w.Write()


def render_to_png(render_window: vtk.vtkRenderWindow, path: str, size: int = 1024) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    render_window.SetOffScreenRendering(1)
    render_window.SetSize(size, size)
    render_window.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(render_window)
    w2i.SetScale(1)
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(path)
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()


def render_q_isosurface(img: vtk.vtkImageData, out: str) -> None:
    contour = vtk.vtkContourFilter()
    contour.SetInputData(img)
    contour.SetInputArrayToProcess(0, 0, 0, 0, "Q")
    contour.SetValue(0, 0.06)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(contour.GetOutputPort())
    mapper.ScalarVisibilityOff()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.18, 0.48, 0.48)   # teal
    actor.GetProperty().SetOpacity(0.9)
    actor.GetProperty().SetSpecular(0.4)
    actor.GetProperty().SetSpecularPower(20)

    ren = vtk.vtkRenderer()
    ren.SetBackground(0.984, 0.980, 0.969)  # bg
    ren.AddActor(actor)
    ren.GetActiveCamera().SetPosition(14, 14, 12)
    ren.GetActiveCamera().SetFocalPoint(np.pi, np.pi, np.pi)
    ren.GetActiveCamera().SetViewUp(0, 0, 1)
    ren.ResetCameraClippingRange()

    rw = vtk.vtkRenderWindow()
    rw.AddRenderer(ren)
    render_to_png(rw, out)


def render_streamlines(img: vtk.vtkImageData, out: str) -> None:
    # Add velocity magnitude as a point scalar for coloring
    vel_arr = ns.vtk_to_numpy(img.GetPointData().GetArray("velocity"))
    mag = np.linalg.norm(vel_arr, axis=1).astype(np.float32)
    mag_vtk = ns.numpy_to_vtk(mag, deep=True, array_type=vtk.VTK_FLOAT)
    mag_vtk.SetName("speed")
    img.GetPointData().AddArray(mag_vtk)

    seeds = vtk.vtkPointSource()
    seeds.SetCenter(np.pi, np.pi, np.pi)
    seeds.SetRadius(2.6)
    seeds.SetNumberOfPoints(70)

    rk = vtk.vtkRungeKutta4()
    tracer = vtk.vtkStreamTracer()
    tracer.SetInputData(img)
    tracer.SetSourceConnection(seeds.GetOutputPort())
    tracer.SetMaximumPropagation(40)
    tracer.SetInitialIntegrationStep(0.05)
    tracer.SetIntegrationDirectionToBoth()
    tracer.SetIntegrator(rk)
    tracer.SetInputArrayToProcess(0, 0, 0, 0, "velocity")

    tubes = vtk.vtkTubeFilter()
    tubes.SetInputConnection(tracer.GetOutputPort())
    tubes.SetRadius(0.04)
    tubes.SetNumberOfSides(10)

    lut = vtk.vtkColorTransferFunction()
    lut.AddRGBPoint(0.00, 0.121, 0.353, 0.355)
    lut.AddRGBPoint(0.50, 0.180, 0.478, 0.482)
    lut.AddRGBPoint(0.85, 0.851, 0.643, 0.255)
    lut.AddRGBPoint(1.00, 0.682, 0.176, 0.176)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(tubes.GetOutputPort())
    mapper.SelectColorArray("speed")
    mapper.SetScalarModeToUsePointFieldData()
    mapper.SetLookupTable(lut)
    mapper.SetScalarRange(0.0, 1.0)
    mapper.ScalarVisibilityOn()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    ren = vtk.vtkRenderer()
    ren.SetBackground(0.984, 0.980, 0.969)
    ren.AddActor(actor)
    ren.GetActiveCamera().SetPosition(15, 13, 11)
    ren.GetActiveCamera().SetFocalPoint(np.pi, np.pi, np.pi)
    ren.GetActiveCamera().SetViewUp(0, 0, 1)
    ren.ResetCamera()
    ren.GetActiveCamera().Zoom(1.1)

    rw = vtk.vtkRenderWindow()
    rw.AddRenderer(ren)
    render_to_png(rw, out)


def main() -> None:
    coords, vel = taylor_green(n=64)
    dx = float(coords[1] - coords[0])
    Q = q_criterion(vel, dx)

    img = build_image_data(coords, vel, Q)
    write_vti(img, "assets/data/taylor_green.vti")

    render_q_isosurface(img, "assets/renders/q_isosurface.png")
    render_streamlines(img, "assets/renders/streamlines.png")
    print("[ok] Taylor-Green: VTI + 2 renders written.")


if __name__ == "__main__":
    main()
