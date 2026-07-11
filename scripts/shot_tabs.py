from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent.parent / "screenshots"
URL = "http://127.0.0.1:8000/patient/u-cole/enc-u-cole"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
    pg.goto(URL, timeout=180000, wait_until="load")
    pg.wait_for_timeout(500)
    pg.screenshot(path=str(OUT / "tab_recommendation.png"), full_page=True)
    print("shot recommendation")
    pg.click("text=Orders")
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "tab_orders.png"), full_page=True)
    print("shot orders")
    pg.click("text=Labs")
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "tab_labs.png"), full_page=True)
    print("shot labs")
    b.close()
