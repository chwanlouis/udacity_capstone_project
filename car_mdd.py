import numpy as np
import pandas as pd
from datetime import datetime


def	car(_date, X):
	start = datetime.strptime(_date[0], '%d/%m/%Y')
	end = datetime.strptime(_date[-1], '%d/%m/%Y')
	delta = end - start
	delta_days = delta.days
	delta_years = float(delta_days) / 365
	print(delta_years)
	return_rate = (X[-1] - X[0])/X[0]
	return np.power(1 + return_rate, 1.0/delta_years) - 1


def max_drawdown(X):
    mdd = 0
    peak = X[0]
    for x in X:
        if x > peak: 
            peak = x
        dd = (peak - x) / peak
        if dd > mdd:
            mdd = dd
    return mdd 


if __name__ == '__main__':
    file_name = 'dataset/HK_Equity_Fund_B_testing.csv'
    df = pd.read_csv(file_name)
    date_list = df.Date.values.tolist()
    price_list = df.Price.values.tolist()
    _car = car(date_list, price_list) * 100
    _mdd = max_drawdown(price_list) * 100
    print('Compound Annuel Return = %.4f percent' % _car)
    print('Maximum DrawDown = %.4f percent' % _mdd)
    print('CAR/MDD = %.4f' % (_car/_mdd))