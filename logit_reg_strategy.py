from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade import strategy


class BenchmarkStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, capital, target):
        super(BenchmarkStrategy, self).__init__(feed)
        self.instrument = instrument
        self.position = None
        self.capital = capital
        self.target = target

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY %s at $%.2f" % (execInfo.getQuantity(), execInfo.getPrice()))

    def onBars(self, bars):
        if self.target not in bars.keys():
            return
        bar = bars[self.target]
        close = bar.getPrice()
        # Buy and hold
        amount = self.capital / close
        if self.position is None and amount >= 1:
            self.position = self.enterLong(self.target, amount, True, False)


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
