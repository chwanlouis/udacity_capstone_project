from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade import strategy


class BenchmarkStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, capital, target):
        super(BenchmarkStrategy, self).__init__(feed, capital)
        self.instrument = instrument
        self.positions = {k: None for k in self.instrument}
        self.target = target

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY %s at $%.2f" % (execInfo.getQuantity(), execInfo.getPrice()))

    def onEnterCanceled(self, position):
        self.positions[self.target] = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info("SELL at $%.2f" % (execInfo.getPrice()))
        self.positions[self.target] = None

    def onBars(self, bars):
        bar = bars[self.target]
        close = bar.getPrice()
        # Buy and hold
        if self.positions[self.target] is None:
            amount = int(self.getBroker().getEquity() / close)
            self.positions[self.target] = self.enterLong(self.target, amount, True, False)


if __name__ == '__main__':
    feed = GenericBarFeed(frequency='DAY')
    instruments = {
        'hk_equity_fund': 'dataset/hk_equity_fund_data.csv',
        'growth_fund': 'dataset/growth_fund_data.csv',
        'balanced_fund': 'dataset/balanced_fund_data.csv',
        'conservative_fund': 'dataset/conservative_fund_data.csv',
        'hkdollar_bond_fund': 'dataset/hkdollar_bond_fund_data.csv',
        'stable_fund': 'dataset/stable_fund_data.csv'
    }
    for instu, fname in instruments.iteritems():
        feed.addBarsFromCSV(instu, fname)
    benchmark_strategy = BenchmarkStrategy(
        feed=feed,
        instrument=instruments.keys(),
        capital=1000000.0,
        target='hk_equity_fund'
    )
    benchmark_strategy.run()
    print(benchmark_strategy.getBroker().getEquity())
