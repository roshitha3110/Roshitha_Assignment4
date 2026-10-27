import re
from typing import List, Optional, Dict
from playwright.sync_api import Page, Locator, expect
from pages.base_page import BasePage
from data.test_data import ProductState


class HomePage(BasePage):
    def __init__(self, page: Page, base_url: str = ""):
        super().__init__(page, base_url)
        self.search_input: Locator = page.locator("#small-searchterms")
        self.search_button: Locator = page.locator("input[value='Search']")
        self.cart_link: Locator = page.locator("#topcartlink a")
        self.cart_qty_badge: Locator = page.locator("#topcartlink .cart-qty")
        self.login_link: Locator = page.locator(".header-links a.ico-login")
        self.logout_link: Locator = page.locator(".header-links a.ico-logout")
        self.account_link: Locator = page.locator(".header-links .account")
        self.register_link: Locator = page.locator(".header-links a.ico-register")

    def open(self) -> None:
        self.navigate("/")

    def search_product(self, term: str) -> "SearchResultsPage":
        self.search_input.fill(term)
        self.search_button.click()
        self.page.wait_for_load_state("domcontentloaded")
        return SearchResultsPage(self.page, self.base_url)

    def is_logged_in(self) -> bool:
        return self.account_link.is_visible()

    def get_logged_in_user_email(self) -> Optional[str]:
        if self.is_logged_in():
            return self.account_link.inner_text().strip()
        return None

    def logout(self) -> None:
        if self.logout_link.is_visible():
            self.logout_link.click()
            self.page.wait_for_load_state("domcontentloaded")

    def go_to_cart(self) -> "CartPage":
        self.cart_link.click()
        self.page.wait_for_load_state("domcontentloaded")
        return CartPage(self.page, self.base_url)

    def go_to_login(self) -> "LoginPage":
        self.login_link.click()
        self.page.wait_for_load_state("domcontentloaded")
        return LoginPage(self.page, self.base_url)


class SearchResultsPage(BasePage):
    def __init__(self, page: Page, base_url: str = ""):
        super().__init__(page, base_url)
        self.product_items: Locator = page.locator(".product-item")
        self.no_results: Locator = page.locator(".search-results .result")

    def get_all_product_titles(self) -> List[str]:
        return [title.strip() for title in self.product_items.locator(".product-title a").all_inner_texts()]

    def select_product_by_name(self, product_name: str) -> "ProductDetailsPage":
        target_card = self.product_items.filter(has=self.page.locator(f".product-title a:has-text('{product_name}')"))
        expect(target_card.first).to_be_visible()
        target_card.locator(".product-title a").first.click()
        self.page.wait_for_load_state("domcontentloaded")
        return ProductDetailsPage(self.page, self.base_url)


class ProductDetailsPage(BasePage):
    def __init__(self, page: Page, base_url: str = ""):
        super().__init__(page, base_url)
        self.product_title: Locator = page.locator(".product-name h1")
        self.product_price: Locator = page.locator(".price-value-45, .actual-price, .product-price span").first
        self.quantity_input: Locator = page.locator(".add-to-cart-panel input[id^='addtocart_'][id$='_EnteredQuantity']")
        self.add_to_cart_button: Locator = page.locator(".add-to-cart-panel input[value='Add to cart']")
        self.notification_bar: Locator = page.locator("#bar-notification.success, .bar-notification.success")
        self.notification_close: Locator = page.locator("#bar-notification .close")
        self.cart_link: Locator = page.locator("#topcartlink a")

    def get_product_name(self) -> str:
        return self.product_title.inner_text().strip()

    def get_product_price(self) -> float:
        raw_price = self.product_price.inner_text().strip()
        clean = re.sub(r"[^\d.]", "", raw_price)
        return float(clean)

    def set_quantity(self, quantity: int) -> None:
        if self.quantity_input.is_visible():
            self.quantity_input.fill(str(quantity))

    def add_to_cart(self, quantity: int = 1) -> ProductState:
        product_name = self.get_product_name()
        unit_price = self.get_product_price()
        if quantity != 1:
            self.set_quantity(quantity)

        self.add_to_cart_button.click()
        expect(self.notification_bar).to_be_visible(timeout=10000)

        return ProductState(
            name=product_name,
            unit_price=unit_price,
            quantity=quantity,
            product_url=self.page.url
        )

    def go_to_cart(self) -> "CartPage":
        self.cart_link.click()
        self.page.wait_for_load_state("domcontentloaded")
        return CartPage(self.page, self.base_url)


class CartPage(BasePage):
    def __init__(self, page: Page, base_url: str = ""):
        super().__init__(page, base_url)
        self.cart_rows: Locator = page.locator(".cart tbody tr, .cart-item-row")
        self.order_summary: Locator = page.locator(".order-summary-content")
        self.update_cart_btn: Locator = page.locator("input[name='updatecart']")

    def is_empty(self) -> bool:
        return self.empty_cart_msg.is_visible()

    def get_cart_items_data(self) -> List[Dict[str, str]]:
        items = []
        count = self.cart_rows.count()
        for i in range(count):
            row = self.cart_rows.nth(i)
            name = row.locator(".product-name").inner_text().strip()
            unit_price = row.locator(".unit-price").inner_text().strip()
            qty = row.locator(".qty-input").input_value()
            subtotal = row.locator(".product-subtotal").inner_text().strip()
            items.append({
                "name": name,
                "unit_price": float(re.sub(r"[^\d.]", "", unit_price)),
                "quantity": int(qty),
                "subtotal": float(re.sub(r"[^\d.]", "", subtotal))
            })
        return items

    def verify_product_in_cart(self, expected_state: ProductState) -> None:
        matching_rows = self.cart_rows.filter(
            has=self.page.locator(f".product-name:has-text('{expected_state.name}')")
        )
        expect(matching_rows.first).to_be_visible()

        row = matching_rows.first
        raw_unit_price = row.locator(".unit-price").inner_text().strip()
        unit_val = float(re.sub(r"[^\d.]", "", raw_unit_price))
        assert unit_val == expected_state.unit_price

        row_qty = int(row.locator(".qty-input").input_value())
        assert row_qty == expected_state.quantity

        raw_subtotal = row.locator(".product-subtotal").inner_text().strip()
        subtotal_val = float(re.sub(r"[^\d.]", "", raw_subtotal))
        assert subtotal_val == expected_state.expected_subtotal

    def clear_all_items(self) -> None:
        if not self.is_empty() and self.cart_rows.count() > 0:
            remove_checkboxes = self.page.locator("input[name='removefromcart']")
            for i in range(remove_checkboxes.count()):
                remove_checkboxes.nth(i).check()
            self.update_cart_btn.click()
            self.page.wait_for_load_state("domcontentloaded")


class LoginPage(BasePage):
    def __init__(self, page: Page, base_url: str = ""):
        super().__init__(page, base_url)
        self.email_input: Locator = page.locator("#Email")
        self.password_input: Locator = page.locator("#Password")
        self.remember_me_check: Locator = page.locator("#RememberMe")
        self.login_button: Locator = page.locator("input[value='Log in']")

    def open(self) -> None:
        self.navigate("/login")

    def login(self, email: str, password: str, remember_me: bool = True) -> None:
        self.email_input.fill(email)
        self.password_input.fill(password)
        if remember_me and not self.remember_me_check.is_checked():
            self.remember_me_check.check()
        self.login_button.click()
        self.page.wait_for_load_state("domcontentloaded")
