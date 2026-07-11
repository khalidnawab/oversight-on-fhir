"""Screenshot key pages against the live frontier backend (slower — real model calls)."""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent.parent / "screenshots"
OUT.mkdir(exist_ok=True)

PAGES = {
    "live_patient_anand": "http://127.0.0.1:8000/patient/u-anand/enc-u-anand",  # culture-negative -> stop
    "live_census": "http://127.0.0.1:8000/",
}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
    for name, url in PAGES.items():
        page.goto(url, timeout=240000, wait_until="load")
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
        print(f"shot {name}")
    browser.close()
