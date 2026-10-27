import pytest
from pathlib import Path
from playwright.sync_api import Browser, BrowserContext, Page, expect
from pages.webshop_page import HomePage
from data.test_data import TestConfig


@pytest.mark.auth
class TestAuthenticatedSession:
    def test_reuse_saved_storage_state_without_relogin(self, authenticated_page: Page, base_url: str):
        home = HomePage(authenticated_page, base_url)
        home.open()
        expect(home.account_link).to_be_visible()
        expect(home.logout_link).to_be_visible()
        expect(home.login_link).not_to_be_visible()
        assert home.get_logged_in_user_email() == TestConfig.DEMO_USER_EMAIL

    def test_inject_custom_cookie_before_navigation(self, browser_instance: Browser, auth_state_path: Path, base_url: str):
        context: BrowserContext = browser_instance.new_context(storage_state=str(auth_state_path))
        test_cookie = {
            "name": "qa_experiment_variant",
            "value": "variant_checkout_v2",
            "domain": "demowebshop.tricentis.com",
            "path": "/"
        }
        context.add_cookies([test_cookie])
        page = context.new_page()
        page.goto(base_url, wait_until="domcontentloaded")

        cookies = context.cookies()
        matched = [c for c in cookies if c["name"] == "qa_experiment_variant"]
        assert len(matched) == 1
        assert matched[0]["value"] == "variant_checkout_v2"
        context.close()

    def test_inject_local_storage_before_navigation(self, browser_instance: Browser, auth_state_path: Path, base_url: str):
        context = browser_instance.new_context(storage_state=str(auth_state_path))
        page = context.new_page()
        page.add_init_script("""
            window.localStorage.setItem('user_preference_theme', 'dark_mode');
            window.localStorage.setItem('automation_run_id', 'RUN_2026_PLAYWRIGHT');
        """)
        page.goto(base_url, wait_until="domcontentloaded")

        theme = page.evaluate("() => window.localStorage.getItem('user_preference_theme')")
        run_id = page.evaluate("() => window.localStorage.getItem('automation_run_id')")
        assert theme == "dark_mode"
        assert run_id == "RUN_2026_PLAYWRIGHT"
        context.close()

    def test_security_hygiene_credentials_in_env_and_gitignored(self):
        project_root = Path(__file__).resolve().parent.parent
        gitignore_path = project_root / ".gitignore"
        assert gitignore_path.exists()
        content = gitignore_path.read_text()
        assert ".env" in content
        assert "auth/state.json" in content or "*.state.json" in content
