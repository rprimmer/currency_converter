#!/usr/bin/env python3
"""Convert currencies using a USD-based FloatRates feed."""

import argparse
import math
from pathlib import Path
import sys

import requests
import yaml

DEFAULT_URL = "https://www.floatrates.com/daily/usd.json"
REQUEST_TIMEOUT = 10


def parse_amount(value):
    """Accept finite numeric amounts from the CLI, YAML, or a prompt."""
    try:
        if isinstance(value, bool):
            raise ValueError
        amount = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Amount must be a finite number.") from exc
    if not math.isfinite(amount):
        raise ValueError("Amount must be a finite number.")
    return amount


def normalize_currency(value):
    """Use one representation for currency codes throughout the program."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Currency codes must be non-empty strings.")
    return value.strip().lower()


def load_config(path="config.yaml"):
    """Read optional YAML defaults from the current working directory."""
    try:
        with Path(path).open(encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        return {}
    if config is None:
        return {}
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a YAML mapping.")
    return config


def fetch_rates(url):
    """Fetch and validate the provider's USD-relative rate records."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL for fetching rates was not provided.")
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or not data:
        raise ValueError("Currency data must be a non-empty mapping.")
    rates = {}
    for code, record in data.items():
        code = normalize_currency(code)
        if not isinstance(record, dict):
            raise ValueError(f"Invalid currency data for {code.upper()}.")
        rate = parse_amount(record.get("rate"))
        if rate <= 0:
            raise ValueError(f"Rate for {code.upper()} must be positive.")
        if normalize_currency(record.get("baseCode", "usd")) != "usd":
            raise ValueError("Currency data must use USD as its base currency.")
        name = record.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Missing currency name for {code.upper()}.")
        rates[code] = {**record, "rate": rate}
    return rates


def convert_currency(amount, base_currency, target_currency, rates):
    """Return a converted amount, or None if a currency is unknown.

    Each rate expresses units of that currency per US dollar. Dividing by
    the source rate converts to USD; multiplying by the target rate converts
    from USD. USD itself always has a rate of one.
    """
    amount = parse_amount(amount)
    base_currency = normalize_currency(base_currency)
    target_currency = normalize_currency(target_currency)
    base_rate = 1.0 if base_currency == "usd" else rates.get(base_currency, {}).get("rate")
    target_rate = 1.0 if target_currency == "usd" else rates.get(target_currency, {}).get("rate")
    if base_rate is None or target_rate is None:
        return None
    if base_currency == target_currency:
        return amount
    result = amount * (target_rate / base_rate)
    if not math.isfinite(result):
        raise ValueError("Converted amount is too large.")
    return result


def show_currencies(rates):
    print("Available currencies:")
    names = {code: record["name"] for code, record in rates.items()}
    names["usd"] = "U.S. Dollar"
    for code, name in sorted(names.items()):
        print(f"{code.upper()} - {name}")


class CancelledInput(Exception):
    """The user chose to leave an interactive prompt."""


def prompt_value(message, parse, get_rates):
    """Allow help, cancellation, and corrections at every prompt."""
    while True:
        value = input(message).strip()
        if value.lower() in {"q", "quit"}:
            raise CancelledInput
        if value.lower() in {"?", "help"}:
            show_currencies(get_rates())
            continue
        try:
            return parse(value)
        except ValueError as exc:
            print(f"{exc} Please try again, or type q to quit.")


def resolve_inputs(args, config, get_rates):
    """Prefer command-line values, then configuration, then guided prompts."""
    amount = args.amount if args.amount is not None else config.get("amount")
    if args.currencies:
        base_currency = args.currencies[0]
        targets = args.currencies[1:]
    else:
        base_currency = config.get("base_currency")
        targets = config.get("converting_currencies") or []
    if not isinstance(targets, list):
        raise ValueError("converting_currencies must be a YAML list of currency codes.")

    if amount is None or not base_currency or not targets:
        print("Currency Converter")
        print("Convert an amount from one currency to one or more others.")
        print("Use currency codes: USD = US dollar, EUR = euro, GBP = British pound.")
        print("At any prompt, type ? to list currencies or q to quit.\n")

    if amount is None:
        amount = prompt_value("Amount to convert (e.g. 100 or 25.50; no currency symbol): ",
                              parse_amount, get_rates)
    else:
        amount = parse_amount(amount)

    def parse_codes(value):
        codes = [normalize_currency(code) for code in value.replace(",", " ").split()]
        if not codes:
            raise ValueError("Enter at least one currency code, such as EUR.")
        rates = get_rates()
        unknown = [code.upper() for code in codes if code != "usd" and code not in rates]
        if unknown:
            raise ValueError(f"Unknown currency: {', '.join(unknown)}. Type ? to see available codes.")
        return codes

    def parse_source(value):
        if len(value.replace(",", " ").split()) != 1:
            raise ValueError("Enter one source currency code, such as USD.")
        return parse_codes(value)[0]

    if not base_currency:
        base_currency = prompt_value("Convert FROM (e.g. USD): ", parse_source, get_rates)
    else:
        base_currency = normalize_currency(base_currency)
    if not targets:
        targets = prompt_value(
            f"Convert {amount:g} {base_currency.upper()} TO (e.g. EUR GBP CAD; spaces or commas): ",
            parse_codes, get_rates)
    return amount, base_currency, [normalize_currency(code) for code in targets]


def main(argv=None):
    """Run the CLI and return an exit status without exiting library callers."""
    parser = argparse.ArgumentParser(description="Convert currencies to and from a base currency")
    parser.add_argument("amount", type=float, nargs="?", help="Amount to convert")
    parser.add_argument("currencies", nargs="*", help="Source currency followed by target currencies")
    parser.add_argument("-s", "--show", action="store_true", help="Show available currency codes")
    args = parser.parse_args(argv)

    try:
        config = load_config()
        url = config.get("url") or DEFAULT_URL
        if args.show:
            show_currencies(fetch_rates(url))
            return 0
        rates = None

        def get_rates():
            nonlocal rates
            if rates is None:
                rates = fetch_rates(url)
            return rates

        amount, base_currency, targets = resolve_inputs(args, config, get_rates)
        rates = get_rates()
        status = 0
        for currency in targets:
            result = convert_currency(amount, base_currency, currency, rates)
            if result is None:
                print(f"Exchange rate not found for {base_currency.upper()} to {currency.upper()}.")
                status = 1
            else:
                print(f"{amount} {base_currency.upper()} is equivalent to {result:.4f} {currency.upper()}.")
        return status
    except (CancelledInput, KeyboardInterrupt):
        print("\nConversion cancelled.")
        return 0
    except EOFError:
        print("Error: Input ended before the conversion was complete.", file=sys.stderr)
        return 1
    except (requests.RequestException, ValueError, OSError, yaml.YAMLError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
