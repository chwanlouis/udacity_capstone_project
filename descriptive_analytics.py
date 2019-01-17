import numpy as np
import pandas as pd
from scipy import stats


def basic_stats(instruments):
    all_instu_stats = list()
    for key, val in instruments.items():
        df = pd.read_csv(val)
        close_price = df['Close'].values.tolist()
        instu_stats = dict()
        instu_stats['instument'] = key
        instu_stats['min'] = min(close_price)
        instu_stats['max'] = max(close_price)
        instu_stats['median'] = np.median(close_price)
        instu_stats['mean'] = np.mean(close_price)
        instu_stats['skew'] = stats.skew(close_price)
        instu_stats['kurtosis'] = stats.kurtosis(close_price)
        all_instu_stats.append(instu_stats)
    all_instu_stats_df = pd.DataFrame(all_instu_stats)
    colnames = ['instument', 'min', 'max', 'median', 'mean', 'skew', 'kurtosis']
    return all_instu_stats_df[colnames]


if __name__ == '__main__':
    instruments = {
        'hk_equity_fund': 'dataset/hk_equity_fund_data.csv',
        'growth_fund': 'dataset/growth_fund_data.csv',
        'balanced_fund': 'dataset/balanced_fund_data.csv',
        'conservative_fund': 'dataset/conservative_fund_data.csv',
        'hkdollar_bond_fund': 'dataset/hkdollar_bond_fund_data.csv',
        'stable_fund': 'dataset/stable_fund_data.csv',
        'HSI': 'dataset/HSI_investing_com.csv',
        'IXIC': 'dataset/IXIC_investing_com.csv',
        'us2yrby': 'dataset/us2yrbondyield_investing_com.csv',
        'us10yrby': 'dataset/us10yrbondyield_investing_com.csv'
    }
    all_instuments_stats = basic_stats(instruments)
    all_instuments_stats.to_csv('all_instument_basic_stats.csv', index=False)
    print(all_instuments_stats)
