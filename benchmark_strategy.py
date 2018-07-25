from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade import strategy
from pyalgotrade.stratanalyzer import returns as rets
from pyalgotrade.stratanalyzer import sharpe, drawdown, trades


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
        if self.target not in bars.keys():
            return
        bar = bars[self.target]
        close = bar.getPrice()
        # Buy and hold
        if self.positions[self.target] is None:
            amount = int(self.getBroker().getEquity() / close)
            self.positions[self.target] = self.enterLong(self.target, amount, True, False)


def main():
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
    tree_reg_strategy = BenchmarkStrategy(
        feed=feed,
        instrument=instruments.keys(),
        capital=1000000.0,
        target='hk_equity_fund'
    )
    retAnalyzer = rets.Returns()
    tree_reg_strategy.attachAnalyzer(retAnalyzer)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    tree_reg_strategy.attachAnalyzer(sharpeRatioAnalyzer)
    drawDownAnalyzer = drawdown.DrawDown()
    tree_reg_strategy.attachAnalyzer(drawDownAnalyzer)
    tradesAnalyzer = trades.Trades()
    tree_reg_strategy.attachAnalyzer(tradesAnalyzer)
    tree_reg_strategy.run()

    print "Final portfolio value: $%.2f" % tree_reg_strategy.getResult()
    print "Cumulative returns: %.2f %%" % (retAnalyzer.getCumulativeReturns()[-1] * 100)
    print "Sharpe ratio: %.2f" % (sharpeRatioAnalyzer.getSharpeRatio(0.05))
    print "Max. drawdown: %.2f %%" % (drawDownAnalyzer.getMaxDrawDown() * 100)
    print "Longest drawdown duration: %s" % (drawDownAnalyzer.getLongestDrawDownDuration())
    print "Calmar ratio: %.4f" % (retAnalyzer.getCumulativeReturns()[-1] / drawDownAnalyzer.getMaxDrawDown())

    print
    print "Total trades: %d" % (tradesAnalyzer.getCount())
    if tradesAnalyzer.getCount() > 0:
        profits = tradesAnalyzer.getAll()
        print "Avg. profit: $%2.f" % (profits.mean())
        print "Profits std. dev.: $%2.f" % (profits.std())
        print "Max. profit: $%2.f" % (profits.max())
        print "Min. profit: $%2.f" % (profits.min())
        returns = tradesAnalyzer.getAllReturns()
        print "Avg. return: %2.f %%" % (returns.mean() * 100)
        print "Returns std. dev.: %2.f %%" % (returns.std() * 100)
        print "Max. return: %2.f %%" % (returns.max() * 100)
        print "Min. return: %2.f %%" % (returns.min() * 100)

    print
    print "Profitable trades: %d" % (tradesAnalyzer.getProfitableCount())
    if tradesAnalyzer.getProfitableCount() > 0:
        profits = tradesAnalyzer.getProfits()
        print "Avg. profit: $%2.f" % (profits.mean())
        print "Profits std. dev.: $%2.f" % (profits.std())
        print "Max. profit: $%2.f" % (profits.max())
        print "Min. profit: $%2.f" % (profits.min())
        returns = tradesAnalyzer.getPositiveReturns()
        print "Avg. return: %2.f %%" % (returns.mean() * 100)
        print "Returns std. dev.: %2.f %%" % (returns.std() * 100)
        print "Max. return: %2.f %%" % (returns.max() * 100)
        print "Min. return: %2.f %%" % (returns.min() * 100)

    print
    print "Unprofitable trades: %d" % (tradesAnalyzer.getUnprofitableCount())
    if tradesAnalyzer.getUnprofitableCount() > 0:
        losses = tradesAnalyzer.getLosses()
        print "Avg. loss: $%2.f" % (losses.mean())
        print "Losses std. dev.: $%2.f" % (losses.std())
        print "Max. loss: $%2.f" % (losses.min())
        print "Min. loss: $%2.f" % (losses.max())
        returns = tradesAnalyzer.getNegativeReturns()
        print "Avg. return: %2.f %%" % (returns.mean() * 100)
        print "Returns std. dev.: %2.f %%" % (returns.std() * 100)
        print "Max. return: %2.f %%" % (returns.max() * 100)
        print "Min. return: %2.f %%" % (returns.min() * 100)


if __name__ == '__main__':
    main()

