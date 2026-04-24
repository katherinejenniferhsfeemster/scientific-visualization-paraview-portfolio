"""
ParaView batch script — load the Taylor-Green dataset, build a state with
Q-criterion isosurface + streamlines + colorbar, and write a screenshot.

Run with:
    pvbatch scripts/pvpython/load_taylor_green.py
or  pvpython scripts/pvpython/load_taylor_green.py

Notes
-----
This script is documentation: it expects ParaView's `paraview.simple` to be
on the PYTHONPATH (use the ParaView-bundled `pvpython` interpreter). In CI we
exercise the same logic via pure VTK in scripts/python/.
"""
from paraview.simple import (  # type: ignore
    XMLImageDataReader, Contour, StreamTracerWithCustomSource, PointSource,
    Tube, Show, ColorBy, GetColorTransferFunction, GetActiveViewOrCreate,
    SaveScreenshot, ResetCamera, GetActiveCamera, Render,
)


def main(vti: str = "assets/data/taylor_green.vti",
         out: str = "assets/renders/paraview_taylor_green.png") -> None:
    reader = XMLImageDataReader(FileName=[vti])
    reader.PointArrayStatus = ["velocity", "Q"]

    # --- Q-criterion isosurface ---
    iso = Contour(Input=reader)
    iso.ContourBy = ["POINTS", "Q"]
    iso.Isosurfaces = [0.06]
    rep = Show(iso)
    rep.Representation = "Surface"
    rep.AmbientColor = [0.18, 0.48, 0.48]
    rep.DiffuseColor = [0.18, 0.48, 0.48]
    rep.Opacity = 0.85

    # --- Streamlines ---
    seeds = PointSource(Center=[3.14, 3.14, 3.14], NumberOfPoints=80, Radius=2.4)
    stream = StreamTracerWithCustomSource(
        Input=reader, SeedSource=seeds,
        Vectors=["POINTS", "velocity"],
        IntegrationDirection="BOTH",
        MaximumStreamlineLength=40,
    )
    tube = Tube(Input=stream, Radius=0.04, NumberofSides=10)
    rep_t = Show(tube)
    ColorBy(rep_t, ("POINTS", "velocity", "Magnitude"))
    lut = GetColorTransferFunction("velocity")
    lut.RGBPoints = [
        0.00, 0.121, 0.353, 0.355,
        0.50, 0.180, 0.478, 0.482,
        0.85, 0.851, 0.643, 0.255,
        1.00, 0.682, 0.176, 0.176,
    ]

    view = GetActiveViewOrCreate("RenderView")
    view.Background = [0.984, 0.980, 0.969]
    view.ViewSize = [1280, 1024]
    ResetCamera()
    cam = GetActiveCamera()
    cam.Elevation(20)
    cam.Azimuth(35)
    Render()
    SaveScreenshot(out, view, ImageResolution=[1280, 1024])


if __name__ == "__main__":
    main()
