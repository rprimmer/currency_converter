# Currency Converter

A small Python command-line tool for converting between currencies using
[FloatRates](https://www.floatrates.com/) USD-based exchange rates.

## Installation

From the repository directory, create a virtual environment and install the package:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

Dependencies are `requests` and `PyYAML`. Development checks use Python's built-in
`unittest` framework; no additional test dependencies are needed.

## Usage

```sh
convert-currency 100 usd eur aud cad
convert-currency --show
convert-currency
```

The first currency is the source; the remaining currencies are targets. Codes
are case-insensitive. Results are displayed to four decimal places.

The same interface is available as `python -m convert_currency` after installation.
To run directly from a checkout after installing `requirements.txt`, use:

```sh
PYTHONPATH=src python3 -m convert_currency 100 usd eur gbp
```

Options:

- `-h`, `--help`: display help.
- `-s`, `--show`: fetch and list available currencies, including USD, without prompts.

## Configuration and interactive mode

An optional `config.yaml` is read from the **current working directory**. The
included sample supplies defaults, so running from the repository uses those
values instead of prompting.

```yaml
url: "https://www.floatrates.com/daily/usd.json"
amount: 100
base_currency: "USD"
converting_currencies: ["EUR", "GBP", "CAD"]
```

Command-line amounts override the configured amount. A command-line currency
list replaces both the configured source and targets. Missing amounts, sources,
or target lists are requested interactively. For example, `convert-currency 100 usd`
prompts for targets. Interactive prompts include examples and explain source and
target currencies. Type `?` or `help` at any prompt to list available currencies,
or `q` / `quit` to cancel. Invalid prompted amounts and currency codes can be
corrected without restarting. Target codes may be separated by spaces or commas.
Ctrl-C also cancels cleanly. Zero is a valid amount. Negative amounts are also accepted.

A missing or empty configuration file is allowed. Without a configured URL, the
program uses `https://www.floatrates.com/daily/usd.json`. A custom URL must return
the same USD-based format, with currency codes mapped to records containing a
positive numeric `rate` and a `name`. If present, `baseCode` must be `USD`.

## Conversion and errors

Each rate is the number of currency units per USD. Conversion uses:

```text
result = amount × (target rate / source rate)
```

USD has a rate of one. Converting a supported currency to itself returns the
original amount. Unknown currencies are reported, and other requested targets
are still processed.

Requests use a ten-second timeout. Invalid configuration, non-finite amounts,
malformed rate data, and network failures produce an error message and exit
status 1. Unknown currencies also produce status 1; successful runs return 0.
Command-line syntax errors return status 2.

Calculations use floating-point numbers and round only for display. The tool
provides estimates from the downloaded rates; it does not account for fees.

## Development

```sh
python3 -m pip install -r requirements.txt
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Tests use fixed rate data and mocked network calls, covering conversions,
configuration, interactive input, listing currencies, and error handling.

The implementation is in [convert_currency.py](src/convert_currency/convert_currency.py).
Input parsing, configuration loading, rate fetching, and conversion are separate
functions so each responsibility can be understood and tested independently.

## Standalone executable

To build an executable with [PyInstaller](https://pyinstaller.org/):

```sh
python -m pip install pyinstaller
python -m PyInstaller --clean --noconfirm convert-currency.spec
```

The executable is written to `dist/convert-currency/convert-currency` on macOS
and Linux. It reads `config.yaml` from the directory where it is run.

The command and standalone executable are named `convert-currency`. The internal
Python package uses `convert_currency`, as required for Python imports. Keep the
adjacent `_internal` directory with the standalone executable when moving it.
