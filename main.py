# Resources
import krakenex
from pykrakenapi import KrakenAPI
import time
import pandas as pd

# API init
api = krakenex.API()
k = KrakenAPI(api)

# Globals & settings
running = True
interval = 60  # int(1) == new data every 1 second.
RSI_sell = 70  # [RSI] overbought trigger.
RSI_buy = 30  # {RSI} oversold trigger.

price_high = 0
price_low = 0
price_close = 0
last_RSI = 50  # [RSI] init.


# Functions
def get_coin_data(pair='ETHEUR'):
    """
    Function to collect and separate ticker data such as high, low, and close -prices.
    :param pair: (string) coin-tag + fiat in capitals as the desired ticker. none='ETHEUR'.
    :return:
    """
    global price_high, price_low, price_close
    coin_data = k.get_ticker_information(pair='ETHEUR')
    price_high = round(float(coin_data['h'][0][0]), 2)
    price_low = round(float(coin_data['l'][0][0]), 2)
    price_close = round(float(coin_data['c'][0][0]), 2)


def save_coin_data():
    """
    Function to save the last collected ticker-data to coin_data.csv.
    :return:
    """
    df_database = pd.read_csv('coin_data.csv')
    df_new_set = pd.DataFrame(
        data={
            'price_high': price_high,
            'price_low': price_low,
            'price_close': price_close
        },
        columns=('price_high', 'price_low', 'price_close'),
        index=[0]
    )

    df_database = pd.concat([df_database, df_new_set])
    df_database.to_csv('coin_data.csv', index=False)


def calculate_rsi(period=14):
    """
    Function to calculate RSI based on the data contained in 'coin_data.csv'.
    :param period: int: number of collected values to calculate RSI over. none=14 (standard)
    :return:
    """
    global last_RSI
    df_price_close = pd.read_csv('coin_data.csv', usecols=['price_close'])[:period]
    if len(df_price_close) == period:
        delta = df_price_close.diff(1)

        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        raw_rsi = 100 - (100 / (1 + (ema_up / ema_down)))
        rsi = round(raw_rsi['price_close'][13], 2)
        last_RSI = rsi

    else:
        print(f'[RSI] Waiting on data..  ({len(df_price_close)} of {period} data sets collected.)')


def check_triggers():
    """
    Function to check if all BUY or SELL triggers have been met.
    :return:
    """
    if last_RSI > RSI_sell:  # (Overbought trigger = sell)
        print(f'[RSI] Overbought, Sell!')
    elif last_RSI < RSI_buy:  # (Oversold trigger = buy)
        print(f'[RSI] Oversold, Buy!')
    else:
        print(f'[RSI] {last_RSI}, hold..')


def kraken_buy():
    pass  # buy code here.


def kraken_sell():
    pass  # sell code here.


def print_coin_data():  # test function.
    print(f'[A new data set has been collected.]\n'
          f'[High] €{price_high}\n'
          f'[Low] €{price_low}\n'
          f'[Close] €{price_close}\n'
          f'')


# Main loop.
if __name__ == "__main__":
    while running:
        get_coin_data()
        # print_coin_data()
        save_coin_data()
        calculate_rsi()
        check_triggers()
        time.sleep(interval)
