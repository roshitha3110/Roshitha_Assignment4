import os
import sys
import pytest
from pathlib import Path
from typing import Generator
from playwright.sync_api import Playwright, Browser, BrowserContext, Page, sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.test_data import TestConfig
from scripts.auth_setup import perform_auth_setup

TestConfig.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
TestConfig.TRACES_DIR.mkdir(parents=True, exist_ok=True)
TestConfig.REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def base_url() -> str:
    return TestConfig.BASE_URL


@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser_instance(playwright_instance: Playwright) -> Generator[Browser, None, None]:
    browser = playwright_instance.chromium.launch(
        headless=TestConfig.HEADLESS,
        slow_mo=TestConfig.SLOW_MO
    )
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def browser_context(browser_instance: Browser, request: pytest.FixtureRequest) -> Generator[BrowserContext, None, None]:
    context = browser_instance.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True
    )
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield context

    test_failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
    test_slug = request.node.name.replace("/", "_").replace(":", "_")
    if test_failed:
        trace_path = TestConfig.TRACES_DIR / f"{test_slug}_trace.zip"
        try:
            context.tracing.stop(path=str(trace_path))
        except Exception:
            pass
    else:
        try:
            context.tracing.stop()
        except Exception:
            pass
    context.close()


@pytest.fixture(scope="function")
def page(browser_context: BrowserContext, request: pytest.FixtureRequest) -> Generator[Page, None, None]:
    page = browser_context.new_page()
    request.node.playwright_page = page
    yield page
    if not page.is_closed():
        page.close()


@pytest.fixture(scope="session")
def auth_state_path() -> Path:
    state_file = TestConfig.AUTH_STATE_PATH
    if not state_file.exists() or state_file.stat().st_size == 0:
        perform_auth_setup(str(state_file))
    return state_file


@pytest.fixture(scope="function")
def authenticated_context(browser_instance: Browser, auth_state_path: Path) -> Generator[BrowserContext, None, None]:
    context = browser_instance.new_context(
        storage_state=str(auth_state_path),
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def authenticated_page(authenticated_context: BrowserContext, request: pytest.FixtureRequest) -> Generator[Page, None, None]:
    page = authenticated_context.new_page()
    request.node.playwright_page = page
    yield page
    if not page.is_closed():
        page.close()


@pytest.fixture(scope="session")
def demo_form_url() -> str:
    return f"file://{TestConfig.STATIC_FORM_PATH.resolve()}"


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when == "call" and report.failed:
        page: Page = getattr(item, "playwright_page", None)
        if page and not page.is_closed():
            test_slug = item.name.replace("/", "_").replace(":", "_")
            screenshot_path = TestConfig.SCREENSHOTS_DIR / f"{test_slug}_failure.png"
            try:
                page.screenshot(path=str(screenshot_path), full_page=True)
                extra = getattr(report, "extras", [])
                try:
                    import pytest_html
                    extra.append(pytest_html.extras.image(str(screenshot_path), name="Failure Screenshot"))
                    report.extras = extra
                except Exception:
                    pass
            except Exception:
                pass
