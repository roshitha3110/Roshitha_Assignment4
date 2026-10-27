import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from data.test_data import TestConfig


def perform_auth_setup(output_state_path: str = None) -> Path:
    state_path = Path(output_state_path) if output_state_path else TestConfig.AUTH_STATE_PATH
    state_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[*] Starting authentication setup for: {TestConfig.DEMO_USER_EMAIL}")
    print(f"[*] Target URL: {TestConfig.BASE_URL}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto(f"{TestConfig.BASE_URL}/login", wait_until="domcontentloaded")
        page.fill("#Email", TestConfig.DEMO_USER_EMAIL)
        page.fill("#Password", TestConfig.DEMO_USER_PASSWORD)
        page.check("#RememberMe")
        page.click("input[value='Log in']")
        page.wait_for_load_state("domcontentloaded")

        account_link = page.locator(".header-links .account")
        if not account_link.is_visible():
            raise RuntimeError(f"Authentication failed for {TestConfig.DEMO_USER_EMAIL}")

        print(f"[+] Login verified for: {account_link.inner_text().strip()}")
        context.storage_state(path=str(state_path))
        print(f"[+] Storage state saved to: {state_path}")
        browser.close()

    return state_path


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    perform_auth_setup(target)
