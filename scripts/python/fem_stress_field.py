"""
Synthetic FEM stress field on an unstructured mesh.

Builds a tetrahedral mesh of a notched cantilever beam, applies an analytic
elasticity-like stress tensor with a stress concentration at the notch,
computes von Mises stress, and writes the result to .vtu (XML unstructured
grid) for ParaView. Also renders a warp-by-vector view.

Outputs
-------
    assets/data/notched_beam.vtu
    assets/renders/von_mises.png
    assets/renders/warp_by_vector.png
"""
from __future__ import annotations

import os
import numpy as np
import vtk
from vtk.util import numpy_support as ns


# ---------------------------------------------------------------------------
# Mesh: structured -> tetrahedralised
# ---------------------------------------------------------------------------
def build_beam(nx: int = 60, ny: int = 16, nz: int = 16,
               L: float = 1.0, H: float = 0.2, W: float = 0.2,
               notch_x: float = 0.55, notch_depth: float = 0.06) -> vtk.vtkUnstructuredGrid:
    """Hex-grid notched beam, then tetrahedralise."""
    img = vtk.vtkImageData()
    img.SetDimensions(nx, ny, nz)
    img.SetSpacing(L / (nx - 1), H / (ny - 1), W / (nz - 1))
    img.SetOrigin(0, -H / 2, -W / 2)

    geom = vtk.vtkImageDataGeometryFilter()
    geom.SetInputData(img)

    to_ug = vtk.vtkAppendFilter()
    to_ug.SetInputData(img)
    to_ug.Update()
    ug = to_ug.GetOutput()

    # Knock out cells in the notch
    notch_w = 0.04
    cells_to_keep = vtk.vtkIdTypeArray()
    cells_to_keep.SetNumberOfComponents(1)
    for cid in range(ug.GetNumberOfCells()):
        cell = ug.GetCell(cid)
        b = cell.GetBounds()  # (xmin,xmax,ymin,ymax,zmin,zmax)
        cx = 0.5 * (b[0] + b[1])
        cy = 0.5 * (b[2] + b[3])
        in_notch = (abs(cx - notch_x) < notch_w / 2) and (cy > (H / 2 - notch_depth))
        if not in_notch:
            cells_to_keep.InsertNextValue(cid)

    sel_node = vtk.vtkSelectionNode()
    sel_node.SetFieldType(vtk.vtkSelectionNode.CELL)
    sel_node.SetContentType(vtk.vtkSelectionNode.INDICES)
    sel_node.SetSelectionList(cells_to_keep)
    sel = vtk.vtkSelection()
    sel.AddNode(sel_node)
    extract = vtk.vtkExtractSelection()
    extract.SetInputData(0, ug)
    extract.SetInputData(1, sel)
    extract.Update()

    tetra = vtk.vtkDataSetTriangleFilter()
    tetra.SetInputConnection(extract.GetOutputPort())
    tetra.Update()
    return tetra.GetOutput()


# ---------------------------------------------------------------------------
# Synthetic stress + displacement
# ---------------------------------------------------------------------------
def attach_fields(ug: vtk.vtkUnstructuredGrid,
                  L: float = 1.0, H: float = 0.2, W: float = 0.2,
                  notch_x: float = 0.55) -> None:
    pts = ns.vtk_to_numpy(ug.GetPoints().GetData())
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]

    # Bending: M(x) = P*(L-x), I = W*H^3/12, sigma_xx = M*y/I
    P = 1.0e3
    I = W * H ** 3 / 12.0
    sigma_xx = -P * (L - x) * y / I

    # Stress concentration at notch
    Kt = 1.0 + 2.4 * np.exp(-((x - notch_x) ** 2) / 0.0025) * np.exp(-((y - H / 2) ** 2) / 0.002)
    sigma_xx = sigma_xx * Kt

    # Shear from V/A (V = P)
    A = H * W
    tau_xy = 1.5 * (P / A) * (1 - (2 * y / H) ** 2)
    tau_xy = tau_xy * Kt

    sigma_yy = np.zeros_like(sigma_xx)
    sigma_zz = 0.3 * sigma_xx
    tau_xz = np.zeros_like(sigma_xx)
    tau_yz = np.zeros_like(sigma_xx)

    # von Mises
    sxx, syy, szz = sigma_xx, sigma_yy, sigma_zz
    txy, txz, tyz = tau_xy, tau_xz, tau_yz
    vm = np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2)
                 + 3.0 * (txy ** 2 + txz ** 2 + tyz ** 2))

    # Displacement: simple cantilever bending shape, normalized so the tip
    # deflection is ~ 0.06 (units == metres of beam) for a clear warp render
    delta = (x ** 2) * (3 * L - x)
    delta = delta / delta.max() * 0.06
    ux = np.zeros_like(x)
    uy = -delta
    uz = np.zeros_like(x)
    disp = np.stack([ux, uy, uz], axis=-1).astype(np.float32)

    def add_scalar(name: str, arr: np.ndarray) -> None:
        a = ns.numpy_to_vtk(arr.astype(np.float32), deep=True, array_type=vtk.VTK_FLOAT)
        a.SetName(name)
        ug.GetPointData().AddArray(a)

    def add_vector(name: str, arr: np.ndarray) -> None:
        a = ns.numpy_to_vtk(arr, deep=True, array_type=vtk.VTK_FLOAT)
        a.SetName(name)
        a.SetNumberOfComponents(3)
        ug.GetPointData().AddArray(a)

    add_scalar("sigma_xx", sigma_xx)
    add_scalar("tau_xy", tau_xy)
    add_scalar("von_mises", vm)
    add_vector("displacement", disp)
    ug.GetPointData().SetActiveScalars("von_mises")
    ug.GetPointData().SetActiveVectors("displacement")


# ---------------------------------------------------------------------------
# IO + renders
# ---------------------------------------------------------------------------
def write_vtu(ug: vtk.vtkUnstructuredGrid, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    w = vtk.vtkXMLUnstructuredGridWriter()
    w.SetFileName(path)
    w.SetInputData(ug)
    w.SetDataModeToBinary()
    w.Write()


def _render(ren: vtk.vtkRenderer, out: str, size: int = 1024) -> None:
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rw = vtk.vtkRenderWindow()
    rw.AddRenderer(ren)
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


def _camera(ren: vtk.vtkRenderer) -> None:
    cam = ren.GetActiveCamera()
    cam.SetPosition(1.4, 0.9, 1.6)
    cam.SetFocalPoint(0.45, -0.02, 0.0)
    cam.SetViewUp(0, 1, 0)
    ren.ResetCamera()
    cam.Zoom(1.5)


def render_von_mises(ug: vtk.vtkUnstructuredGrid, out: str) -> None:
    surf = vtk.vtkDataSetSurfaceFilter()
    surf.SetInputData(ug)

    lut = vtk.vtkColorTransferFunction()
    lut.AddRGBPoint(0.0, 0.121, 0.353, 0.355)   # deep teal
    lut.AddRGBPoint(0.5, 0.851, 0.643, 0.255)   # amber
    lut.AddRGBPoint(1.0, 0.682, 0.176, 0.176)   # ember

    arr = ns.vtk_to_numpy(ug.GetPointData().GetArray("von_mises"))
    lo, hi = float(np.percentile(arr, 5)), float(np.percentile(arr, 95))

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(surf.GetOutputPort())
    mapper.SelectColorArray("von_mises")
    mapper.SetScalarModeToUsePointFieldData()
    mapper.SetLookupTable(lut)
    mapper.SetScalarRange(lo, hi)
    mapper.ScalarVisibilityOn()

    lut.RemoveAllPoints()
    lut.AddRGBPoint(lo, 0.121, 0.353, 0.355)
    lut.AddRGBPoint(0.5 * (lo + hi), 0.851, 0.643, 0.255)
    lut.AddRGBPoint(hi, 0.682, 0.176, 0.176)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    ren = vtk.vtkRenderer()
    ren.SetBackground(0.984, 0.980, 0.969)
    ren.AddActor(actor)
    _camera(ren)
    _render(ren, out)


def render_warp(ug: vtk.vtkUnstructuredGrid, out: str) -> None:
    warp = vtk.vtkWarpVector()
    warp.SetInputData(ug)
    warp.SetInputArrayToProcess(0, 0, 0, 0, "displacement")
    warp.SetScaleFactor(1.5)

    surf = vtk.vtkDataSetSurfaceFilter()
    surf.SetInputConnection(warp.GetOutputPort())

    arr = ns.vtk_to_numpy(ug.GetPointData().GetArray("von_mises"))
    lo, hi = float(np.percentile(arr, 5)), float(np.percentile(arr, 95))

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(surf.GetOutputPort())
    mapper.SelectColorArray("von_mises")
    mapper.SetScalarModeToUsePointFieldData()
    mapper.SetScalarRange(lo, hi)

    lut = vtk.vtkColorTransferFunction()
    lut.AddRGBPoint(lo, 0.121, 0.353, 0.355)
    lut.AddRGBPoint(0.5 * (lo + hi), 0.851, 0.643, 0.255)
    lut.AddRGBPoint(hi, 0.682, 0.176, 0.176)
    mapper.SetLookupTable(lut)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().EdgeVisibilityOn()
    actor.GetProperty().SetEdgeColor(0.10, 0.12, 0.13)
    actor.GetProperty().SetLineWidth(0.4)

    ren = vtk.vtkRenderer()
    ren.SetBackground(0.984, 0.980, 0.969)
    ren.AddActor(actor)
    _camera(ren)
    _render(ren, out)


def main() -> None:
    ug = build_beam()
    attach_fields(ug)
    write_vtu(ug, "assets/data/notched_beam.vtu")
    render_von_mises(ug, "assets/renders/von_mises.png")
    render_warp(ug, "assets/renders/warp_by_vector.png")
    print(f"[ok] FEM stress: {ug.GetNumberOfCells()} cells, {ug.GetNumberOfPoints()} points.")


if __name__ == "__main__":
    main()
