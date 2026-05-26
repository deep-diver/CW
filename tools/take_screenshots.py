"""Take screenshots of the FreshCart Market Tier B reference app."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import time, shutil

STATIC = Path("targets/web/freshcart_market/tier_b/reference_app")
OUT = Path("targets/web/freshcart_market/tier_b/reports/screenshots/reference")

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(f"file://{STATIC.resolve() / 'index.html'}")
        time.sleep(0.5)

        # 1) Market page — default view
        page.screenshot(path=OUT / "01_market.png", full_page=False)
        print("01_market.png")

        # 2) Market — filtered by GreenFarm
        page.click('[data-testid="filter-greenfarm"]')
        time.sleep(0.3)
        page.screenshot(path=OUT / "02_market_greenfarm.png", full_page=False)
        print("02_market_greenfarm.png")

        # 3) Market — add items to cart
        page.click('[data-testid="filter-all"]')
        page.click('[data-testid="add-GC-AVO-01"]')
        page.click('[data-testid="add-GC-TUN-01"]')
        page.click('[data-testid="add-GC-SHR-01"]')
        page.click('[data-testid="add-GC-HON-01"]')
        time.sleep(0.3)
        page.screenshot(path=OUT / "03_market_cart.png", full_page=False)
        print("03_market_cart.png")

        # 4) Basket page — with prep options
        page.click('[data-testid="go-basket"]')
        time.sleep(0.3)
        page.screenshot(path=OUT / "04_basket.png", full_page=False)
        print("04_basket.png")

        # 5) Basket — after applying sashimi prep
        page.click('[data-testid="prep-sashimi-GC-TUN-01"]')
        page.click('[data-testid="prep-devein-GC-SHR-01"]')
        page.click('[data-testid="prep-gift-GC-HON-01"]')
        time.sleep(0.3)
        page.screenshot(path=OUT / "05_basket_prep.png", full_page=False)
        print("05_basket_prep.png")

        # 6) Checkout page
        page.click('[data-testid="go-checkout"]')
        time.sleep(0.3)
        page.click('[data-testid="enable-express"]')
        page.click('[data-testid="enable-gift-wrap"]')
        page.click('[data-testid="slot-evening"]')
        page.fill('[data-testid="customer-name"]', "Eunjung Choi")
        page.fill('[data-testid="customer-phone"]', "010-9876-5432")
        time.sleep(0.3)
        page.screenshot(path=OUT / "06_checkout.png", full_page=False)
        print("06_checkout.png")

        # 7) Place order, go to orders
        page.click('[data-testid="place-order"]')
        time.sleep(0.5)
        page.click('[data-testid="go-orders"]')
        time.sleep(0.3)
        page.screenshot(path=OUT / "07_orders.png", full_page=False)
        print("07_orders.png")

        # 8) Orders — staff view with checklist
        page.click('[data-testid="role-staff"]')
        time.sleep(0.3)
        page.click('[data-testid="verify-fulfillment"]')
        page.click('[data-testid="confirm-packed"]')
        time.sleep(0.3)
        page.screenshot(path=OUT / "08_orders_staff.png", full_page=False)
        print("08_orders_staff.png")

        browser.close()
    print(f"\nScreenshots saved to {OUT.resolve()}")

if __name__ == "__main__":
    main()
