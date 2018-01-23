import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime


class SunLifeFundInfo(object):
    def __init__(self):
        self.conservative_fund = {
            "detail_name": "Sun Life MPF Conservative Fund(Class B)",
            "file_name": "conservative_fund_data.csv",
            "url": '''https://www.sunlife.com.hk/HK/Investments/Pension+services+-+MPF+and+ORSO+Fund+Prices+and+Performance/Sun+Life+Rainbow+MPF+Price+&+Performance/MPF+Past+Prices?vgnLocale=en_CA&type=plancode=13|fundCode=R65-GCRCPF-B|period=LD|reportType=mpf|sdate=12/01/2000|edate=01/15/2018|reportFormat=1|currency=HKD|fundClass=(Class%20B)'''
        }
        self.hkdollar_bond_fund = {
            "detail_name": "Sun Life MPF Hong Kong Dollar Bond Fund(Class B)",
            "file_name": "hkdollar_bond_fund_data.csv",
            "url": '''https://www.sunlife.com.hk/HK/Investments/Pension+services+-+MPF+and+ORSO+Fund+Prices+and+Performance/Sun+Life+Rainbow+MPF+Price+&+Performance/MPF+Past+Prices?vgnLocale=en_CA&type=plancode=13|fundCode=R65-HCRFIG-B|period=LD|reportType=mpf|sdate=12/01/2000|edate=01/15/2018|reportFormat=1|currency=HKD|fundClass=(Class%20B)'''
        }
        self.stable_fund = {
            "detail_name": "Sun Life MPF Stable Fund(Class B)",
            "file_name": "stable_fund_data.csv",
            "url": '''https://www.sunlife.com.hk/HK/Investments/Pension+services+-+MPF+and+ORSO+Fund+Prices+and+Performance/Sun+Life+Rainbow+MPF+Price+&+Performance/MPF+Past+Prices?vgnLocale=en_CA&type=plancode=13|fundCode=R65-JCRSIF-B|period=LD|reportType=mpf|sdate=12/01/2000|edate=01/15/2018|reportFormat=1|currency=HKD|fundClass=(Class%20B)'''
        }
        self.balanced_fund = {
            "detail_name": "Sun Life MPF Balanced Fund(Class B)",
            "file_name": "balanced_fund_data.csv",
            "url": '''https://www.sunlife.com.hk/HK/Investments/Pension+services+-+MPF+and+ORSO+Fund+Prices+and+Performance/Sun+Life+Rainbow+MPF+Price+&+Performance/MPF+Past+Prices?vgnLocale=en_CA&type=plancode=13|fundCode=R65-KCRBPF-B|period=LD|reportType=mpf|sdate=12/01/2000|edate=01/15/2018|reportFormat=1|currency=HKD|fundClass=(Class%20B)'''
        }
        self.growth_fund = {
            "detail_name": "Sun Life MPF Growth Fund(Class B)",
            "file_name": "growth_fund_data.csv",
            "url": '''https://www.sunlife.com.hk/HK/Investments/Pension+services+-+MPF+and+ORSO+Fund+Prices+and+Performance/Sun+Life+Rainbow+MPF+Price+&+Performance/MPF+Past+Prices?vgnLocale=en_CA&type=plancode=13|fundCode=R65-LCRPGF-B|period=LD|reportType=mpf|sdate=12/01/2000|edate=01/15/2018|reportFormat=1|currency=HKD|fundClass=(Class%20B)'''
        }
        self.hk_equity_fund = {
            "detail_name": "Sun Life MPF Hong Kong Equity Fund(Class B)",
            "file_name": "hk_equity_fund_data.csv",
            "url": '''https://www.sunlife.com.hk/HK/Investments/Pension+services+-+MPF+and+ORSO+Fund+Prices+and+Performance/Sun+Life+Rainbow+MPF+Price+&+Performance/MPF+Past+Prices?vgnLocale=en_CA&type=plancode=13|fundCode=R65-ICRHKE-B|period=LD|reportType=mpf|sdate=12/01/2000|edate=01/15/2018|reportFormat=1|currency=HKD|fundClass=(Class%20B)'''
        }
        self.all_fund = [
            self.conservative_fund,
            self.hkdollar_bond_fund,
            self.stable_fund,
            self.balanced_fund,
            self.growth_fund,
            self.hk_equity_fund
        ]

    @staticmethod
    def souping_csv(fund):
        response = requests.get(fund['url'])
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find_all('tbody')[0]
        all_values = table.find_all('tr')
        df = pd.DataFrame(columns=['Date', 'Price'])
        index = 0
        for row in all_values:
            try:
                _date, _price = row.find_all('td')
                _date = datetime.strptime(_date.get_text(), '%d/%m/%Y')
                _price = float(_price.get_text().replace(' ', ''))
                df.loc[index] = [_date, _price]
                index += 1
            except ValueError:
                continue
        path = 'dataset/%s' % fund['file_name']
        df.to_csv(path, index=False)
        print('%s generated' % path)

    def run(self):
        for fund in self.all_fund:
            self.souping_csv(fund)


if __name__ == '__main__':
    sunlife_crawler = SunLifeFundInfo()
    sunlife_crawler.run()
