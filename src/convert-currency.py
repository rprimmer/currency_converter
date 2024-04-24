#!/usr/bin/env python3

import argparse
import requests

def fetch_rates(url):  # Add URL as a parameter
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
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

    rates = fetch_rates("http://www.floatrates.com/daily/usd.json")  # Pass the URL here

    if args.show:
        show_currencies(rates)
        return

    if args.amount is None:
        args.amount = float(input("Enter the amount to convert: "))
    if not args.currencies:
        args.currencies = input("Enter the base currency and target currencies, separated by spaces: ").split()

    if len(args.currencies) < 2:
        print("Please provide at least two currencies for comparison.")
        return

    base_currency = args.currencies[0].lower()

    for currency in args.currencies[1:]:
        currency = currency.lower()
        result = convert_currency(args.amount, base_currency, currency, rates)
        if result is not None:
            print(f"{args.amount} {base_currency.upper()} is equivalent to {result:.4f} {currency.upper()}.")
        else:
            print(f"{base_currency.upper()} to {currency.upper()} exchange rate not found.")

if __name__ == "__main__":
    main()
