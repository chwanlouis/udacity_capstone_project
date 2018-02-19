import time
import pandas as pd
from learning_agent import LogisticRegressionClassifier


class DataFeeder(object):
    def __init__(self, data_file_name):
        self.data_file_name = data_file_name
        self.records = self.reader()

    def reader(self):
        df = pd.read_csv(self.data_file_name)
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
        return df.sort_values('Date').to_dict('records')

    def feed(self):
        if len(self.records):
            return self.records.pop(0)
        else:
            return None


class StrategyBacktesting(object):
    def __init__(self, feeder, capital, classifier_type):
        self.feeder = feeder
        self.capital = capital
        self.historical_data = list()
        self.classifier_type = classifier_type

    def on_bars(self, bar):
        print(bar)

    def on_classifier(self):
        model = self.classifier_type(
            data=self.historical_data,
            feature=None,
            target=None
        )
        # print(len(model.data_row))

    def run(self, nbars_run=None):
        if type(nbars_run) is not None:
            counter = nbars_run
        else:
            counter = -1
        while True:
            bar = self.feeder.feed()
            if bar is None:
                break
            self.on_bars(bar)
            # after trading hours
            self.historical_data.append(bar)
            # self.on_classifier()
            counter -= 1
            if counter == 0:
                break


if __name__ == '__main__':
    data_file_name = 'dataset/processed_data.csv'
    data_feeder = DataFeeder(data_file_name)
    backtester = StrategyBacktesting(
        feeder=data_feeder,
        capital=1000000,
        classifier_type=LogisticRegressionClassifier
    )
    backtester.run(nbars_run=5)
