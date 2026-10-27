import os
import pytest
from playwright.sync_api import Page, Browser, expect
from pages.webshop_page import HomePage
from data.test_data import TestConfig


@pytest.mark.locators
class TestLocatorsAndDebugging:

    def test_role_and_placeholder_locators(self, page: Page, base_url: str, demo_form_url: str):
        page.goto(demo_form_url)
        expect(page.get_by_placeholder("Enter first name")).to_be_visible()
        expect(page.get_by_placeholder("name@example.com")).to_be_visible()

        page.goto(base_url)
        page.locator("#small-searchterms").fill("Laptop")
        page.get_by_role("button", name="Search").click()
        expect(page.get_by_role("heading", name="Search")).to_be_visible()

    def test_filter_product_cards(self, page: Page, base_url: str):
        page.goto(f"{base_url}/books")
        cards = page.locator(".product-item")

        assert cards.count() >= 1
        expect(cards.filter(has_text="Computing and Internet").first).to_be_visible()
        expect(cards.filter(has=page.locator("input[value='Add to cart']")).first).to_be_visible()

    def test_trace_viewer(self, browser_instance: Browser, base_url: str):
        trace_file = TestConfig.TRACES_DIR / "debug_sample_trace.zip"
        context = browser_instance.new_context()
        page = context.new_page()

        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page.goto(base_url)
        page.locator("#small-searchterms").fill("Jewelry")
        page.get_by_role("button", name="Search").click()
        context.tracing.stop(path=str(trace_file))
        context.close()

        assert trace_file.exists()
        assert trace_file.stat().st_size > 5000

    def test_debug_pause(self, page: Page, base_url: str):
        page.goto(base_url)

        if os.getenv("PWDEBUG") == "1":
            page.pause()

        expect(page).to_have_title("Demo Web Shop")

    def test_codegen_refactoring(self, page: Page, base_url: str):
        home = HomePage(page, base_url)
        home.open()

        details = home.search_product("Fiction").select_product_by_name("Fiction")
        assert details.get_product_price() == 24.00
