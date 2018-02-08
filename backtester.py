import pandas as pd


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
    def __init__(self, feeder, capital):
        self.feeder = feeder
        self.capital = capital

    def on_bars(self, bar):
        print(bar)

    def run(self):
        while True:
            bar = self.feeder.feed()
            if bar is None:
                break
            self.on_bars(bar)


if __name__ == '__main__':
    data_file_name = 'dataset/processed_data.csv'
    data_feeder = DataFeeder(data_file_name)
    backtester = StrategyBacktesting(
        feeder=data_feeder,
        capital=1000000
    )
    backtester.run()
