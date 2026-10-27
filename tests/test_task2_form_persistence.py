import pytest
from playwright.sync_api import Page, expect
from pages.form_page import MultiStepFormPage
from data.test_data import MultiStepFormData


@pytest.mark.forms
class TestMultiStepFormPersistence:

    def test_form_persistence_and_submission(self, page: Page, demo_form_url: str):
        form = MultiStepFormPage(page, demo_form_url)
        data = MultiStepFormData()
        form.open()

        # Fill step 1 and step 2
        form.fill_step_one(data)
        form.continue_to_step_two()
        form.fill_step_two(data)

        # Go back and check saved values
        form.back_to_step_one()
        values = form.get_step_one_values()

        assert values["first_name"] == data.first_name
        assert values["last_name"] == data.last_name
        assert values["email"] == data.email
        assert values["phone"] == data.phone

        # Submit the form
        form.continue_to_step_two()
        form.continue_to_step_three()
        expect(form.review_name).to_be_visible()

        form.accept_terms()
        form.submit_registration()

        assert form.get_confirmation_record()["record_id"].startswith("REC-")

    def test_invalid_step_one_details(self, page: Page, demo_form_url: str):
        form = MultiStepFormPage(page, demo_form_url)
        form.open()

        # Check required fields
        form.continue_to_step_two()
        expect(form.first_name_error).to_be_visible()
        expect(form.address_input).not_to_be_visible()

        # Enter invalid email
        form.first_name_input.fill("Taylor")
        form.last_name_input.fill("Swift")
        form.phone_input.fill("1234567")
        form.email_input.fill("invalid-email")
        form.continue_to_step_two()

        expect(form.email_error).to_be_visible()
        expect(form.address_input).not_to_be_visible()

    def test_submit_without_accepting_terms(self, page: Page, demo_form_url: str):
        form = MultiStepFormPage(page, demo_form_url)
        data = MultiStepFormData()
        form.open()

        form.fill_step_one(data)
        form.continue_to_step_two()
        form.fill_step_two(data)
        form.continue_to_step_three()

        # Submit without accepting terms
        expect(form.terms_checkbox).not_to_be_checked()
        form.submit_registration()

        expect(form.terms_error).to_be_visible()
        expect(form.confirmation_section).not_to_be_visible()
