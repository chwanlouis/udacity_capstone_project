import pandas as pd
from sklearn.linear_model import LogisticRegression


class LogisticRegressionClassifier(object):
    def __init__(self, data, feature=None, target=None):
        if feature is None:
            self.feature = [
                'balanced_fund_data_Price_t-1',
                'conservative_fund_data_Price_t-1',
                'growth_fund_data_Price_t-1',
                'hk_equity_fund_data_Price_t-1',
                'hkdollar_bond_fund_data_Price_t-1',
                'stable_fund_data_Price_t-1'
                # 'HSI_investing_com_Price',
                # 'IXIC_investing_com_Price',
                # 'us2yrbondyield_investing_com_Price',
                # 'us10yrbondyield_investing_com_Price'
            ]
        else:
            self.feature = feature
        if target is None:
            self.target = [
                'balanced_fund_data_Price',
                'conservative_fund_data_Price',
                'growth_fund_data_Price',
                'hk_equity_fund_data_Price',
                'hkdollar_bond_fund_data_Price',
                'stable_fund_data_Price'
            ]
        else:
            self.target = target
        self.data_row, self.target_row = self.get_data_and_target_row(data, self.feature, self.target)

    @staticmethod
    def get_data_and_target_row(data, feature, target):
        feature_df = pd.DataFrame(data)[feature]
        target_df = pd.DataFrame(data)[target]
        return feature_df, target_df

    def build_model(self, target):
        all_model = dict()
        for tar in target:
            pass


if __name__ == '__main__':
    pass
