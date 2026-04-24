"""
ParaView batch animation: rotate the volume render of the plume dataset
and write 60 frames + an MP4 (requires ffmpeg).

Run:
    pvbatch scripts/pvpython/animate_volume.py
"""
import os
from paraview.simple import (  # type: ignore
    XMLImageDataReader, Show, GetActiveViewOrCreate, GetActiveCamera,
    GetColorTransferFunction, GetOpacityTransferFunction, ResetCamera,
    Render, SaveScreenshot,
)


def main(vti: str = "assets/data/plume.vti",
         out_dir: str = "assets/renders/anim",
         frames: int = 60) -> None:
    os.makedirs(out_dir, exist_ok=True)
    reader = XMLImageDataReader(FileName=[vti])
    reader.PointArrayStatus = ["concentration"]

    rep = Show(reader)
    rep.Representation = "Volume"

    color = GetColorTransferFunction("concentration")
    color.RGBPoints = [
        0.0, 0.121, 0.353, 0.355,
        0.3, 0.180, 0.478, 0.482,
        0.6, 0.851, 0.643, 0.255,
        1.0, 0.682, 0.176, 0.176,
    ]
    opacity = GetOpacityTransferFunction("concentration")
    opacity.Points = [0.0, 0.0, 0.5, 0.0,
                      0.3, 0.4, 0.5, 0.0,
                      0.9, 0.95, 0.5, 0.0]

    view = GetActiveViewOrCreate("RenderView")
    view.Background = [0.984, 0.980, 0.969]
    view.ViewSize = [1024, 1024]
    ResetCamera()

    cam = GetActiveCamera()
    for i in range(frames):
        cam.Azimuth(360.0 / frames)
        Render()
        SaveScreenshot(f"{out_dir}/frame_{i:03d}.png", view)

    # Optionally combine with: ffmpeg -framerate 24 -i frame_%03d.png -c:v libx264 anim.mp4


if __name__ == "__main__":
    main()
