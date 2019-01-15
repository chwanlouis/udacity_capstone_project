# Machine Learning based trading agent

This readme is going to introduce the dependencies, working environment and instructions for the software

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them

* python 2.7.14
* scikit-learn 0.19.1
* numpy 1.15.2
* pandas 0.18.1
* pyalgotrade 0.18
* bs4 4.6.0


### Installing

A step by step series of examples that tell you have to get a development env running

Please install anaconda 2 via the web and execute the following command

```
pip install scikit-learn==0.19.1
pip install numpy==1.15.2
pip install pandas==0.18.1
pip install pyalgotrade==0.18
pip install beautifulsoup4==4.6.0
```

## Running the tests

### Getting the benchmark result
'''
python benchmark_result.py
'''
### Getting the backtest result
'''
python backtester.py
'''
All the record is saved in log/backtesting_result.txt

### Getting the walk forward test result
'''
python walk_forward_backtester.py
'''
All the record is saved in log/walk_forward_backtesting_result_sec_*.txt. "*" is the number of section divided

## Authors

* **Louis Wan** - *Initial work* - [chwanlouis](https://github.com/chwanlouis)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* the backtest report is copied from pyalgotrade example
