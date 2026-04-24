# In-situ visualization with ParaView Catalyst

Demonstration of a Catalyst v2 adaptor for in-situ visualization — the
correct strategy whenever the simulation produces more data per step than
can be reasonably written to disk.

## What this shows

- A toy time-stepping driver (`driver.py`) that mimics a CFD solver,
  generating a 3D scalar field every step
- A Catalyst pipeline (`catalyst_adaptor.py`) that runs *inside* the
  simulation process and produces:
  - dual isocontours (0.25 and 0.55)
  - color mapping with a custom teal → amber → ember transfer function
  - one PNG every 10 cycles with no raw output written

## Architecture

```
   ┌─────────────────────────┐
   │   simulation driver     │
   │  (numpy / Conduit / C++)│
   └──────────┬──────────────┘
              │  vtkImageData per timestep
              ▼
   ┌─────────────────────────┐
   │  Catalyst bridge        │  ── lives in the same process
   │  bridge.coprocess(desc) │
   └──────────┬──────────────┘
              │
              ▼
   ┌─────────────────────────┐
   │  catalyst_adaptor.py    │  ── ParaView pipeline (Contour, Show,
   │                         │     ColorBy, SaveScreenshot)
   └──────────┬──────────────┘
              │
              ▼
       PNG every N steps  +  optional Catalyst Live to a remote pvserver
```

## Run

With ParaView built with Catalyst:

```bash
pvbatch scripts/catalyst/driver.py \
    --catalyst scripts/catalyst/catalyst_adaptor.py \
    --steps 200
```

## Why in-situ

A 1024³ float scalar field is 4 GB per step; at 0.1 s per step that's
40 GB/s of I/O — three orders of magnitude over a fast NVMe array.
In-situ visualization sidesteps the I/O wall entirely and lets the user
steer the simulation interactively via Catalyst Live.

## Files

| Path                                   | Purpose                            |
|----------------------------------------|------------------------------------|
| `scripts/catalyst/driver.py`           | Toy simulation that pushes grids   |
| `scripts/catalyst/catalyst_adaptor.py` | In-situ ParaView pipeline          |

[← back to portfolio](../../README.md)
