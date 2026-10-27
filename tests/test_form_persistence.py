import pytest
from playwright.sync_api import Page, expect
from pages.form_page import MultiStepFormPage
from data.test_data import MultiStepFormData


@pytest.mark.forms
class TestMultiStepFormPersistence:
    def test_multi_step_wizard_persistence_and_submission(self, page: Page, demo_form_url: str):
        form_page = MultiStepFormPage(page, demo_form_url)
        form_page.open()

        test_data = MultiStepFormData()
        form_page.fill_step_one(test_data)
        form_page.continue_to_step_two()

        expect(form_page.address_input).to_be_visible()
        form_page.fill_step_two(test_data)

        # Navigate backwards to verify persistence
        form_page.back_to_step_one()
        expect(form_page.first_name_input).to_be_visible()

        persisted = form_page.get_step_one_values()
        assert persisted["first_name"] == test_data.first_name
        assert persisted["last_name"] == test_data.last_name
        assert persisted["email"] == test_data.email
        assert persisted["phone"] == test_data.phone

        # Proceed to step 3 and submit
        form_page.continue_to_step_two()
        form_page.continue_to_step_three()
        expect(form_page.review_name).to_be_visible()

        form_page.accept_terms()
        form_page.submit_registration()

        record = form_page.get_confirmation_record()
        assert record["record_id"].startswith("REC-")

    def test_negative_step_one_validation_missing_and_invalid_email(self, page: Page, demo_form_url: str):
        form_page = MultiStepFormPage(page, demo_form_url)
        form_page.open()

        form_page.continue_to_step_two()
        expect(form_page.first_name_error).to_be_visible()
        expect(form_page.address_input).not_to_be_visible()

        form_page.first_name_input.fill("Taylor")
        form_page.last_name_input.fill("Swift")
        form_page.phone_input.fill("1234567")
        form_page.email_input.fill("invalid-email")
        form_page.continue_to_step_two()

        expect(form_page.email_error).to_be_visible()
        expect(form_page.address_input).not_to_be_visible()

    def test_negative_step_three_unaccepted_terms_blocked(self, page: Page, demo_form_url: str):
        form_page = MultiStepFormPage(page, demo_form_url)
        form_page.open()
        form_page.fill_step_one(MultiStepFormData())
        form_page.continue_to_step_two()
        form_page.fill_step_two(MultiStepFormData())
        form_page.continue_to_step_three()

        expect(form_page.terms_checkbox).not_to_be_checked()
        form_page.submit_registration()

        expect(form_page.terms_error).to_be_visible()
        expect(form_page.confirmation_section).not_to_be_visible()
