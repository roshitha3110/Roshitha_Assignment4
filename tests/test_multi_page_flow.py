import pytest
import logging
from playwright.sync_api import Page, expect
from pages.webshop_page import HomePage, SearchResultsPage, ProductDetailsPage, CartPage
from data.test_data import ProductState

logger = logging.getLogger(__name__)


@pytest.mark.multipage
class TestMultiPageFlow:
    def test_search_and_add_to_cart_state_verification(self, page: Page, base_url: str):
        home_page = HomePage(page, base_url)
        cart_page = CartPage(page, base_url)

        home_page.open()
        expect(page).to_have_title("Demo Web Shop")

        home_page.go_to_cart()
        if not cart_page.is_empty():
            cart_page.clear_all_items()

        home_page.open()
        search_query = "Fiction"
        search_results: SearchResultsPage = home_page.search_product(search_query)

        expect(page).to_have_url(f"{base_url}/search?q={search_query}")
        titles = search_results.get_all_product_titles()
        assert any(search_query in t for t in titles)

        details_page: ProductDetailsPage = search_results.select_product_by_name("Fiction")
        expect(page).to_have_url(f"{base_url}/fiction")

        product_state: ProductState = details_page.add_to_cart(quantity=2)
        assert product_state.unit_price == 24.00
        assert product_state.expected_subtotal == 48.00

        cart_page = details_page.go_to_cart()
        expect(page).to_have_url(f"{base_url}/cart")
        cart_page.verify_product_in_cart(product_state)

        cart_page.clear_all_items()
        assert cart_page.is_empty()
