"""
One-off script: drives the running Streamlit app (must already be running on
localhost:8765) with a real browser via Playwright, switches the language,
uploads the synthetic test song, runs an analysis, and saves screenshots.
"""
import time
from playwright.sync_api import sync_playwright

URL = "http://localhost:8765"
TEST_AUDIO = "/home/claude/hit-song-predictor/tests/sample_test_audio.wav"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 1100})
    page.on("pageerror", lambda exc: print(f"[pageerror] {exc}"))
    page.goto(URL, wait_until="networkidle")
    time.sleep(2)
    page.screenshot(path="/home/claude/hit-song-predictor/tests/shot_debug_initial.png", full_page=True)

    # The sidebar's "Target market" selectbox is first in DOM order, the
    # main-area "Language" selectbox is second — even though Language
    # appears above visually (sidebar markup precedes main content).
    lang_select = page.get_by_role("combobox").nth(1)
    lang_select.click()
    time.sleep(0.8)
    page.get_by_role("option", name="नेपाली (Nepali)").click()
    time.sleep(1.5)
    page.screenshot(path="/home/claude/hit-song-predictor/tests/shot_ne_landing.png", full_page=True)

    # Skip lyrics (last radio option) and upload
    page.get_by_text("बोल छोड्नुहोस्").click()
    time.sleep(0.5)
    file_input = page.locator('input[type="file"]').first
    file_input.set_input_files(TEST_AUDIO)
    time.sleep(2)

    analyze_btn = page.get_by_role("button", name="विश्लेषण गर्नुहोस्")
    analyze_btn.click()

    for i in range(60):
        time.sleep(1)
        if page.locator("text=उपयुक्तता स्कोर").count() > 0:
            print(f"found score text at t+{i+1}s")
            break
    else:
        print("TIMED OUT waiting for score text")
    time.sleep(2)
    page.screenshot(path="/home/claude/hit-song-predictor/tests/shot_ne_results.png", full_page=True)

    browser.close()

print("Screenshots saved.")
