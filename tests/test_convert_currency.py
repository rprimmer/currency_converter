"""Regression tests use fixed rates and never contact the provider."""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import requests

from convert_currency import convert_currency as converter

RATES = {
    "eur": {"rate": 0.8, "name": "Euro"},
    "gbp": {"rate": 0.5, "name": "Pound Sterling"},
}


class ConversionTests(unittest.TestCase):
    def test_conversion_paths(self):
        for source, target, expected in [
            ("usd", "eur", 80), ("eur", "usd", 125),
            ("eur", "gbp", 62.5), ("eur", "eur", 100),
            ("usd", "usd", 100), (" EUR ", "GBP", 62.5),
        ]:
            with self.subTest(source=source, target=target):
                self.assertAlmostEqual(converter.convert_currency(100, source, target, RATES), expected)

    def test_unknown_currencies(self):
        for source, target in [("xxx", "usd"), ("usd", "xxx"), ("xxx", "xxx")]:
            self.assertIsNone(converter.convert_currency(100, source, target, RATES))

    def test_zero_and_negative_amounts(self):
        self.assertEqual(converter.convert_currency(0, "usd", "eur", RATES), 0)
        self.assertEqual(converter.convert_currency(-100, "usd", "eur", RATES), -80)

    def test_invalid_amounts(self):
        for amount in [True, None, "bad", float("nan"), float("inf")]:
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                converter.parse_amount(amount)


class ConfigTests(unittest.TestCase):
    def test_optional_and_invalid_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            self.assertEqual(converter.load_config(path), {})
            for contents in ["", "# empty\n", "null"]:
                path.write_text(contents)
                self.assertEqual(converter.load_config(path), {})
            path.write_text("amount: 0\nbase_currency: USD\n")
            self.assertEqual(converter.load_config(path), {"amount": 0, "base_currency": "USD"})
            for contents in ["[]", "false", "42"]:
                path.write_text(contents)
                with self.assertRaises(ValueError):
                    converter.load_config(path)


class FetchTests(unittest.TestCase):
    @patch.object(converter.requests, "get")
    def test_fetch_checks_status_and_timeout(self, get):
        get.return_value.json.return_value = RATES
        self.assertEqual(converter.fetch_rates("https://example.com"), RATES)
        get.assert_called_once_with("https://example.com", timeout=10)
        get.return_value.raise_for_status.assert_called_once_with()

    @patch.object(converter.requests, "get")
    def test_bad_payloads(self, get):
        for payload in [[], {}, {"eur": None}, {"eur": {"name": "Euro"}},
                        {"eur": {"name": "Euro", "rate": 0}},
                        {"eur": {"name": "Euro", "rate": -1}},
                        {"eur": {"name": "Euro", "rate": "NaN"}},
                        {"eur": {"name": "Euro", "rate": 1, "baseCode": "GBP"}}]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                get.return_value.json.return_value = payload
                converter.fetch_rates("https://example.com")

    @patch.object(converter.requests, "get")
    def test_http_errors_propagate(self, get):
        get.return_value.raise_for_status.side_effect = requests.HTTPError("Unavailable")
        with self.assertRaises(requests.HTTPError):
            converter.fetch_rates("https://example.com")
        get.return_value.json.assert_not_called()


class CliTests(unittest.TestCase):
    def run_cli(self, argv, config=None, inputs=(), fetch_error=None):
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(converter, "load_config", return_value=config or {}), \
             patch.object(converter, "fetch_rates", return_value=RATES, side_effect=fetch_error) as fetch, \
             patch("builtins.input", side_effect=inputs) as prompt, \
             redirect_stdout(output), redirect_stderr(errors):
            status = converter.main(argv)
        return status, output.getvalue(), errors.getvalue(), fetch, prompt

    def test_show_without_prompts(self):
        status, output, errors, _, prompt = self.run_cli(["--show"])
        self.assertEqual(status, 0)
        self.assertIn("USD - U.S. Dollar", output)
        self.assertLess(output.index("EUR"), output.index("GBP"))
        self.assertEqual(errors, "")
        prompt.assert_not_called()

    def test_cli_overrides_config(self):
        status, output, _, fetch, prompt = self.run_cli(
            ["100", "USD", "EUR", "GBP"],
            {"amount": 200, "base_currency": "GBP", "converting_currencies": ["USD"], "url": "https://example.com"})
        self.assertEqual(status, 0)
        self.assertIn("80.0000 EUR", output)
        self.assertIn("50.0000 GBP", output)
        fetch.assert_called_once_with("https://example.com")
        prompt.assert_not_called()

    def test_config_defaults(self):
        status, output, _, _, prompt = self.run_cli(
            [], {"amount": 0, "base_currency": "EUR", "converting_currencies": ["USD"]})
        self.assertEqual(status, 0)
        self.assertIn("0.0000 USD", output)
        prompt.assert_not_called()

    def test_interactive(self):
        status, output, _, _, _ = self.run_cli([], inputs=["100", "eur", "usd gbp"])
        self.assertEqual(status, 0)
        self.assertIn("125.0000 USD", output)
        self.assertIn("62.5000 GBP", output)

    def test_missing_targets_prompt(self):
        status, output, _, _, _ = self.run_cli(
            ["100", "usd"], {"converting_currencies": ["GBP"]}, inputs=["eur"])
        self.assertEqual(status, 0)
        self.assertIn("EUR", output)
        self.assertNotIn("50.0000 GBP", output)

    def test_unknown_target_sets_failure_status_but_continues(self):
        status, output, _, _, _ = self.run_cli(["100", "usd", "xxx", "eur"])
        self.assertEqual(status, 1)
        self.assertIn("Exchange rate not found", output)
        self.assertIn("80.0000 EUR", output)

    def test_invalid_input_fails_before_network(self):
        for argv, config, inputs in [
            (["nan", "usd", "eur"], {}, []),
            ([], {"amount": 1, "base_currency": "usd", "converting_currencies": "EUR"}, []),
        ]:
            with self.subTest(argv=argv, config=config):
                status, _, errors, fetch, _ = self.run_cli(argv, config, inputs)
                self.assertEqual(status, 1)
                self.assertIn("Error:", errors)
                fetch.assert_not_called()

    def test_interactive_help_and_corrections(self):
        status, output, _, fetch, _ = self.run_cli(
            [], inputs=["bad", "25.50", "?", "dollars", "USD", "", "XYZ", "EUR, GBP"])
        self.assertEqual(status, 0)
        self.assertIn("USD = US dollar", output)
        self.assertIn("Available currencies:", output)
        self.assertIn("Please try again", output)
        self.assertIn("Unknown currency: XYZ", output)
        self.assertIn("20.4000 EUR", output)
        self.assertIn("12.7500 GBP", output)
        fetch.assert_called_once()

    def test_quit_at_each_prompt(self):
        for inputs in [["q"], ["100", "quit"], ["100", "usd", "Q"]]:
            with self.subTest(inputs=inputs):
                status, output, errors, _, _ = self.run_cli([], inputs=inputs)
                self.assertEqual(status, 0)
                self.assertIn("Conversion cancelled", output)
                self.assertEqual(errors, "")

    def test_interrupted_input(self):
        for error, expected in [(EOFError(), 1), (KeyboardInterrupt(), 0)]:
            status, output, errors, _, _ = self.run_cli([], inputs=error)
            self.assertEqual(status, expected)
            self.assertNotIn("Traceback", output + errors)

    def test_network_failure_is_readable(self):
        status, _, errors, _, _ = self.run_cli(["--show"], fetch_error=requests.Timeout("Timed out"))
        self.assertEqual(status, 1)
        self.assertIn("Timed out", errors)
        self.assertNotIn("Traceback", errors)


if __name__ == "__main__":
    unittest.main()
