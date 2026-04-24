"""
Run all visualization scripts headlessly to regenerate every PNG.

Usage:
    python3 scripts/python/render_figures.py
"""
import importlib.util
import pathlib
import sys


HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))


def _run(name: str) -> None:
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    print(f"\n=== {name} ===")
    spec.loader.exec_module(mod)
    mod.main()


def main() -> None:
    import os
    os.chdir(ROOT)
    _run("taylor_green_vortex")
    _run("fem_stress_field")
    _run("volumetric_scalar")
    print("\n[ok] All figures rendered.")


if __name__ == "__main__":
    main()
