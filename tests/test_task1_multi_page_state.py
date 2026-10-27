import pytest
from playwright.sync_api import Page, expect
from pages.webshop_page import HomePage, CartPage
from data.test_data import ProductState


@pytest.mark.multipage
class TestMultiPageFlow:

    def test_search_and_add_to_cart(self, page: Page, base_url: str):
        home = HomePage(page, base_url)
        cart = CartPage(page, base_url)

        # Open website and clear cart
        home.open()
        expect(page).to_have_title("Demo Web Shop")

        home.go_to_cart()
        if not cart.is_empty():
            cart.clear_all_items()

        # Search for Fiction
        home.open()
        results = home.search_product("Fiction")
        expect(page).to_have_url(f"{base_url}/search?q=Fiction")

        assert any("Fiction" in title for title in results.get_all_product_titles())

        # Open product and add 2 items
        details = results.select_product_by_name("Fiction")
        expect(page).to_have_url(f"{base_url}/fiction")

        state = details.add_to_cart(quantity=2)
        assert state.unit_price == 24.00
        assert state.expected_subtotal == 48.00

        # Verify cart and clear it
        cart = details.go_to_cart()
        expect(page).to_have_url(f"{base_url}/cart")
        cart.verify_product_in_cart(state)

        cart.clear_all_items()
        assert cart.is_empty()
