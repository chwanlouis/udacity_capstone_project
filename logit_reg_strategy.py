import time
import pandas as pd
from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade import strategy


class BenchmarkStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, capital, target):
        super(BenchmarkStrategy, self).__init__(feed)
        self.instrument = instrument
        self.position = None
        self.capital = capital
        self.target = target
        self.historical_data = list()
        self.historical_df = None
        self.historical_df_colnames = self.get_historical_df_colnames()

    def get_historical_df_colnames(self):
        colnames = list()
        for instrument in self.instrument:
            colnames.append('%s_open' % instrument)
            colnames.append('%s_high' % instrument)
            colnames.append('%s_low' % instrument)
            colnames.append('%s_close' % instrument)
            colnames.append('%s_volume' % instrument)
        return colnames

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY %s at $%.2f" % (execInfo.getQuantity(), execInfo.getPrice()))

    def onHistoricalData(self, bars):
        data_dict = dict()
        for instrument in self.instrument:
            if instrument in bars.keys():
                data_dict['%s_open' % instrument] = bars[instrument].getOpen()
                data_dict['%s_high' % instrument] = bars[instrument].getHigh()
                data_dict['%s_low' % instrument] = bars[instrument].getLow()
                data_dict['%s_close' % instrument] = bars[instrument].getClose()
                data_dict['%s_volume' % instrument] = bars[instrument].getVolume()
                if 'datetime' not in data_dict.keys():
                    data_dict['datetime'] = bars[instrument].getDateTime()
            else:
                data_dict['%s_open' % instrument] = None
                data_dict['%s_high' % instrument] = None
                data_dict['%s_low' % instrument] = None
                data_dict['%s_close' % instrument] = None
                data_dict['%s_volume' % instrument] = None
        self.historical_data.append(data_dict)
        # self.historical_df = pd.DataFrame(self.historical_data).interpolate()[self.historical_df_colnames].dropna()

    def onBars(self, bars):
        # updating historical dataset
        self.onHistoricalData(bars)
        if self.target not in bars.keys():
            return
        bar = bars[self.target]
        dt = bar.getDateTime()
        close = bar.getPrice()
        print(dt, close)
        # Buy and hold
        # amount = self.capital / close
        # if self.position is None and amount >= 1:
        #     self.position = self.enterLong(self.target, amount, True, False)


if __name__ == '__main__':
    feed = GenericBarFeed(frequency='DAY')
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
    for instu, fname in instruments.iteritems():
        print('Importing data %s from file path %s' % (instu, fname))
        feed.addBarsFromCSV(instu, fname)
    benchmark_strategy = BenchmarkStrategy(
        feed=feed,
        instrument=instruments.keys(),
        capital=1000000.0,
        target='hk_equity_fund'
    )
    benchmark_strategy.run()
    print(benchmark_strategy.getBroker().getEquity())
