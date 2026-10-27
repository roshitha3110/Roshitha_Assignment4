import pytest
from typing import Callable, Any
from playwright.sync_api import Page, BrowserContext, Route, Request, expect
from pages.webshop_page import HomePage, LoginPage
from data.test_data import TestConfig


class SafeSessionRetryHandler:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.max_retries = 1

    def execute_with_auth_recovery(self, action_func: Callable[[], Any]) -> Any:
        retries = 0
        while retries <= self.max_retries:
            result = action_func()
            if "/login" in self.page.url:
                if retries >= self.max_retries:
                    raise PermissionError("Session expired and retry limit reached.")
                login_page = LoginPage(self.page, self.base_url)
                login_page.login(TestConfig.DEMO_USER_EMAIL, TestConfig.DEMO_USER_PASSWORD)
                self.page.wait_for_load_state("domcontentloaded")
                retries += 1
            else:
                return result
        return None


@pytest.mark.auth
class TestSessionExpiryAndOAuth:
    def test_authenticated_dependency_profile_access(self, authenticated_page: Page, base_url: str):
        home = HomePage(authenticated_page, base_url)
        home.open()
        home.account_link.click()
        authenticated_page.wait_for_load_state("domcontentloaded")
        expect(authenticated_page).to_have_url(f"{base_url}/customer/info")
        expect(authenticated_page.locator("#Email")).to_have_value(TestConfig.DEMO_USER_EMAIL)

    def test_session_expiry_detection_and_safe_retry(self, authenticated_page: Page, authenticated_context: BrowserContext, base_url: str):
        home = HomePage(authenticated_page, base_url)
        home.open()
        expect(home.account_link).to_be_visible()

        authenticated_context.clear_cookies()
        handler = SafeSessionRetryHandler(authenticated_page, base_url)
        handler.execute_with_auth_recovery(lambda: authenticated_page.goto(f"{base_url}/customer/info"))

        expect(authenticated_page).to_have_url(f"{base_url}/customer/info")
        expect(authenticated_page.locator("#Email")).to_have_value(TestConfig.DEMO_USER_EMAIL)

    def test_simulated_oauth2_mfa_authorization_flow(self, page: Page):
        idp_auth = "https://idp.enterprise-sso.com/oauth/authorize"
        idp_mfa = "https://idp.enterprise-sso.com/oauth/mfa"
        callback = "https://demowebshop.tricentis.com/oauth/callback"

        page.route(lambda u: "idp.enterprise-sso.com/oauth/authorize" in u, lambda r: r.fulfill(
            status=200, content_type="text/html",
            body="""<h2>SSO</h2><button id="btn-login" onclick="location.href='/oauth/mfa'">Sign in</button>"""
        ))
        page.route(lambda u: "idp.enterprise-sso.com/oauth/mfa" in u, lambda r: r.fulfill(
            status=200, content_type="text/html",
            body="""<h2>2FA</h2><input id="totp-code"><div id="mfa-err" style="display:none;color:red;">Invalid code</div>
            <button id="btn-verify" onclick="if(document.getElementById('totp-code').value==='654321') location.href='https://demowebshop.tricentis.com/oauth/callback?code=AUTH99&state=xyz'; else document.getElementById('mfa-err').style.display='block';">Verify</button>"""
        ))
        page.route(lambda u: "demowebshop.tricentis.com/oauth/callback" in u.split("?")[0], lambda r: r.fulfill(
            status=200, content_type="text/html", body=f"<h1 id='status'>Auth Success</h1><p id='url'>{r.request.url}</p>"
        ))

        page.goto(f"{idp_auth}?client_id=demo&redirect_uri={callback}")
        page.click("#btn-login")

        page.fill("#totp-code", "000000")
        page.click("#btn-verify")
        expect(page.locator("#mfa-err")).to_be_visible()

        page.fill("#totp-code", "654321")
        page.click("#btn-verify")
        expect(page.locator("#status")).to_be_visible()
        expect(page.locator("#url")).to_contain_text("code=AUTH99")
