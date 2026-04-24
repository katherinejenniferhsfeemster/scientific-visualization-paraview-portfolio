"""
Body of the ParaView Programmable Filter `VorticityMagnitudeWithSeeds`.

Paste this content into the Script field of the proxy (or load via the XML),
then set VectorArrayName + NumberOfSeeds. Output is a vtkPolyData whose
points are the top-N highest-vorticity locations of the input grid -- ready
to be plugged into a Stream Tracer with Custom Source.
"""
import numpy as np
from vtk.util import numpy_support as ns

input0 = self.GetInputDataObject(0, 0)              # noqa: F821 (PV exec context)
output = self.GetOutputDataObject(0)                 # noqa: F821

vec_name = VectorArrayName                           # injected by proxy   noqa: F821
n_seeds = int(NumberOfSeeds)                         # noqa: F821

# Compute vorticity via VTK's filter so it works on any topology
import vtk
grad = vtk.vtkGradientFilter()
grad.SetInputData(input0)
grad.SetInputArrayToProcess(0, 0, 0, 0, vec_name)
grad.SetComputeVorticity(True)
grad.SetVorticityArrayName("vorticity")
grad.Update()

dataset = grad.GetOutput()
vort = ns.vtk_to_numpy(dataset.GetPointData().GetArray("vorticity"))
mag = np.linalg.norm(vort, axis=1)

# Push vorticity magnitude back into the input so downstream filters see it
mag_vtk = ns.numpy_to_vtk(mag.astype(np.float32), deep=True)
mag_vtk.SetName("vorticity_mag")
dataset.GetPointData().AddArray(mag_vtk)

# Pick top-N points
idx = np.argsort(mag)[::-1][:n_seeds]
pts = ns.vtk_to_numpy(dataset.GetPoints().GetData())[idx]

vtk_pts = vtk.vtkPoints()
vtk_pts.SetData(ns.numpy_to_vtk(pts.astype(np.float64), deep=True))

verts = vtk.vtkCellArray()
for i in range(len(pts)):
    verts.InsertNextCell(1)
    verts.InsertCellPoint(i)

output.SetPoints(vtk_pts)
output.SetVerts(verts)

# Carry the magnitude on the seed points too (useful for coloring)
seed_mag = ns.numpy_to_vtk(mag[idx].astype(np.float32), deep=True)
seed_mag.SetName("seed_strength")
output.GetPointData().AddArray(seed_mag)
output.GetPointData().SetActiveScalars("seed_strength")
