#!/usr/bin/env python3

import argparse
import requests

def fetch_rates():
    try:
        response = requests.get("http://www.floatrates.com/daily/usd.json")
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        raise SystemExit(f"Error fetching currency data: {e}")

def convert_currency(amount, base_currency, target_currency, rates):
    if base_currency == target_currency:
        return None  # No need to convert if currencies are the same
    
    # Handle direct USD conversions
    if base_currency == 'usd':
        rate = rates.get(target_currency)
        return amount * rate['rate'] if rate else None
    elif target_currency == 'usd':
        rate = rates.get(base_currency)
        return amount / rate['rate'] if rate else None
    
    # Handle non-USD base to non-USD target conversions
    base_to_usd = rates.get(base_currency)
    usd_to_target = rates.get(target_currency)
    if base_to_usd and usd_to_target:
        return amount * (usd_to_target['rate'] / base_to_usd['rate'])
    else:
        return None

def main():
    parser = argparse.ArgumentParser(description="Convert currencies to and from a base currency")
    parser.add_argument('amount', type=float, help='Amount to convert')
    parser.add_argument('currencies', nargs='+', help='List of currency codes to convert from the first currency')
    args = parser.parse_args()

    if len(args.currencies) < 2:
        print("Please provide at least two currencies for comparison.")
        return

    base_currency = args.currencies[0].lower()
    rates = fetch_rates()

    for currency in args.currencies[1:]:
        currency = currency.lower()
        result = convert_currency(args.amount, base_currency, currency, rates)
        if result is not None:
            print(f"{args.amount} {base_currency.upper()} is equivalent to {result:.4f} {currency.upper()}.")
        else:
            print(f"{base_currency.upper()} to {currency.upper()} exchange rate not found.")

if __name__ == "__main__":
    main()
