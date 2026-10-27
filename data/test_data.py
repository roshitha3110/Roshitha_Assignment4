import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class ProductState:
    """Carries product state across multiple navigation steps without brittle globals."""
    name: str = ""
    unit_price: float = 0.0
    quantity: int = 1
    product_url: str = ""
    attributes: dict = field(default_factory=dict)

    @property
    def expected_subtotal(self) -> float:
        return round(self.unit_price * self.quantity, 2)

    def update_from_details(self, name: str, price: float, quantity: int = 1, url: str = "") -> None:
        self.name = name.strip()
        self.unit_price = price
        self.quantity = quantity
        self.product_url = url


@dataclass
class MultiStepFormData:
    """Data container for multi-step form inputs and validation."""
    first_name: str = "Alex"
    last_name: str = "Morgan"
    email: str = "alex.morgan@example.com"
    phone: str = "+1-555-0199"
    address: str = "123 Automation Blvd, Suite 400"
    city: str = "TechCity"
    postal_code: str = "94016"
    plan: str = "Enterprise"


class TestConfig:
    """Loads configuration and credentials from environment variables."""
    BASE_URL: str = os.getenv("BASE_URL", "https://demowebshop.tricentis.com")
    DEMO_USER_EMAIL: str = os.getenv("DEMO_USER_EMAIL", "demowebshop_tester_2026@sampleqa.org")
    DEMO_USER_PASSWORD: str = os.getenv("DEMO_USER_PASSWORD", "Password123!")
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
    BROWSER_NAME: str = os.getenv("BROWSER", "chromium")
    SLOW_MO: int = int(os.getenv("SLOW_MO", "0"))

    _raw_auth_path = os.getenv("AUTH_STATE_PATH", "auth/state.json")
    AUTH_STATE_PATH: Path = (
        Path(_raw_auth_path) if Path(_raw_auth_path).is_absolute() else (PROJECT_ROOT / _raw_auth_path)
    )

    _raw_artifacts_dir = os.getenv("ARTIFACTS_DIR", "artifacts")
    ARTIFACTS_DIR: Path = (
        Path(_raw_artifacts_dir) if Path(_raw_artifacts_dir).is_absolute() else (PROJECT_ROOT / _raw_artifacts_dir)
    )
    SCREENSHOTS_DIR: Path = ARTIFACTS_DIR / "screenshots"
    TRACES_DIR: Path = ARTIFACTS_DIR / "traces"
    REPORTS_DIR: Path = ARTIFACTS_DIR / "reports"
    STATIC_FORM_PATH: Path = PROJECT_ROOT / "static" / "multi_step_form.html"
