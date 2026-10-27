from typing import Optional
from playwright.sync_api import Page, Response


class BasePage:
    def __init__(self, page: Page, base_url: str = ""):
        self.page = page
        self.base_url = base_url.rstrip("/")

    def navigate(self, path: str = "/") -> Optional[Response]:
        if path.startswith("http://") or path.startswith("https://") or path.startswith("file://"):
            target = path
        else:
            clean_path = path if path.startswith("/") else f"/{path}"
            target = f"{self.base_url}{clean_path}"
        return self.page.goto(target, wait_until="domcontentloaded")

    def get_title(self) -> str:
        return self.page.title()

    def get_current_url(self) -> str:
        return self.page.url

    def take_screenshot(self, filepath: str) -> None:
        self.page.screenshot(path=filepath, full_page=True)
