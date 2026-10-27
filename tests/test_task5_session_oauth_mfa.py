import pytest
from playwright.sync_api import Page, BrowserContext, expect
from pages.webshop_page import HomePage, LoginPage
from data.test_data import TestConfig


@pytest.mark.auth
class TestSessionExpiryAndOAuth:

    def test_authenticated_profile_access(self, authenticated_page: Page, base_url: str):
        home = HomePage(authenticated_page, base_url)
        home.open()
        home.account_link.click()

        expect(authenticated_page).to_have_url(f"{base_url}/customer/info")
        expect(authenticated_page.locator("#Email")).to_have_value(
            TestConfig.DEMO_USER_EMAIL
        )

    def test_session_expiry_and_recovery(
        self,
        authenticated_page: Page,
        authenticated_context: BrowserContext,
        base_url: str
    ):
        # Clear cookies to simulate session expiry
        authenticated_context.clear_cookies()

        # Try to open the profile page
        authenticated_page.goto(f"{base_url}/customer/info")

        # Log in again if redirected to login
        if "/login" in authenticated_page.url:
            LoginPage(authenticated_page, base_url).login(
                TestConfig.DEMO_USER_EMAIL,
                TestConfig.DEMO_USER_PASSWORD
            )
            authenticated_page.goto(f"{base_url}/customer/info")

        expect(authenticated_page.locator("#Email")).to_have_value(
            TestConfig.DEMO_USER_EMAIL
        )

    def test_simulated_oauth_mfa(self, page: Page):
        callback = "https://demowebshop.tricentis.com/oauth/callback"

        # Mock the SSO login page
        page.route("**/oauth/authorize*", lambda route: route.fulfill(
            status=200,
            content_type="text/html",
            body="""
                <button id="btn-login"
                    onclick="location.href='/oauth/mfa'">
                    Sign in
                </button>
            """
        ))

        # Mock the MFA page
        page.route("**/oauth/mfa*", lambda route: route.fulfill(
            status=200,
            content_type="text/html",
            body="""
                <h2>Two-Factor Authentication</h2>
                <input id="totp-code">
                <p id="mfa-err" style="display:none">Invalid code</p>
                <button id="btn-verify" onclick="
                    if (document.querySelector('#totp-code').value === '654321') {
                        location.href = 'https://demowebshop.tricentis.com/oauth/callback?code=AUTH99';
                    } else {
                        document.querySelector('#mfa-err').style.display = 'block';
                    }
                ">Verify</button>
            """
        ))

        # Mock the callback page
        page.route("**/oauth/callback*", lambda route: route.fulfill(
            status=200,
            content_type="text/html",
            body=f"""
                <h1 id="status">Auth Success</h1>
                <p id="url">{route.request.url}</p>
            """
        ))

        page.goto("https://idp.enterprise-sso.com/oauth/authorize")
        page.click("#btn-login")

        # Check invalid MFA code
        page.fill("#totp-code", "000000")
        page.click("#btn-verify")
        expect(page.locator("#mfa-err")).to_be_visible()

        # Check valid MFA code
        page.fill("#totp-code", "654321")
        page.click("#btn-verify")

        expect(page.locator("#status")).to_be_visible()
        expect(page.locator("#url")).to_contain_text("code=AUTH99")
