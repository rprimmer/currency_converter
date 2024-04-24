# Currency Converter

Convert currencies from a base currency.

## Usage

usage: `python convert-currency.py [OPTIONS] [amount] [currencies ...]`

positional arguments:

* `amount`      Amount to convert
* `currencies`  List of currency codes to convert from the first currency

options:

* `-h`, `--help`  show help message and exit
* `-s`, `--show`  Show available currency codes

## Yaml Config

Parameters can be entered on the command line as positional arguments or the user will be queried for these values.

As a convenience for regular batch operation, all parameters can be specified in the yaml file `config.yaml`.

### Yaml fields

* `url` : the website used to fetch currency rates.
* `amount` : currency amount to convert
* `base_currency` : currency to convert from
* `converting_currencies` : currencies to convert to

For example, to convert 100 US Dollars to Euros, Pounds, Russian rubles, Ukrainian hryvnia and Polish Zloty you would use these entries in the `config.yaml`.

```yaml
url: "http://www.floatrates.com/daily/usd.json"
amount: 100
base_currency: "USD"
converting_currencies: ["EUR", "GBP", "RUB", "UAH", "PLN"]
```

## Modes

Can be run in three modes:

* batch with a yaml file,
* batch with command line arguments, or
* interactively.

It is not essential that a `config.yaml` file exist. In the absence of this file, or empty fields within the file, the script will query the user for these values.

The one exception is the URL. If a valid URL is not specified the script defaults to:

* `"http://www.floatrates.com/daily/usd.json"`

### Examples

* `python src/currency_converter/convert-currency.py -s`
* `python src/currency_converter/convert-currency.py`
* `python src/currency_converter/convert-currency.py 100 usd eur aud cad`

## Executable

To convert the python script to an executable use PyInstaller.

An executable removes the need for the user to have a functioning Python environment on the executing machine.

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
    python -m PyInstaller convert-currency.spec
```

Resulting executable is: `dist/convert-currency/convert-currency`
