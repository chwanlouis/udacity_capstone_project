import pandas as pd
from datetime import datetime, timedelta
from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade.technical import rsi, ma, macd
from pyalgotrade import strategy
from pyalgotrade.stratanalyzer import returns as rets
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor


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
        # self.testing_datetime = datetime(2014, 8, 2)
        # self.testing_end_datetime = datetime(2018, 1, 15)
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
        days = ((time_end - time_start) / sections).days
        time_length = timedelta(days=days)
        time_points = list()
        for i in range(sections):
            time_points.append(time_start)
            time_start += time_length
        return time_points

    def get_retrain_time_point(self):
        if len(self.retrain_time_points) > 0:
            return self.retrain_time_points.pop(0)
        else:
            return

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

    def data_preprocess(self, historical_df, days=30):
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
        return self.model_form.fit(X, y)

    def onBars(self, bars):
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
    capital = 1000000.0
    tree_reg_strategy = WalkForwardBacktester(
        feed=feed,
        instrument=instruments.keys(),
        capital=capital,
        selected_features=selected_features,
        predict_n_days=predict_n_days,
        model_form=model_form,
        testing_datetime=testing_datetime,
        testing_end_datetime=testing_end_datetime,
        n_retrain_times=n_retrain_times
    )
    retAnalyzer = rets.Returns()
    tree_reg_strategy.attachAnalyzer(retAnalyzer)
    tree_reg_strategy.run()
    equity_curve = list()
    for ret in retAnalyzer.getCumulativeReturns():
        equity_curve.append(capital * (1 + ret))
    return equity_curve


def drawdown_curve(_price):
    dd = list()
    peak = _price[0]
    for x in _price:
        if x > peak:
            peak = x
        dd.append((x - peak) / peak)
    return dd


if __name__ == '__main__':
    selected_features = ['HSI_close', 'IXIC_close', 'us2yrby_close', 'us10yrby_close']
    predict_n_days = 5
    model_form = Pipeline([('normalizer', StandardScaler()), ('clf', DecisionTreeRegressor(random_state=1))])
    testing_start = datetime(2014, 8, 2)
    testing_end = datetime(2018, 1, 15)
    section = 10
    eqty_curve = main(selected_features, predict_n_days, model_form, testing_start, testing_end, section)
    dd_curve = drawdown_curve(eqty_curve)
    df = pd.DataFrame({
        'equity_curve': eqty_curve,
        'dd_curve': dd_curve
    })
    plt1 = df[['equity_curve']].plot(figsize=(12, 8))
    fig1 = plt1.get_figure()
    fig1.savefig('best_sol_equity.png')
    plt2 = df[['dd_curve']].plot(figsize=(12, 8), style='r-')
    fig2 = plt2.get_figure()
    fig2.savefig('best_sol_dd.png')
