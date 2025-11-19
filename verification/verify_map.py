from playwright.sync_api import Page, expect, sync_playwright
import time

def verify_map_view(page: Page):
    # 1. Navigate to the home page
    page.goto("http://localhost:5000")

    # 2. Wait for the map to be visible
    # The map is in a div with id "map" inside a card
    map_element = page.locator("#map")
    expect(map_element).to_be_visible()

    # 3. Check for Leaflet markers/elements
    # Leaflet adds classes like leaflet-container
    # expect(map_element).to_have_class(re.compile(r"leaflet-container"))

    # 4. Take a screenshot
    # Wait a bit for tiles to load
    time.sleep(2)
    page.screenshot(path="/app/verification/map_verification.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_map_view(page)
        finally:
            browser.close()
