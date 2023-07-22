from datetime import datetime
import numpy as np
import pandas as pd
from finta import TA
import matplotlib.pyplot as plt


class Crypto:
    def __init__(self, name, vol, fee):
        self.buy_state = 0
        self.buys = list()
        self.sells = list()
        self.sell_state = 0
        self.flag = 0
        self.vol = vol
        self.fee = fee
        self.crsi_threshold = 5
        self.rsi_threshold = 20
        self.profit_threshold = 0.7 # 0.5
        self.controller_threshold = 1000 # 200
        self.danger_threshold = 10 # 20
        self.loss_threshold = -0.1 # -0.1
        self.profits = list()
        self.df = self.get_df(name)

    def get_df(self, name):
        df = pd.read_csv(name)
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        df.set_index('Datetime', inplace=True)
        df['RSI_3'] = TA.RSI(df, 3)
        df['RSI_2'] = TA.RSI(df, 2)
        df['PCT_RANK'] = df['Close'].rank(pct=True)
        df['CRSI'] = (df['RSI_3'] + df['RSI_2'] + df['PCT_RANK']) / 3
        df['MA'] = TA.SMA(df)
        df['RSI'] = TA.RSI(df)
        # df = df[120:]
        return df

    def get_profit(self, b, s):
        buy_price = (b * self.vol) + self.fee
        sell_price = (s * self.vol) - self.fee
        rate = sell_price - buy_price
        rate_pct = rate / buy_price * 100
        return rate_pct

    def check_danger(self, end):
        cnt = 1
        start = end - self.danger_threshold
        for j in range(start, end):
            if self.df.MA[j] < self.df.MA[j - 1]:
                cnt += 1
            elif self.df.MA[j] > self.df.MA[j - 1]:
                cnt -= 1
        if cnt > 15:
            return 1
        return 0

    def get_action(self, i, controller):
        if self.flag == 0 and self.df.CRSI[i] < self.crsi_threshold and self. df.RSI[i] < self.rsi_threshold:
            self.flag = 1
            return 1
        elif self.flag == 1 and self.get_profit(self.buy_state, self.df.Close[i]) > self.profit_threshold:
            self.flag = 0
            return 0
        elif self.flag == 1 and controller > self.controller_threshold and self.get_profit(self.buy_state, self.df.Close[i]) > self.loss_threshold:
            self.flag = 0
            return 0
        # elif self.flag == 1 and controller > 1500:
        #     self.flag = 0
        #     return 0
        else:
            return -1

workers = dict()
# data4/sol_full.csv
workers['XAUUSD'] = Crypto(name='XAUUSD.csv', vol=11, fee=0.1)

tot_cash = 0
for worker in workers:
    controller = 0
    length = workers[worker].df.shape[0]
    print(length)
    for i in range(5, length):
        if workers[worker].flag == 1:
            controller += 1
        if workers[worker].flag == 0 and workers[worker].check_danger(i) == 1:
            continue
        decision = workers[worker].get_action(i, controller)
        # <BUY> #
        if decision == 1:
            workers[worker].buy_state = workers[worker].df.Close[i]
            workers[worker].buys.append(workers[worker].df.iloc[i])
            continue
        # <SELL> #
        if decision == 0:
            workers[worker].sell_state = workers[worker].df.Close[i]
            workers[worker].sells.append(workers[worker].df.iloc[i])
            profit = workers[worker].get_profit(
                workers[worker].buy_state,
                workers[worker].sell_state
            )
            workers[worker].profits.append(profit)
            workers[worker].buy_state = 0
            workers[worker].sell_state = 0
            controller = 0
            continue

    print(workers[worker].profits)
    cash1 = 500000
    cash2 = 500000
    for profit in workers[worker].profits:
        delta = cash2 * profit / 100
        cash2 += delta
    tot_cash += cash2
    print(cash2)
    print((cash2-cash1)/cash1*100)
    print('----------------------------------------------------------------------------')
print(tot_cash)
tot_cash_first = 1000000
print((tot_cash - tot_cash_first) / tot_cash_first * 100)

# PLOT
cnt = 0
for worker in workers:
    cnt += 1
    plt.subplot(1, 1, cnt)
    if len(workers[worker].buys) > 0 and len(workers[worker].sells) > 0:
        workers[worker].buys = pd.DataFrame(workers[worker].buys)
        workers[worker].sells = pd.DataFrame(workers[worker].sells)
        plt.plot(workers[worker].df.index, workers[worker].df.Close, 'black',
                 workers[worker].buys.index, workers[worker].buys.Close, 'go',
                 workers[worker].sells.index, workers[worker].sells.Close, 'ro')
    elif len(workers[worker].buys) > 0 and len(workers[worker].sells) == 0:
        workers[worker].buys = pd.DataFrame(workers[worker].buys)
        plt.plot(workers[worker].df.index, workers[worker].df.Close, 'black',
                 workers[worker].buys.index, workers[worker].buys.Close, 'go')
    else:
        plt.plot(workers[worker].df.index, workers[worker].df.Close, 'black')
    plt.title(worker)
plt.show()
print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
