import os
import pandas as pd
from datetime import datetime, timedelta
from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade.technical import rsi, macd
from pyalgotrade import strategy
from pyalgotrade.stratanalyzer import returns as rets
from pyalgotrade.stratanalyzer import sharpe, drawdown, trades
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor
from sklearn.neural_network import MLPClassifier


class WalkForwardBacktester(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, capital, selected_features, predict_n_days, model_form,
                 testing_datetime, testing_end_datetime, n_retrain_times):
        super(WalkForwardBacktester, self).__init__(feed, capital)
        self.capital = capital
        self.instrument = instrument
        self.mpf_asset = [
            'hk_equity_fund', 'growth_fund', 'balanced_fund', 'conservative_fund', 'hkdollar_bond_fund', 'stable_fund'
        ]
        self.positions = {asset: None for asset in self.mpf_asset}
        self.current_percentages = None
        self.previous_percentages = None
        # technical indicators is denfined here
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
        self.testing_datetime = testing_datetime
        self.testing_end_datetime = testing_end_datetime
        self.n_retrain_times = n_retrain_times
        self.retrain_time_points = self.generate_retrain_time_point(
            self.testing_datetime, self.testing_end_datetime, self.n_retrain_times)
        self.retrain_time = self.get_retrain_time_point()
        self.pending_order = None
        self.historical_data = list()
        self.historical_df = None
        self.selected_features = selected_features
        self.predict_n_days = predict_n_days
        self.model_form = model_form
        self.model = None

    @staticmethod
    def generate_retrain_time_point(time_start, time_end, sections):
        '''
        Generate stopping points for re-training the model
        :param time_start: datetime.datetime object
        :param time_end: datetime.datetime object
        :param sections: int object
        :return: list object
        '''
        days = ((time_end - time_start) / sections).days
        time_length = timedelta(days=days)
        time_points = list()
        for i in range(sections):
            time_points.append(time_start)
            time_start += time_length
        return time_points

    def get_retrain_time_point(self):
        '''
        Getting time point for calling this function
        :return: datetime.datetime object
        '''
        if len(self.retrain_time_points) > 0:
            return self.retrain_time_points.pop(0)
        else:
            return

    def onEnterOk(self, position):
        '''
        This function will be triggerd if the position is filled
        :param position:
        :return:
        '''
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY %s QTY %s at $%.2f" % (position.getInstrument(), execInfo.getQuantity(), execInfo.getPrice()))

    def onEnterCanceled(self, position):
        '''
        This function will be triggerd if a open order is cancelled
        :param position:
        :return:
        '''
        instrument = position.getInstrument()
        self.positions[instrument] = None

    def onExitOk(self, position):
        '''
        This function will be triggered if a position is closed
        :param position:
        :return:
        '''
        execInfo = position.getExitOrder().getExecutionInfo()
        instrument = position.getInstrument()
        self.info("SELL at $%.2f" % (execInfo.getPrice()))
        self.positions[instrument] = None

    def bars_to_data_dict(self, bars, indicators):
        '''
        This functions transform bar object and indicators to a dict object
        :param bars: pyalgotrade.bar.Bar object
        :param indicators: dict object
        :return: dict object
        '''
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
        '''
        data transformation and storage
        :param bars:
        :param indicators:
        :return:
        '''
        data_dict = self.bars_to_data_dict(bars, indicators)
        self.historical_data.append(data_dict)

    def data_preprocess(self, historical_df, days=30):
        '''
        Generate input data and labels
        :param historical_df: pandas.DataFrame object
        :param days: int object
        :return: numpy.ndarray, numpy.ndarray
        '''
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
        '''
        get current asset shares
        :return: dict object
        '''
        position_shares = dict()
        for instrument, position in self.positions.iteritems():
            if position is None:
                position_shares[instrument] = None
            else:
                position_shares[instrument] = position.getShares()
        return position_shares

    def get_total_asset_value(self, bars, shares):
        '''
        get current asset total value
        :return: float object
        '''
        total_value = 0
        for instrument, n_shares in shares.iteritems():
            if n_shares is not None:
                price = bars[instrument].getClose()
                total_value += price * n_shares
        return total_value

    def all_position_exit(self):
        '''
        close all current position
        :return:
        '''
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
        '''
        fit the model given defined model form and dataset
        :param X: numpy.ndarray object
        :param y: numpy.ndarray object
        :return: fitted model
        '''
        return self.model_form.fit(X, y)

    def onBars(self, bars):
        '''
        This function will be triggered everytime a new bar is come
        :param bars:
        :return:
        '''
        if 'hk_equity_fund' not in bars.keys():
            return
        indicators = {
            'hk_equity_fund_rsi': self.hk_equity_fund_rsi[-1],
            'growth_fund_rsi': self.growth_fund_rsi[-1],
            'balanced_fund_rsi': self.balanced_fund_rsi[-1],
            'conservative_fund_rsi': self.conservative_fund_rsi[-1],
            'hkdollar_bond_fund_rsi': self.hkdollar_bond_fund_rsi[-1],
            'stable_fund_rsi': self.stable_fund_rsi[-1],
            'hk_equity_fund_macd_histogram': self.hk_equity_fund_macd_histogram[-1],
            'growth_fund_macd_histogram': self.growth_fund_macd_histogram[-1],
            'balanced_fund_macd_histogram': self.balanced_fund_macd_histogram[-1],
            'conservative_fund_macd_histogram': self.conservative_fund_macd_histogram[-1],
            'hkdollar_bond_fund_macd_histogram': self.hkdollar_bond_fund_macd_histogram[-1],
            'stable_fund_macd_histogram': self.stable_fund_macd_histogram[-1]
        }
        # updating historical dataset in training time
        self.onHistoricalData(bars, indicators)
        if self.retrain_time is not None and bars['hk_equity_fund'].getDateTime() > self.retrain_time:
            self.historical_df = pd.DataFrame(self.historical_data)
            # drop NaNs
            self.historical_df = self.historical_df.dropna()
            X, y = self.data_preprocess(self.historical_df, self.predict_n_days)
            self.model = self.training_model(X, y)
            self.retrain_time = self.get_retrain_time_point()
            print('Retrain model ...')
            print(bars['hk_equity_fund'].getDateTime())
            print(len(self.historical_df))
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


def main(selected_features, predict_n_days, model_form, testing_datetime, testing_end_datetime, n_retrain_times):
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
    tree_reg_strategy = WalkForwardBacktester(
        feed=feed,
        instrument=instruments.keys(),
        capital=1000000.0,
        selected_features=selected_features,
        predict_n_days=predict_n_days,
        model_form=model_form,
        testing_datetime=testing_datetime,
        testing_end_datetime=testing_end_datetime,
        n_retrain_times=n_retrain_times
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
    print(string)


if __name__ == '__main__':
    if not os.path.isdir('log'):
        os.mkdir('log')
    selected_features_list = [
        ['HSI_close', 'IXIC_close'],
        ['us2yrby_close', 'us10yrby_close'],
        ['HSI_close', 'IXIC_close', 'us2yrby_close', 'us10yrby_close'],
        ['hk_equity_fund_rsi', 'growth_fund_rsi', 'balanced_fund_rsi', 'conservative_fund_rsi',
         'hkdollar_bond_fund_rsi', 'stable_fund_rsi'],
        ['hk_equity_fund_macd_histogram', 'growth_fund_macd_histogram',
         'balanced_fund_macd_histogram', 'conservative_fund_macd_histogram', 'hkdollar_bond_fund_macd_histogram',
         'stable_fund_macd_histogram'],
        ['hk_equity_fund_rsi', 'growth_fund_rsi', 'balanced_fund_rsi', 'conservative_fund_rsi',
         'hkdollar_bond_fund_rsi', 'stable_fund_rsi', 'hk_equity_fund_macd_histogram', 'growth_fund_macd_histogram',
         'balanced_fund_macd_histogram', 'conservative_fund_macd_histogram', 'hkdollar_bond_fund_macd_histogram',
         'stable_fund_macd_histogram']
    ]
    predict_n_days_list = [5, 10, 20, 30, 40, 50, 60]
    model_forms = {
        'decision_tree': Pipeline([('normalizer', StandardScaler()), ('clf', DecisionTreeRegressor(random_state=1))]),
        'mlp_classifier': Pipeline([('normalizer', StandardScaler()), ('clf', MLPClassifier(random_state=1))])
    }
    testing_start = datetime(2014, 8, 2)
    testing_end = datetime(2018, 1, 15)
    # sections = [2, 3, 4, 5, 6, 7, 8, 9, 10]
    sections = [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
    # time_slots = generate_time_slots(testing_start, testing_end, sections)
    results = list()
    for sec in sections:
        log_file_name = 'log/walk_forward_backtesting_result_sec_%s.txt' % sec
        for selected_features in selected_features_list:
            for predict_n_days in predict_n_days_list:
                for model_string, model_form in model_forms.items():
                    portfo_val, cumulative_returns, sharpe_ratio, mdd, calmar_ratio = \
                        main(selected_features, predict_n_days, model_form, testing_start, testing_end, sec)
                    results.append([selected_features, predict_n_days, calmar_ratio])
                    model_form_string = 'model_form:%s' % model_string
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
