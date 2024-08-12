# Currency Converter

Convert currencies to/from a base currency.

## Usage

usage: `python convert_currency.py [OPTIONS] [amount] [currencies ...]`

positional arguments:

* `amount`      Amount to convert
* `currencies`  List of currency codes to convert from the first currency

OPTIONS:

* `-h`, `--help`  show help message and exit
* `-s`, `--show`  Show available currency codes

## Yaml Config

Parameters can be entered on the command line as positional arguments or the user will be queried for these values.

As a convenience for repeated batch operation all parameters can be specified in the yaml file `config.yaml`.

### Yaml fields

* `url` : the website used to fetch currency rates.
* `amount` : currency amount to convert
* `base_currency` : currency to convert from
* `converting_currencies` : currencies to convert to

For example, to convert 100 US Dollars to Euros, Pounds, Russian Rubles, Ukrainian Hryvnia and Polish Zloty you would use these entries in the `config.yaml`.

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

It is not essential that a `config.yaml` file exist. In the absence of this file, or empty values within the file for some or all of the keys, the script will query the user for these values.

The one exception is the URL. If a valid URL is not specified the script defaults to:

* `"http://www.floatrates.com/daily/usd.json"`

### Examples

* `convert_currency.py -s`- Shows available currency codes.
* `convert_currency.py` - Runs interactively or uses values in `config.yaml`.
* `convert_currency.py 100 usd eur aud cad` - Converts 100 USD to EUR, AUD and CAD.

## Requirements

This project was tested with the following configurations:

* python 3.12.3
* requests==2.31.0
* pyyaml==6.0.1
* macOS 14.4.1 23E224 x86_64 & macOS 14.4.1 23E224 arm64

Ensure you have Python installed along with the necessary packages. To install the required packages, run:

```bash
    pip install -r requirements.txt
```

## Executable

To convert the python script to an executable use PyInstaller. An executable removes the need for the user to have a functioning Python environment on the executing machine.

This script was tested with:

* pyinstaller==6.6.0

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

Resulting executable is: `dist/convert_currency/convert_currency`
