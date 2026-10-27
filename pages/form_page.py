from typing import Dict
from playwright.sync_api import Page, Locator, expect
from pages.base_page import BasePage
from data.test_data import MultiStepFormData


class MultiStepFormPage(BasePage):
    def __init__(self, page: Page, form_url: str):
        super().__init__(page, form_url)
        self.form_url = form_url

        self.first_name_input: Locator = page.locator("#firstName")
        self.last_name_input: Locator = page.locator("#lastName")
        self.email_input: Locator = page.locator("#email")
        self.phone_input: Locator = page.locator("#phone")
        self.next_step_1_btn: Locator = page.locator("#next-step-1")
        self.first_name_error: Locator = page.locator("#firstName-error")
        self.last_name_error: Locator = page.locator("#lastName-error")
        self.email_error: Locator = page.locator("#email-error")
        self.phone_error: Locator = page.locator("#phone-error")

        self.address_input: Locator = page.locator("#address")
        self.city_input: Locator = page.locator("#city")
        self.postal_code_input: Locator = page.locator("#postalCode")
        self.plan_select: Locator = page.locator("#plan")
        self.prev_step_2_btn: Locator = page.locator("#prev-step-2")
        self.next_step_2_btn: Locator = page.locator("#next-step-2")

        self.review_name: Locator = page.locator("#review-name")
        self.review_email: Locator = page.locator("#review-email")
        self.review_phone: Locator = page.locator("#review-phone")
        self.review_address: Locator = page.locator("#review-address")
        self.review_plan: Locator = page.locator("#review-plan")
        self.terms_checkbox: Locator = page.locator("#termsCheck")
        self.terms_error: Locator = page.locator("#terms-error")
        self.submit_btn: Locator = page.locator("#submit-form")

        self.confirmation_section: Locator = page.locator("#step-confirmation")
        self.confirm_heading: Locator = page.locator("#confirm-heading")
        self.record_id: Locator = page.locator("#record-id")
        self.confirmed_name: Locator = page.locator("#confirmed-name")
        self.confirmed_plan: Locator = page.locator("#confirmed-plan")

    def open(self) -> None:
        self.page.goto(self.form_url)
        self.page.wait_for_load_state("domcontentloaded")

    def fill_step_one(self, data: MultiStepFormData) -> None:
        self.first_name_input.fill(data.first_name)
        self.last_name_input.fill(data.last_name)
        self.email_input.fill(data.email)
        self.phone_input.fill(data.phone)

    def continue_to_step_two(self) -> None:
        self.next_step_1_btn.click()

    def get_step_one_values(self) -> Dict[str, str]:
        return {
            "first_name": self.first_name_input.input_value(),
            "last_name": self.last_name_input.input_value(),
            "email": self.email_input.input_value(),
            "phone": self.phone_input.input_value()
        }

    def fill_step_two(self, data: MultiStepFormData) -> None:
        self.address_input.fill(data.address)
        self.city_input.fill(data.city)
        self.postal_code_input.fill(data.postal_code)
        self.plan_select.select_option(data.plan)

    def back_to_step_one(self) -> None:
        self.prev_step_2_btn.click()

    def continue_to_step_three(self) -> None:
        self.next_step_2_btn.click()

    def accept_terms(self) -> None:
        if not self.terms_checkbox.is_checked():
            self.terms_checkbox.check()

    def submit_registration(self) -> None:
        self.submit_btn.click()

    def get_confirmation_record(self) -> Dict[str, str]:
        expect(self.confirm_heading).to_be_visible()
        return {
            "record_id": self.record_id.inner_text().strip(),
            "name": self.confirmed_name.inner_text().strip(),
            "plan": self.confirmed_plan.inner_text().strip()
        }
