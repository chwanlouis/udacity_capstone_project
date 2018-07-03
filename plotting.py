import pandas as pd
import matplotlib.pyplot as plt


def drawdown_curve(_price):
    dd = list()
    peak = _price[0]
    for x in _price:
        if x > peak:
            peak = x
        dd.append((x - peak) / peak)
    return dd


hk_eq_fname = 'dataset/hk_equity_fund_data.csv'
hk_equity_fund_df = pd.read_csv(hk_eq_fname)
hk_equity_fund_df['Date'] = pd.to_datetime(hk_equity_fund_df['Date'], format='%Y-%m-%d')
hk_equity_fund_df = hk_equity_fund_df.sort_values('Date')
hk_equity_fund_df.index = range(len((hk_equity_fund_df)))
drawdown = drawdown_curve(hk_equity_fund_df['Price'])
hk_equity_fund_df['Drawdown'] = drawdown
hk_equity_fund_df = hk_equity_fund_df.set_index('Date')
hk_equity_fund_df.plot()