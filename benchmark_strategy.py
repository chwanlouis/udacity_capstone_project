import os
from datetime import datetime
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
        self.testing_datetime = datetime(2014, 8, 2)
        self.testing_end_datetime = datetime(2018, 1, 15)

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
        if bar.getDateTime() < self.testing_datetime:
            return
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
    # selected_features = [
    #     'hk_equity_fund', 'growth_fund', 'balanced_fund', 'conservative_fund', 'hkdollar_bond_fund', 'stable_fund'
    # ]
    # selected_features = list()
    # indicators = [
    #     'hk_equity_fund_rsi', 'growth_fund_rsi', 'balanced_fund_rsi', 'conservative_fund_rsi',
    #     'hkdollar_bond_fund_rsi', 'stable_fund_rsi'
    # ]
    # selected_features += indicators
    # predict_n_days = 30
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

    print('************************')
    print('** Backtesting Report **')
    print('************************')

    portfo_val = tree_reg_strategy.getResult()
    print "Final portfolio value: $%.2f" % portfo_val
    cumulative_returns = retAnalyzer.getCumulativeReturns()[-1]
    print "Cumulative returns: %.2f %%" % (cumulative_returns * 100)
    sharpe_ratio = sharpeRatioAnalyzer.getSharpeRatio(0.03)
    print "Sharpe ratio: %.2f" % (sharpe_ratio)
    mdd = drawDownAnalyzer.getMaxDrawDown()
    print "Max. drawdown: %.2f %%" % (mdd * 100)
    print "Longest drawdown duration: %s" % (drawDownAnalyzer.getLongestDrawDownDuration())
    if mdd > 0:
        calmar_ratio = retAnalyzer.getCumulativeReturns()[-1] / mdd
        print "Calmar ratio: %.4f" % (calmar_ratio)
    else:
        calmar_ratio = None

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
    return portfo_val, cumulative_returns, sharpe_ratio, mdd, calmar_ratio


def logger(string, file_name):
    if not os.path.isfile(file_name):
        mode = 'w'
    else:
        mode = 'a'
    if '\n' not in string:
        string += '\n'
    with open(file_name, mode) as file:
        file.write(string)


if __name__ == '__main__':
    log_file_name = 'log/walk_forward_backtesting_result_sec_3.txt'
    portfo_val, cumulative_returns, sharpe_ratio, mdd, calmar_ratio = main()
    model_form = 'benchmark'
    selected_features = []
    predict_n_days = 'NA'
    model_form_string = 'model_form:%s' % model_form
    selected_features_string = 'selected_features:%s' % ','.join(selected_features)
    predict_n_days_string = 'predict_n_days:%s' % predict_n_days
    portfo_val_string = 'portfo_val:%s' % portfo_val
    cumulative_returns_string = 'cumulative_returns:%s' % cumulative_returns
    sharpe_ratio_string = 'sharpe_ratio:%s' % sharpe_ratio
    mdd_string = 'mdd:%s' % mdd
    calmar_string = 'calmar_ratio:%s' % calmar_ratio
    logger(model_form_string, log_file_name)
    logger(selected_features_string, log_file_name)
    logger(predict_n_days_string, log_file_name)
    logger(calmar_string, log_file_name)
    logger(portfo_val_string, log_file_name)
    logger(cumulative_returns_string, log_file_name)
    logger(sharpe_ratio_string, log_file_name)
    logger(mdd_string, log_file_name)
    logger('\n', log_file_name)

