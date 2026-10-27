import pytest
import logging
from playwright.sync_api import Page, expect
from pages.webshop_page import HomePage, CartPage, ProductDetailsPage

logger = logging.getLogger(__name__)


@pytest.mark.conditional
class TestConditionalUIExecution:
    def test_conditional_cart_handling_empty_vs_populated(self, page: Page, base_url: str):
        cart_page = CartPage(page, base_url)
        cart_page.navigate("/cart")

        if cart_page.is_empty():
            print("\n>>> [BRANCH TAKEN]: BRANCH_EMPTY_CART - Adding item.")
            page.goto(f"{base_url}/fiction")
            details = ProductDetailsPage(page, base_url)
            details.add_to_cart(quantity=1)
            cart_page.navigate("/cart")
            assert not cart_page.is_empty()
        else:
            print("\n>>> [BRANCH TAKEN]: BRANCH_POPULATED_CART - Clearing cart.")
            cart_page.clear_all_items()
            assert cart_page.is_empty()

    def test_controlled_both_branches_execution(self, page: Page, base_url: str):
        cart_page = CartPage(page, base_url)
        cart_page.navigate("/cart")
        if not cart_page.is_empty():
            cart_page.clear_all_items()

        # Branch A: Empty handling
        assert cart_page.empty_cart_msg.is_visible()
        page.goto(f"{base_url}/fiction")
        details = ProductDetailsPage(page, base_url)
        details.add_to_cart(quantity=1)
        cart_page.navigate("/cart")
        expect(cart_page.cart_rows.first).to_be_visible()

        # Branch B: Populated handling
        assert not cart_page.is_empty()
        cart_page.clear_all_items()
        expect(cart_page.empty_cart_msg).to_be_visible()

    def test_conditional_auth_header_state(self, page: Page, base_url: str):
        home = HomePage(page, base_url)
        home.open()

        if home.is_logged_in():
            print(f"\n>>> [BRANCH TAKEN]: AUTH_SIGNED_IN ({home.get_logged_in_user_email()})")
            expect(home.logout_link).to_be_visible()
        else:
            print("\n>>> [BRANCH TAKEN]: AUTH_ANONYMOUS")
            expect(home.login_link).to_be_visible()
            login_page = home.go_to_login()
            expect(login_page.email_input).to_be_visible()
