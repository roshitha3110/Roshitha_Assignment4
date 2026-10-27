import pytest
from playwright.sync_api import Page, expect
from pages.webshop_page import HomePage, CartPage, ProductDetailsPage


@pytest.mark.conditional
class TestConditionalUIExecution:

    def test_conditional_cart_handling(self, page: Page, base_url: str):
        cart = CartPage(page, base_url)
        cart.navigate("/cart")

        if cart.is_empty():
            print("Empty cart: Adding product")
            page.goto(f"{base_url}/fiction")
            ProductDetailsPage(page, base_url).add_to_cart(quantity=1)
            cart.navigate("/cart")
            assert not cart.is_empty()
        else:
            print("Cart has items: Clearing cart")
            cart.clear_all_items()
            assert cart.is_empty()

    def test_both_cart_branches(self, page: Page, base_url: str):
        cart = CartPage(page, base_url)
        cart.navigate("/cart")

        # Make cart empty first
        if not cart.is_empty():
            cart.clear_all_items()

        expect(cart.empty_cart_msg).to_be_visible()

        # Add a product
        page.goto(f"{base_url}/fiction")
        ProductDetailsPage(page, base_url).add_to_cart(quantity=1)
        cart.navigate("/cart")
        expect(cart.cart_rows.first).to_be_visible()

        # Clear the cart
        cart.clear_all_items()
        expect(cart.empty_cart_msg).to_be_visible()

    def test_conditional_login_header(self, page: Page, base_url: str):
        home = HomePage(page, base_url)
        home.open()

        if home.is_logged_in():
            print("User is logged in")
            expect(home.logout_link).to_be_visible()
        else:
            print("User is not logged in")
            expect(home.login_link).to_be_visible()
            login_page = home.go_to_login()
            expect(login_page.email_input).to_be_visible()
