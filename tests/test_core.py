import unittest
from unittest.mock import patch

import automate2
from fundrel_automation.core.accounts import prepare_account_config, validate_account
from fundrel_automation.core.config import apply_env_defaults, parse_proxies, settings_from_env
from fundrel_automation.core.errors import AccountAlreadyExists, AutomationError
from fundrel_automation.core.results import (
    RESULT_CREATED,
    RESULT_SUCCESS_NOT_CREATED,
    RESULT_UNABLE_TO_VERIFY,
    RESULT_WE_FOUND_ANOTHER_ACCOUNT,
    apply_outcome_to_account,
    outcome_from_exception,
    outcome_from_result,
)
from fundrel_automation.core.routing import HOMEPAGE_URL, select_proxy, select_url_and_proxy
from dev import env_lines_from_settings
from fundrel_automation.core.status import (
    STATUS_ANOTHER_ACCOUNT,
    STATUS_PENDING,
    classify_account,
    reset_to_pending,
)


class CoreHelperTests(unittest.TestCase):
    def test_parse_proxies_accepts_plain_text_and_rejects_bad_values(self):
        proxy = parse_proxies("host:1000:user:pass")[0]
        self.assertEqual(proxy["host"], "host")
        self.assertEqual(proxy["last_use"], 0)

        with self.assertRaises(ValueError):
            parse_proxies("bad")

    def test_settings_can_be_built_from_env_values(self):
        settings = settings_from_env(
            {
                "FUNDREL_EDGE_PATH": "C:\\Edge\\msedge.exe",
                "FUNDREL_PROXIES": "host:1000:user:pass",
            }
        )

        self.assertEqual(settings["edge_path"], "C:\\Edge\\msedge.exe")
        self.assertEqual(settings["proxies"][0]["host"], "host")

    def test_env_defaults_only_fill_empty_settings(self):
        settings = apply_env_defaults(
            {"edge_path": "custom", "proxies": []},
            {"FUNDREL_PROXIES": "host:1:u:p"},
        )

        self.assertEqual(settings["edge_path"], "custom")
        self.assertEqual(settings["proxies"][0]["host"], "host")

    def test_prepare_account_config_generates_username_and_extends_short_password(self):
        account = {
            "email": "person@example.com",
            "password": "pw",
            "firstName": "A+",
            "lastName": "B-",
            "month": "1",
            "day": "1",
            "year": "1990",
            "address": "123",
            "city": "Toronto",
            "province": "ON",
            "postcode": "A1A 1A1",
        }

        config = prepare_account_config(account, {})

        self.assertTrue(config["username"].startswith("ba"))
        self.assertEqual(config["password"], "pwb")
        self.assertEqual(account["password"], "pwb")
        self.assertTrue(validate_account(config)[0])

    def test_outcomes_apply_account_flags_without_reason_matching(self):
        outcome = outcome_from_result(False, RESULT_WE_FOUND_ANOTHER_ACCOUNT)
        account = {}

        apply_outcome_to_account(account, outcome, "shot.png", username="user", timestamp="now")

        self.assertTrue(account["success"])
        self.assertFalse(account["created"])
        self.assertTrue(account["we_found_another_account"])
        self.assertEqual(classify_account(account), STATUS_ANOTHER_ACCOUNT)

    def test_exception_outcomes_handle_typed_and_generic_errors(self):
        existing = outcome_from_exception(AccountAlreadyExists())
        failure = outcome_from_exception(AutomationError("x"))

        self.assertTrue(existing.skipped)
        self.assertFalse(existing.success)
        self.assertEqual(failure.reason, "x")

    def test_pending_reset_clears_terminal_flags(self):
        account = {
            "ran": True,
            "success": True,
            "unable_to_verify": True,
            "reason": "Unable to verify data",
            "screenshot": "shot.png",
            "timestamp": "now",
        }

        reset_to_pending(account)

        self.assertEqual(classify_account(account), STATUS_PENDING)
        self.assertNotIn("screenshot", account)
        self.assertNotIn("timestamp", account)

    def test_unable_to_verify_outcome_sets_flag(self):
        outcome = outcome_from_result(False, RESULT_UNABLE_TO_VERIFY)

        self.assertTrue(outcome.success)
        self.assertTrue(outcome.unable_to_verify)
        self.assertEqual(outcome.screenshot_prefix, RESULT_UNABLE_TO_VERIFY)

    def test_routing_always_uses_homepage(self):
        settings = {"proxies": []}

        first_url, first_proxy, first_wait = select_url_and_proxy(settings, now=100)
        second_url, _, _ = select_url_and_proxy(settings, now=101)

        self.assertEqual(first_url, HOMEPAGE_URL)
        self.assertEqual(second_url, HOMEPAGE_URL)
        self.assertIsNone(first_proxy)
        self.assertEqual(first_wait, 0)

    def test_proxy_selection_uses_unused_proxy_first_then_cooldown(self):
        settings = {
            "proxies": [
                {"host": "used", "last_use": 950},
                {"host": "unused", "last_use": 0},
            ]
        }

        proxy, wait = select_proxy(settings, now=1000, cooldown=600)

        self.assertEqual(proxy["host"], "unused")
        self.assertEqual(wait, 0)
        self.assertEqual(proxy["last_use"], 1000)

    def test_dev_env_lines_can_be_built_from_settings(self):
        lines = env_lines_from_settings(
            {
                "edge_path": "edge",
                "proxies": [{"host": "host", "port": "1", "user": "u", "pass": "p"}],
            }
        )

        self.assertIn("FUNDREL_EDGE_PATH=edge", lines)
        self.assertIn("FUNDREL_PROXIES=host:1:u:p", lines)

    @patch("automate2.image_on_screen")
    def test_post_verify_detects_another_account_before_success(self, mock_image_on_screen):
        def fake_match(image_path, confidence=0.8):
            return image_path == "already_verified_account.png" and confidence <= 0.75

        mock_image_on_screen.side_effect = fake_match

        self.assertEqual(automate2.detect_post_verify_outcome(), RESULT_WE_FOUND_ANOTHER_ACCOUNT)

    @patch("automate2.image_on_screen")
    def test_post_verify_requires_success_screen_before_onboarding(self, mock_image_on_screen):
        mock_image_on_screen.return_value = False

        self.assertIsNone(automate2.detect_post_verify_outcome())
        self.assertEqual(
            outcome_from_result(False, RESULT_SUCCESS_NOT_CREATED).created,
            False,
        )

    @patch("automate2.image_on_screen")
    def test_post_verify_detects_youre_in_success_screen(self, mock_image_on_screen):
        def fake_match(image_path, confidence=0.8):
            return image_path == "youre_in.png" and confidence <= 0.8

        mock_image_on_screen.side_effect = fake_match

        self.assertEqual(automate2.detect_post_verify_outcome(), RESULT_CREATED)


if __name__ == "__main__":
    unittest.main()
