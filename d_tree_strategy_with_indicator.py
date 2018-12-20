import talib
import pandas as pd
import numpy as np
from datetime import datetime
from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade.technical import rsi, ma, macd
from pyalgotrade import strategy
from pyalgotrade.stratanalyzer import returns as rets
from pyalgotrade.stratanalyzer import sharpe, drawdown, trades
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor


class DecisionTreeRegressorStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, capital, selected_features):
        super(DecisionTreeRegressorStrategy, self).__init__(feed, capital)
        self.capital = capital
        self.instrument = instrument
        self.mpf_asset = [
            'hk_equity_fund', 'growth_fund', 'balanced_fund', 'conservative_fund', 'hkdollar_bond_fund', 'stable_fund'
        ]
        self.positions = {asset: None for asset in self.mpf_asset}
        self.current_percentages = None
        self.previous_percentages = None
        self.hk_equity_fund_macd = macd.MACD(feed['hk_equity_fund'].getCloseDataSeries(), 12, 26, 9)
        self.hk_equity_fund_macd_histogram = self.hk_equity_fund_macd.getHistogram()
        self.growth_fund_macd = macd.MACD(feed['growth_fund'].getCloseDataSeries(), 12, 26, 9)
        self.growth_fund_macd_histogram = self.growth_fund_macd.getHistogram()
        self.balanced_fund_macd = macd.MACD(feed['balanced_fund'].getCloseDataSeries(), 12, 26, 9)
        self.balanced_fund_macd_histogram = self.balanced_fund_macd.getHistogram()
        self.conservative_fund_macd = macd.MACD(feed['conservative_fund'].getCloseDataSeries(), 12, 26, 9)
        self.conservative_fund_macd_histogram = self.conservative_fund_macd.getHistogram()
        self.hkdollar_bond_fund_macd = macd.MACD(feed['hkdollar_bond_fund'].getCloseDataSeries(), 12, 26, 9)
        self.hkdollar_bond_fund_macd_histogram = self.hkdollar_bond_fund_macd.getHistogram()
        self.stable_fund_macd = macd.MACD(feed['stable_fund'].getCloseDataSeries(), 12, 26, 9)
        self.stable_fund_macd_histogram = self.stable_fund_macd.getHistogram()
        self.hk_equity_fund_rsi = rsi.RSI(feed['hk_equity_fund'].getCloseDataSeries(), 14)
        self.growth_fund_rsi = rsi.RSI(feed['growth_fund'].getCloseDataSeries(), 14)
        self.balanced_fund_rsi = rsi.RSI(feed['balanced_fund'].getCloseDataSeries(), 14)
        self.conservative_fund_rsi = rsi.RSI(feed['conservative_fund'].getCloseDataSeries(), 14)
        self.hkdollar_bond_fund_rsi = rsi.RSI(feed['hkdollar_bond_fund'].getCloseDataSeries(), 14)
        self.stable_fund_rsi = rsi.RSI(feed['stable_fund'].getCloseDataSeries(), 14)
        self.testing_datetime = datetime(2014, 8, 2)
        self.testing_end_datetime = datetime(2018, 1, 15)
        self.pending_order = None
        self.historical_data = list()
        self.historical_df = None
        self.selected_features = selected_features
        self.model = None

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY %s QTY %s at $%.2f" % (position.getInstrument(), execInfo.getQuantity(), execInfo.getPrice()))

    def onEnterCanceled(self, position):
        instrument = position.getInstrument()
        self.positions[instrument] = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        instrument = position.getInstrument()
        self.info("SELL at $%.2f" % (execInfo.getPrice()))
        self.positions[instrument] = None

    def bars_to_data_dict(self, bars, indicators):
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
        for key, val in indicators.iteritems():
            data_dict[key] = val
        return data_dict

    def onHistoricalData(self, bars, indicators):
        data_dict = self.bars_to_data_dict(bars, indicators)
        self.historical_data.append(data_dict)

    def data_preprocess(self, historical_df, days=5):
        y_colnames = list()
        for asset in self.mpf_asset:
            colname = '%s_close_return_t+%s' % (asset, days)
            historical_df[colname] = (historical_df['%s_close' % asset].shift(-days) - historical_df['%s_close' % asset]) / historical_df['%s_close' % asset]
            historical_df[colname] = [1 if val > 0.01 else 0 for val in historical_df[colname]]
            y_colnames.append(colname)
        historical_df = historical_df.dropna()
        X_df = historical_df[self.selected_features]
        y_df = historical_df[y_colnames]
        return X_df.values, y_df.values

    def round_up_normalization(self, percentages):
        '''
        MPF adjustment requiring correct to nearest 1%
        '''
        total = float(sum(percentages.values()))
        if total > 0:
            normalized_percentages = {k: float(v) / total for k, v in percentages.iteritems()}
            percentages_times_100 = {k: int(v * 100) for k, v in normalized_percentages.iteritems()}
            difference = 100 - sum(percentages_times_100.values())
            percentages_times_100['conservative_fund'] += difference
            return {k: float(v) / 100 for k, v in percentages_times_100.iteritems()}
        else:
            return percentages

    def get_all_position_shares(self):
        position_shares = dict()
        for instrument, position in self.positions.iteritems():
            if position is None:
                position_shares[instrument] = None
            else:
                position_shares[instrument] = position.getShares()
        return position_shares

    def get_total_asset_value(self, bars, shares):
        total_value = 0
        for instrument, n_shares in shares.iteritems():
            if n_shares is not None:
                price = bars[instrument].getClose()
                total_value += price * n_shares
        return total_value

    def all_position_exit(self):
        for _, position in self.positions.iteritems():
            if position is not None:
                position.exitMarket()

    def portfolio_adjustment(self, bars, percentages):
        '''
        Buy fund according to percentages
        :param percentages: dictionary of percentages
        ## format
        percentages = {
            'hk_equity_fund': 0.25, 'growth_fund': 0.0, 'balanced_fund': 0.25,
            'conservative_fund': 0.25, 'hkdollar_bond_fund': 0.0, 'stable_fund': 0.25
        }
        :return: None
        '''
        cash = self.getBroker().getEquity() - self.get_total_asset_value(bars, self.get_all_position_shares())
        for asset, percent in percentages.iteritems():
            cash_arranged = percent * cash * 0.99
            shares = int(cash_arranged / bars[asset].getPrice())
            # print('ASSET:%s , shares to buy:%s' % (asset, shares))
            if self.positions[asset] is None and shares > 0:
                self.positions[asset] = self.enterLong(asset, shares, True, False)

    def training_model(self, X, y):
        normalizer = StandardScaler()
        clf = DecisionTreeRegressor(random_state=1)
        pipeline = Pipeline(
            [('normalizer', normalizer),
             ('clf', clf)]
        )
        return pipeline.fit(X, y)

    def onBars(self, bars):
        if 'hk_equity_fund' not in bars.keys():
            return
        indicators = {
            'hk_equity_fund_rsi': self.hk_equity_fund_rsi[-1],
            'growth_fund_rsi': self.growth_fund_rsi[-1],
            'balanced_fund_rsi': self.balanced_fund_rsi[-1],
            'conservative_fund_rsi': self.conservative_fund_rsi[-1],
            'hkdollar_bond_fund_rsi': self.hkdollar_bond_fund_rsi[-1],
            'stable_fund_rsi': self.stable_fund_rsi[-1]
        }
        # updating historical dataset in training time
        if bars['hk_equity_fund'].getDateTime() < self.testing_datetime:
            self.onHistoricalData(bars, indicators)
        elif self.historical_df is None:
            self.historical_df = pd.DataFrame(self.historical_data)
            # drop NaNs
            self.historical_df = self.historical_df.dropna()
            X, y = self.data_preprocess(self.historical_df)
            self.model = self.training_model(X, y)
        if self.model is not None:
            data_dict = self.bars_to_data_dict(bars, indicators)
            X_bar = pd.DataFrame(data_dict, index=[0])[self.selected_features].values
            if any([x is None for x in X_bar[0]]):
                return
            prediction = self.model.predict(X_bar)[0]
            percentages = {asset: val for asset, val in zip(self.mpf_asset, prediction)}
            # print(percentages)
            percentages = self.round_up_normalization(percentages)
            self.current_percentages = percentages
            if self.pending_order is not None:
                self.portfolio_adjustment(bars, percentages)
                self.pending_order = None
            if self.previous_percentages != self.current_percentages:
                self.all_position_exit()
                self.pending_order = percentages
            self.previous_percentages = self.current_percentages


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
    selected_features = list()
    indicators = [
        'hk_equity_fund_rsi', 'growth_fund_rsi', 'balanced_fund_rsi', 'conservative_fund_rsi',
        'hkdollar_bond_fund_rsi', 'stable_fund_rsi'
    ]
    selected_features += indicators
    tree_reg_strategy = DecisionTreeRegressorStrategy(
        feed=feed,
        instrument=instruments.keys(),
        capital=1000000.0,
        selected_features=selected_features
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

    print "Final portfolio value: $%.2f" % tree_reg_strategy.getResult()
    print "Cumulative returns: %.2f %%" % (retAnalyzer.getCumulativeReturns()[-1] * 100)
    print "Sharpe ratio: %.2f" % (sharpeRatioAnalyzer.getSharpeRatio(0.03))
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
