"""
ParaView Catalyst v2 adaptor — in-situ visualization driven from a Python
simulation script. The simulation produces a 3D scalar field on a uniform
grid each timestep; Catalyst slices, contours, and writes a PNG every N
steps without ever touching disk for raw data.

Usage
-----
With ParaView built with Catalyst:

    pvbatch scripts/catalyst/driver.py \\
        --catalyst scripts/catalyst/catalyst_adaptor.py
"""
from paraview.simple import (  # type: ignore
    Contour, Show, GetActiveViewOrCreate, ColorBy,
    GetColorTransferFunction, SaveScreenshot, Render,
)
from paraview import catalyst                       # type: ignore
from paraview.catalyst import bridge                 # type: ignore

# -- Catalyst options ---------------------------------------------------
options = catalyst.Options()
options.GlobalTrigger = "TimeStep"
options.CatalystLiveTrigger = "TimeStep"
options.EnableCatalystLive = 1


def catalyst_initialize():
    bridge.initialize()


def catalyst_finalize():
    bridge.finalize()


# -- Per-timestep pipeline ---------------------------------------------
def catalyst_execute(info):
    grid = info.catalyst_input("input")              # vtkImageData

    iso = Contour(Input=grid)
    iso.ContourBy = ["POINTS", "concentration"]
    iso.Isosurfaces = [0.25, 0.55]

    rep = Show(iso)
    ColorBy(rep, ("POINTS", "concentration"))
    lut = GetColorTransferFunction("concentration")
    lut.RGBPoints = [
        0.00, 0.121, 0.353, 0.355,
        0.50, 0.851, 0.643, 0.255,
        1.00, 0.682, 0.176, 0.176,
    ]

    view = GetActiveViewOrCreate("RenderView")
    view.Background = [0.984, 0.980, 0.969]
    view.ViewSize = [1024, 1024]
    Render()

    # Save one PNG every 10 steps -- adjust to your output cadence.
    if info.cycle % 10 == 0:
        SaveScreenshot(f"in-situ/iso_{info.cycle:05d}.png", view)
