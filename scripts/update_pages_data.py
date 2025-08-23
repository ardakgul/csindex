"""Update the static dashboard JSON for GitHub Pages.

Runs the Cloudy&Shiny index calculation (fast path) and copies the latest
`current_index.json` into `frontend/public/data/current_index.json` so that
the next push (or manual commit) updates the static site data.

Intended to be scheduled every 30 minutes via Windows Task Scheduler.
"""
from __future__ import annotations
import json, shutil, time, os, sys, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEBSITE_DATA = ROOT / 'website' / 'data' / 'current_index.json'
PUBLIC_DATA = ROOT / 'frontend' / 'public' / 'data' / 'current_index.json'

def main():
    start = time.time()
    try:
        # Run calculation script (it will refresh website/data/current_index.json)
        print('[update] Running index calculation...')
        rc = os.system(f'"{sys.executable}" "{ROOT / "cloudy_shiny_index.py"}" >nul 2>&1')
        if rc != 0:
            print(f'[update] WARNING: calculation exited with code {rc}')
        if WEBSITE_DATA.exists():
            PUBLIC_DATA.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(WEBSITE_DATA, PUBLIC_DATA)
            print(f'[update] Copied {WEBSITE_DATA} -> {PUBLIC_DATA}')
        else:
            print('[update] WARNING: website current_index.json not found')
    except Exception as e:
        print('[update] ERROR:', e)
        traceback.print_exc()
        return 1
    finally:
        print(f'[update] Done in {time.time()-start:.1f}s')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
