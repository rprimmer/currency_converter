#!/usr/bin/env python3

import argparse
import requests
import yaml
import os

def fetch_rates(url):
    try:
        if not url:  # Check if the URL is provided and valid
            raise ValueError("URL for fetching rates is not provided.")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except (requests.RequestException, ValueError) as e:
        raise SystemExit(f"Error fetching currency data: {e}")

def convert_currency(amount, base_currency, target_currency, rates):
    if base_currency == target_currency:
        return None  # No need to convert if currencies are the same

    if base_currency == 'usd':
        rate = rates.get(target_currency)
        return amount * rate['rate'] if rate else None
    elif target_currency == 'usd':
        rate = rates.get(base_currency)
        return amount / rate['rate'] if rate else None

    base_to_usd = rates.get(base_currency)
    usd_to_target = rates.get(target_currency)
    if base_to_usd and usd_to_target:
        return amount * (usd_to_target['rate'] / base_to_usd['rate'])
    else:
        return None

def show_currencies(rates):
    print("Available currencies:")
    for key in sorted(rates.keys()):
        print(f"{key.upper()} - {rates[key]['name']}")

def main():
    parser = argparse.ArgumentParser(description="Convert currencies to and from a base currency")
    parser.add_argument('amount', type=float, nargs='?', help='Amount to convert')
    parser.add_argument('currencies', nargs='*', help='List of currency codes to convert from the first currency')
    parser.add_argument('-s', '--show', action='store_true', help='Show available currency codes')
    args = parser.parse_args()

    if args.show:
        show_currencies(rates)
        return

    default_url = "http://www.floatrates.com/daily/usd.json"
    config_path = "config.yaml"
    config = {}

    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file) or {}
    
    url = config.get('url') or default_url
    rates = fetch_rates(url)

    amount = args.amount if args.amount is not None else config.get('amount')
    if amount is None:
        amount = float(input("Enter the amount to convert: "))

    if args.currencies:
        base_currency = args.currencies[0].lower()
        converting_currencies = args.currencies[1:]
    else:
        base_currency = (config.get('base_currency') or input("Enter the base currency: ")).strip().lower()
        converting_currencies = config.get('converting_currencies', [])

    if not base_currency:
        base_currency = input("Enter the base currency: ").lower()

    if not converting_currencies:
        converting_currencies = input("Enter target currencies, separated by spaces: ").split()

    if len(converting_currencies) < 1:
        print("Please provide at least one target currency for comparison.")
        return

    for currency in converting_currencies:
        currency = currency.lower()
        result = convert_currency(amount, base_currency, currency, rates)
        if result is not None:
            print(f"{amount} {base_currency.upper()} is equivalent to {result:.4f} {currency.upper()}.")
        else:
            print(f"Exchange rate not found for {base_currency.upper()} to {currency.upper()}.")

if __name__ == "__main__":
    main()
