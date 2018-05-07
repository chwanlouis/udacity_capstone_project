import numpy as np
import pandas as pd
from datetime import datetime


class CarMddRatio(object):
    def __init__(self, data_frame):
        self.data_frame = data_frame
        self.date_list = self.data_frame.Date.values.tolist()
        self.price_list = self.data_frame.Price.values.tolist()

    @staticmethod
    def	car(_date, _price):
        start = datetime.strptime(_date[0], '%d/%m/%Y')
        end = datetime.strptime(_date[-1], '%d/%m/%Y')
        delta = end - start
        delta_years = float(delta.days) / 365
        return_rate = (_price[-1] - _price[0])/_price[0]
        return np.power(1 + return_rate, 1.0/delta_years) - 1

    @staticmethod
    def max_drawdown(_price):
        mdd = 0
        peak = _price[0]
        for x in _price:
            if x > peak:
                peak = x
            dd = (peak - x) / peak
            if dd > mdd:
                mdd = dd
        return mdd

    def get_car_mdd_ratio(self):
        return self.car(self.date_list, self.price_list)/self.max_drawdown(self.price_list)


if __name__ == '__main__':
    file_name = 'dataset/HK_Equity_Fund_B_testing.csv'
    df = pd.read_csv(file_name)
    metric = CarMddRatio(df)
    print(metric.get_car_mdd_ratio())
