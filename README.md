# Currency Converter

Convert currencies from a base currency

## Usage

usage: `convert-currency.py [-h] [-s] [amount] [currencies ...]`

positional arguments:

* `amount`      Amount to convert
* `currencies`  List of currency codes to convert from the first currency

options:

* `-h`, `--help`  show help message and exit
* `-s`, `--show`  Show available currency codes

## Modes

Can be run in batch by supplying all options and arguments. In the absence of any arguments, the user is queried for the information.

### Examples

* `python src/currency_converter/convert-currency.py`
  * enters interactive mode
* `python src/currency_converter/convert-currency.py -s`
  * displays available currency codes
* `python src/currency_converter/convert-currency.py 100 usd eur aud cad`
  * converts 100 US dollars to Euros, Australian and Canadian dollars

## Executable

To create an executable, use PyInstaller.

To determine if it's already loaded:

```sh
    pip show pyinstaller
```

If not present:

```sh
    pip install pyinstaller
```

To generate an executable:

```sh
    python -m PyInstaller convert_currency.spec
```

Resulting executable is: `dist/convert-currency/convert-currency`
