from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent.parent / "screenshots"
OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
    pg.goto("http://127.0.0.1:8000/cds-hooks", timeout=60000, wait_until="load")
    pg.wait_for_timeout(600)
    pg.screenshot(path=str(OUT / "cds_hooks.png"), full_page=True)
    print("shot cds_hooks")
    b.close()
