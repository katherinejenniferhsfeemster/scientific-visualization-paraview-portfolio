"""
Volumetric scalar field (climate / atmospheric proxy).

Generates a synthetic 3D scalar field that mimics a stratified atmospheric
plume (gaussian source advected and diffused), writes it to .vti, and
renders it three ways:
    1. GPU volume rendering with a transfer function
    2. Multiple isocontours
    3. Threshold + slice combination
"""
from __future__ import annotations

import os
import numpy as np
import vtk
from vtk.util import numpy_support as ns


def synthetic_plume(n: int = 96) -> tuple[np.ndarray, np.ndarray]:
    x = np.linspace(-1, 1, n)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")

    # Source at (-0.6, 0, -0.4), advected in +x by wind, diffuses with z
    src = np.array([-0.6, 0.0, -0.4])
    drift = X - src[0] - 0.5 * (Z - src[2])
    radial = np.sqrt(drift ** 2 + (Y - src[1]) ** 2)
    sigma = 0.18 + 0.25 * (X - src[0] + 1.0)
    plume = np.exp(-(radial ** 2) / (2 * sigma ** 2))

    # Stratification: stronger at low altitude
    stratification = np.exp(-3.0 * (Z + 0.5) ** 2)
    field = (plume * stratification).astype(np.float32)
    return x, field


def to_image_data(coords: np.ndarray, field: np.ndarray) -> vtk.vtkImageData:
    n = coords.size
    dx = float(coords[1] - coords[0])
    img = vtk.vtkImageData()
    img.SetDimensions(n, n, n)
    img.SetSpacing(dx, dx, dx)
    img.SetOrigin(coords[0], coords[0], coords[0])
    arr = ns.numpy_to_vtk(field.reshape(-1, order="F"), deep=True, array_type=vtk.VTK_FLOAT)
    arr.SetName("concentration")
    img.GetPointData().AddArray(arr)
    img.GetPointData().SetActiveScalars("concentration")
    return img


def write_vti(img: vtk.vtkImageData, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    w = vtk.vtkXMLImageDataWriter()
    w.SetFileName(path)
    w.SetInputData(img)
    w.SetDataModeToBinary()
    w.Write()


def _to_png(rw: vtk.vtkRenderWindow, out: str, size: int = 1024) -> None:
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rw.SetOffScreenRendering(1)
    rw.SetSize(size, size)
    rw.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.Update()
    pw = vtk.vtkPNGWriter()
    pw.SetFileName(out)
    pw.SetInputConnection(w2i.GetOutputPort())
    pw.Write()


def render_volume(img: vtk.vtkImageData, out: str) -> None:
    color = vtk.vtkColorTransferFunction()
    color.AddRGBPoint(0.00, 0.121, 0.353, 0.355)   # teal deep
    color.AddRGBPoint(0.30, 0.180, 0.478, 0.482)
    color.AddRGBPoint(0.60, 0.851, 0.643, 0.255)   # amber
    color.AddRGBPoint(1.00, 0.682, 0.176, 0.176)   # ember

    opacity = vtk.vtkPiecewiseFunction()
    opacity.AddPoint(0.00, 0.00)
    opacity.AddPoint(0.10, 0.08)
    opacity.AddPoint(0.30, 0.40)
    opacity.AddPoint(0.60, 0.85)
    opacity.AddPoint(0.90, 0.98)
    opacity.AddPoint(1.00, 1.00)

    prop = vtk.vtkVolumeProperty()
    prop.SetColor(color)
    prop.SetScalarOpacity(opacity)
    prop.SetInterpolationTypeToLinear()
    prop.ShadeOn()
    prop.SetAmbient(0.3)
    prop.SetDiffuse(0.7)
    prop.SetSpecular(0.2)

    mapper = vtk.vtkSmartVolumeMapper()
    mapper.SetInputData(img)

    vol = vtk.vtkVolume()
    vol.SetMapper(mapper)
    vol.SetProperty(prop)

    ren = vtk.vtkRenderer()
    ren.SetBackground(0.984, 0.980, 0.969)
    ren.AddVolume(vol)
    cam = ren.GetActiveCamera()
    cam.SetPosition(2.6, 1.9, 1.5)
    cam.SetFocalPoint(0.0, 0.0, 0.0)
    cam.SetViewUp(0, 0, 1)
    ren.ResetCamera()
    cam.Zoom(1.4)

    rw = vtk.vtkRenderWindow()
    rw.AddRenderer(ren)
    _to_png(rw, out)


def render_isocontours(img: vtk.vtkImageData, out: str) -> None:
    contour = vtk.vtkContourFilter()
    contour.SetInputData(img)
    contour.SetInputArrayToProcess(0, 0, 0, 0, "concentration")
    levels = [0.15, 0.35, 0.65]
    contour.SetNumberOfContours(len(levels))
    for i, v in enumerate(levels):
        contour.SetValue(i, v)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(contour.GetOutputPort())

    lut = vtk.vtkColorTransferFunction()
    lut.AddRGBPoint(0.15, 0.121, 0.353, 0.355)
    lut.AddRGBPoint(0.35, 0.851, 0.643, 0.255)
    lut.AddRGBPoint(0.65, 0.682, 0.176, 0.176)
    mapper.SetLookupTable(lut)
    mapper.SetScalarRange(0.15, 0.65)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetOpacity(0.55)

    ren = vtk.vtkRenderer()
    ren.SetBackground(0.984, 0.980, 0.969)
    ren.AddActor(actor)
    cam = ren.GetActiveCamera()
    cam.SetPosition(2.6, 1.9, 1.5)
    cam.SetFocalPoint(0.0, 0.0, 0.0)
    cam.SetViewUp(0, 0, 1)
    ren.ResetCamera()
    cam.Zoom(1.4)

    rw = vtk.vtkRenderWindow()
    rw.AddRenderer(ren)
    _to_png(rw, out)


def main() -> None:
    coords, field = synthetic_plume(n=96)
    img = to_image_data(coords, field)
    write_vti(img, "assets/data/plume.vti")
    render_volume(img, "assets/renders/volume_render.png")
    render_isocontours(img, "assets/renders/isocontours.png")
    print("[ok] Volume: VTI + 2 renders.")


if __name__ == "__main__":
    main()
