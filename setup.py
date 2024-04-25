from setuptools import setup, find_packages

setup(
    name='currency-converter',
    version='2.1.0',
    description='A tool for converting currencies',
    author='Robert Primmer',
    author_email='rob.primmer@icloud.com',
    package_dir={'': 'src'},  
    packages=find_packages(where='src'),  
    install_requires=[
        'requests',  
        'pyyaml'     
    ],
    entry_points={
        'console_scripts': [
            'convert-currency=currency_converter.convert_currency:main',  
        ]
    },
)
