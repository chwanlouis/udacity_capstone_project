import pandas as pd
from datetime import datetime


class DataMerger(object):
    def __init__(self, file_name_list):
        self.file_name_list = file_name_list

    @staticmethod
    def reader(file_name):
        header_prefex = file_name.replace('dataset/', '').replace('.csv', '')
        df = pd.read_csv(file_name)
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
        df = df.set_index('Date')
        df.columns = ['%s_%s' % (header_prefex, colname)for colname in df.columns.values.tolist()]
        return df

    def run(self, save_csv=True):
        merged = None
        start_date = datetime.strptime('2002-01-09', '%Y-%m-%d')
        end_date = datetime.strptime('2017-12-31', '%Y-%m-%d')
        for file_name in self.file_name_list:
            df = self.reader(file_name)
            if merged is None:
                merged = df
            else:
                merged = merged.merge(df, how='left', left_index=True, right_index=True)
        merged = merged.sort_index()[start_date:end_date].interpolate(method='linear').round(decimals=4)
        if save_csv:
            merged.to_csv('dataset/processed_data.csv')
        return merged


if __name__ == '__main__':
    data_fname_list = [
        'dataset/balanced_fund_data.csv',
        'dataset/conservative_fund_data.csv',
        'dataset/growth_fund_data.csv',
        'dataset/hk_equity_fund_data.csv',
        'dataset/hkdollar_bond_fund_data.csv',
        'dataset/stable_fund_data.csv',
        'dataset/HSI_investing_com.csv',
        'dataset/IXIC_investing_com.csv',
        'dataset/us2yrbondyield_investing_com.csv',
        'dataset/us10yrbondyield_investing_com.csv'
    ]
    data_merger = DataMerger(data_fname_list)
    merged_df = data_merger.run(
        save_csv=True
    )
