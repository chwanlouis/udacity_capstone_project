import os
import time
import pandas as pd
from learning_agent import MultipleLayerPerceptronClassifier


class DataFeeder(object):
    def __init__(self, data_file_name, selected_features=None):
        self.data_file_name = data_file_name
        self.selected_features = selected_features
        self.records = self.reader()

    def reader(self):
        df = pd.read_csv(self.data_file_name)
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
        df = df.set_index('Date')
        if self.selected_features is not None:
            df = pd.read_csv(self.data_file_name)[['Date'] + self.selected_features]
        return df.sort_values('Date').to_dict('records')

    def feed(self):
        if len(self.records):
            return self.records.pop(0)
        else:
            return None


class StrategyBacktesting(object):
    def __init__(self, feeder, capital, classifier_type, selected_features):
        self.feeder = feeder
        self.capital = capital
        self.training_bars = 300
        self.n_bars_after_retrain = 100
        self.historical_data = list()
        self.classifier_type = classifier_type
        self.selected_features = selected_features
        self.total_bar_count = 0
        self.prediction = None

    def on_bars(self, bar):
        print(bar)
        if self.prediction is not None:
            balanced_fund_data_rise_prob, conservative_fund_data_rise_prob, growth_fund_data_rise_prob, \
            hk_equity_fund_data_rise_prob, hkdollar_bond_fund_data_rise_prob, stable_fund_data_rise_prob = self.prediction
            print('Balance Fund rising probability : %.4f' % balanced_fund_data_rise_prob)
            print('Conservative Fund rising probability : %.4f' % conservative_fund_data_rise_prob)
            print('Growth Fund rising probability : %.4f' % growth_fund_data_rise_prob)
            print('HK equity Fund rising probability : %.4f' % hk_equity_fund_data_rise_prob)
            print('HK dollar Bond Fund rising probability : %.4f' % hkdollar_bond_fund_data_rise_prob)
            print('Stable Fund rising probability : %.4f' % stable_fund_data_rise_prob)


    def on_classifier(self, bar):
        if len(self.historical_data) < self.training_bars:
            return
        if not os.path.isdir('model/'):
            os.path.mkdir('model/')
        model_builder = self.classifier_type(
            features_name=self.selected_features
        )
        data = self.historical_data[-self.training_bars:]
        if self.total_bar_count % self.n_bars_after_retrain == 0:
            os.remove(model_builder.model_file_path)
        if not os.path.isfile(model_builder.model_file_path):
            model_builder.train(data, n_days=10, req_return=0.005, is_save_model=True, reload_model=False)
        else:
            model_builder.load_model()
        test_data = [bar[feature] for feature in self.selected_features]
        prediction = model_builder.get_probability([test_data])
        return prediction[0].tolist()

    def run(self, nbars_run=None):
        if type(nbars_run) == int and nbars_run >= 0:
            counter = nbars_run
        else:
            counter = -1
        while True:
            if counter == 0:
                break
            bar = self.feeder.feed()
            if bar is None:
                break
            self.on_bars(bar)
            self.prediction = None
            # after trading hours
            self.prediction = self.on_classifier(bar)
            self.historical_data.append(bar)
            counter -= 1
            self.total_bar_count += 1


if __name__ == '__main__':
    data_file_name = 'dataset/processed_data.csv'
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
    data_feeder = DataFeeder(data_file_name, selected_features)
    backtester = StrategyBacktesting(
        feeder=data_feeder,
        capital=1000000,
        classifier_type=MultipleLayerPerceptronClassifier,
        selected_features=selected_features
    )
    backtester.run()
