from pathlib import Path
import os
import pytest
from playwright.sync_api import Browser, Page, expect
from pages.webshop_page import HomePage


@pytest.mark.auth
class TestAuthenticatedSession:

    # 1. Reuse saved login session
    def test_reuse_saved_session(self, authenticated_page: Page, base_url: str):
        home = HomePage(authenticated_page, base_url)
        home.open()

        expect(home.account_link).to_be_visible()
        expect(home.logout_link).to_be_visible()
        expect(home.login_link).not_to_be_visible()

        email = os.getenv("DEMO_USER_EMAIL")
        assert email, "DEMO_USER_EMAIL is missing from environment"
        assert home.get_logged_in_user_email() == email

        print("PASS: Saved session reused")

    # 2. Add a cookie before opening the website
    def test_add_cookie(self, browser_instance: Browser, auth_state_path: Path, base_url: str):
        context = browser_instance.new_context(
            storage_state=str(auth_state_path)
        )

        try:
            context.add_cookies([{
                "name": "qa_experiment_variant",
                "value": "variant_checkout_v2",
                "domain": "demowebshop.tricentis.com",
                "path": "/"
            }])

            page = context.new_page()
            page.goto(base_url)

            cookie = next(
                c for c in context.cookies()
                if c["name"] == "qa_experiment_variant"
            )

            assert cookie["value"] == "variant_checkout_v2"
            print("PASS: Cookie added")

        finally:
            context.close()

    # 3. Add local storage before opening