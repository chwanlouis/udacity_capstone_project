import time
import pandas as pd
from random import randint
from pyalgotrade.barfeed.csvfeed import GenericBarFeed
from pyalgotrade import strategy


class LogisticRegressionStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, capital):
        super(LogisticRegressionStrategy, self).__init__(feed, capital)
        self.instrument = instrument
        self.mpf_asset = [
            'hk_equity_fund', 'growth_fund', 'balanced_fund', 'conservative_fund', 'hkdollar_bond_fund', 'stable_fund'
        ]
        self.positions = {asset: None for asset in self.mpf_asset}
        self.current_percentages = None
        self.previous_percentages = None
        self.pending_order = list()
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

    def onEnterCanceled(self, position):
        instrument = position.getInstrument()
        self.positions[instrument] = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        instrument = position.getInstrument()
        self.info("SELL at $%.2f" % (execInfo.getPrice()))
        self.positions[instrument] = None

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

    def round_up_normalization(self, percentages):
        '''
        MPF adjustment requiring correct to nearest 1%
        '''
        total = float(sum(percentages.values()))
        normalized_percentages = {k: float(v) / total for k, v in percentages.iteritems()}
        percentages_times_100 = {k: int(v * 100) for k, v in normalized_percentages.iteritems()}
        difference = 100 - sum(percentages_times_100.values())
        percentages_times_100['conservative_fund'] += difference
        return {k: float(v) / 100 for k, v in percentages_times_100.iteritems()}

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
            # cash_arranged = percent * cash
            # hands = int(cash_arranged / bars[asset].getPrice()) / 50000
            # shares = hands * 5000
            shares = 1
            # print('ASSET:%s , shares to buy:%s' % (asset, shares))
            if self.positions[asset] is None and shares > 0:
                self.positions[asset] = self.enterLong(asset, shares, True, False)

    def onBars(self, bars):
        # updating historical dataset
        self.onHistoricalData(bars)
        # dt = bar.getDateTime()
        # close = bar.getPrice()
        if 'hk_equity_fund' not in bars.keys():
            return
        percentages = {
            'hk_equity_fund': randint(1, 100),
            'growth_fund': randint(1, 100),
            'balanced_fund': randint(1, 100),
            'conservative_fund': randint(1, 100),
            'hkdollar_bond_fund': randint(1, 100),
            'stable_fund': randint(1, 100)
        }
        percentages = self.round_up_normalization(percentages)
        self.current_percentages = percentages
        if self.previous_percentages != self.current_percentages:
            self.all_position_exit()
            self.portfolio_adjustment(bars, percentages)
        self.previous_percentages = self.current_percentages


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
    logit_reg_strategy = LogisticRegressionStrategy(
        feed=feed,
        instrument=instruments.keys(),
        capital=1000.0
    )
    logit_reg_strategy.run()
    print(logit_reg_strategy.getBroker().getEquity())
