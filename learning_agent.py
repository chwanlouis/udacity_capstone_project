import os
import pickle
import pandas as pd
from sklearn.neural_network import MLPClassifier


class MultipleLayerPerceptronClassifier(object):
    def __init__(self, features_name):
        self.model_name = 'mlp_classifier'
        self.model_file_path = 'model/mlp_classifier.pickle'
        self.features_name = features_name
        self.fund_list = [
            'balanced_fund_data_Price',
            'conservative_fund_data_Price',
            'growth_fund_data_Price',
            'hk_equity_fund_data_Price',
            'hkdollar_bond_fund_data_Price',
            'stable_fund_data_Price'
        ]
        self.model = None

    @staticmethod
    def get_future_return(df, feature, n_days, req_return):
        current_price = df[feature]
        future_price = df[feature].shift(-n_days)
        future_return = (future_price - current_price) / current_price
        df['%s_future_return' % feature] = [1 if i > req_return else 0 for i in future_return]
        return df

    def create_target(self, data, n_days, req_return):
        df = pd.DataFrame(data)
        for fund_name in self.fund_list:
            df = self.get_future_return(df, fund_name, n_days, req_return)
        return_list = ['%s_future_return' % i for i in self.fund_list]
        df = df.dropna()
        return df[self.features_name].values, df[return_list].values

    def train(self, data, n_days, req_return, is_save_model=True, reload_model=False):
        if reload_model:
            model_file_exist = self.load_model()
            if model_file_exist:
                print('Pickle file Loaded')
                return
            print('Pickle file does not exist')
        self.model = MLPClassifier(
            solver='lbfgs',
            alpha=1e-5,
            hidden_layer_sizes=(15, 5),
            random_state=1
        )
        X, y = self.create_target(data, n_days, req_return)
        self.model = self.model.fit(X, y)
        if is_save_model:
            with open(self.model_file_path, 'wb') as handle:
                pickle.dump(self.model, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def load_model(self):
        if os.path.isfile(self.model_file_path):
            self.model = pickle.load(open(self.model_file_path, 'rb'))
            return True
        return False

    def get_probability(self, data):
        if self.model is None:
            print('Model is not build')
            return
        # df = pd.DataFrame(data)[self.features_name].values
        return self.model.predict_proba(data)


if __name__ == '__main__':
    df = pd.read_csv('dataset/processed_data.csv')
    selected_features = [
        'balanced_fund_data_Price',
        'conservative_fund_data_Price',
        'growth_fund_data_Price',
        'hk_equity_fund_data_Price',
        'hkdollar_bond_fund_data_Price',
        'stable_fund_data_Price',
        'HSI_investing_com_Price',
        'IXIC_investing_com_Price',
        'us2yrbondyield_investing_com_Price',
        'us10yrbondyield_investing_com_Price'
    ]
    df = df[selected_features]
    data = df.to_dict('record')[:300]
    test_data = df.to_dict('record')
    model_builder = MultipleLayerPerceptronClassifier(
        features_name=selected_features
    )
    model_builder.train(
        data=data,
        n_days=10,
        req_return=0.005
    )
    prob = model_builder.get_probability(test_data)
    for prob_row in prob:
        print(prob_row)
