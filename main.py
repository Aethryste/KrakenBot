# Resources.
import krakenex
from pykrakenapi import KrakenAPI
import config
import time
import pandas as pd
from numpy import floor

# User-settings (config.py).
C_interval = config.collection_interval
RSI_sell = config.RSI_sell
RSI_buy = config.RSI_buy
TICKER = config.ticker
BPD = config.buy_price_deviation

# Globals
running = True
RSI_ready = False
BB_ready = False
account_balance = 0
last_RSI = 50  # RSI initial state, to prevent false triggers at startup.
price_high = 0
price_low = 0
price_close = 0
bollinger_upper = 0
bollinger_lower = 0

# List of (trading)triggers.
T_RSI_buy = False
T_RSI_sell = False
T_BB_buy = False
T_BB_sell = False
T_IPoC = False

# API init.
api = krakenex.API()  # key=config.API_KEY, secret=config.PRIVATE_KEY
k = KrakenAPI(api)

# Paper-trading, testing purposes.
paper_trading = 10000  # 10k init.
IPoC = 0


# Functions
def get_coin_data(pair='ETHEUR'):
    """
    Function to collect and separate ticker data such as high, low, and close -prices.
    :param pair: (string) coin-tag + fiat in capitals as the desired ticker. none='ETHEUR'.
    :return:
    """
    global price_high, price_low, price_close
    coin_data = k.get_ticker_information(pair=pair)
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
    Function to calculate RSI based on the data within 'coin_data.csv'.
    :param period: int: number of collected values to calculate over. none=14 (standard)
    :return:
    """
    global last_RSI, RSI_ready
    df_price_close = pd.read_csv('coin_data.csv', usecols=['price_close'])[-period:]
    if len(df_price_close) == period:
        RSI_ready = True

        delta = df_price_close.diff(1)
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()

        raw_rsi = 100 - (100 / (1 + (ema_up / ema_down)))
        rsi = raw_rsi['price_close'][-1:]
        last_RSI = round(rsi.values[0], 2)

    else:
        print(f'[RSI] Collecting data..  ({len(df_price_close)} of {period} data sets collected.)')


def calculate_bollinger(period=20):
    """
    Function to calculate 'Bollinger bands' based on the data within 'coin_data.csv'.
    :param period: int: number of collected values to calculate over. none=20 (standard)
    :return:
    """
    global bollinger_upper, bollinger_lower, BB_ready
    df_price_close = pd.read_csv('coin_data.csv', usecols=['price_close'])[-period:]

    if len(df_price_close) == period:
        BB_ready = True
        raw_sma = df_price_close.rolling(period).mean()  # sma = 'simple moving average'.
        sma = round(raw_sma['price_close'][-1:].values[0], 2)
        raw_std = df_price_close.rolling(period).std()  # std = 'Standard deviation'.
        std = round(raw_std['price_close'][-1:].values[0], 2)
        bollinger_upper = sma + std * 2
        bollinger_lower = sma - std * 2

    else:
        print(f'[Bollinger-bands] Collecting data..  ({len(df_price_close)} of {period} data sets collected.)')


def check_triggers():
    """
    Function to check if all BUY or SELL triggers have been met.
    :return:
    """
    global T_RSI_buy, T_RSI_sell, T_BB_buy, T_BB_sell

    # Checking each trigger.
    if RSI_ready and BB_ready:
        if last_RSI < RSI_buy:
            T_RSI_buy = True
        if price_close <= bollinger_lower:
            T_BB_buy = True
        if last_RSI > RSI_sell:
            T_RSI_sell = True
        if price_close >= bollinger_upper:
            T_BB_sell = True

    # All buy-related outcomes.
    if T_RSI_buy and T_BB_buy:
        print(f'[RSI] Oversold, Buy!\n'
              f'[Bollinger-bands] Breakout, Buy!')
        # kraken_buy():
        paper_buy()
    elif T_RSI_buy and not T_BB_buy:
        print(f'[RSI] Oversold, Buy!\n'
              f'[Bollinger-bands] no breakout though..\n'
              f'[difference to lower band: {round((price_close - bollinger_lower), 2)}]')
    elif T_BB_buy and not T_RSI_buy:
        print(f'[Bollinger-bands] Breakout, Buy!\n'
              f'[RSI] not yet..\n'
              f'[Current RSI: {last_RSI}]')

    # All sell-related outcomes.
    if T_RSI_sell and T_BB_sell:
        print(f'[RSI] Overbought, Sell!\n'
              f'[Bollinger-bands] Breakout, Sell!')
        # kraken_sell():
        paper_sell()
    elif T_RSI_sell and not T_BB_sell:
        print(f'[RSI] Overbought, Sell!\n'
              f'[Bollinger-bands] no breakout though..\n'
              f'[difference to upper band: {round((bollinger_upper - price_close), 2)}]')
    elif T_BB_sell and not T_RSI_sell:
        print(f'[Bollinger-bands] Breakout, Sell!\n'
              f'[RSI] not yet..\n'
              f'[Current RSI: {last_RSI}]')


def reset_triggers():
    global T_RSI_buy, T_RSI_sell, T_BB_buy, T_BB_sell
    T_RSI_buy = False
    T_RSI_sell = False
    T_BB_buy = False
    T_BB_sell = False


def kraken_balance():  # WIP
    global account_balance
    account_balance = k.get_account_balance()
    print(account_balance)


def kraken_buy():  # WIP
    volume = floor(paper_trading/price_close)
    api_nonce = str(int(time.time() * 1000))
    api.query_private('AddOrder',
                    {'nonce': api_nonce,
                     'pair': TICKER,
                     'type': 'buy',
                     'ordertype': 'limit',
                     'leverage': 'none',
                     'volume': volume,
                     'price': (price_close + BPD)
                     })


def kraken_sell():
    pass  # sell code here.


# For testing
def paper_buy():
    global paper_trading, IPoC, price_close, T_IPoC
    if T_IPoC:
        print('[BUY:prevented][Already in possession of crypto.]')
    else:
        IPoC = floor(paper_trading/price_close)
        paper_trading -= IPoC * price_close
        T_IPoC = True
        print(f'[BUY:successful][We now own {IPoC} {TICKER[:2]}.]')


# For testing
def paper_sell():
    global paper_trading, IPoC, price_close, T_IPoC
    if not T_IPoC:
        print('[SELL:prevented][No crypto in possession.]')
    else:
        paper_trading += IPoC * price_close
        IPoC = 0
        T_IPoC = False
        print(f'[SELL:successful][current account worth: {paper_trading}.]')


def status_rapport():
    """
    Function to print the latest data to console.
    :return:
    """
    global last_RSI, bollinger_lower, bollinger_upper, price_close
    if RSI_ready and BB_ready:
        print(f'[STATUS RAPPORT]\n'
              f'[RSI: {last_RSI}]\n'
              f'-----------------\n'
              f'[BOLLINGER]\n'
              f'[high] {round(bollinger_upper, 2)}\n'
              f'[price] {price_close}\n'
              f'[low] {round(bollinger_lower, 2)}')
    else:
        print('[STATUS RAPPORT] Collecting data..')


# Main loop.
if __name__ == "__main__":
    print(f'[KrakenBot:ACTIVE]\n'
          f'[SETTINGS: [TICKER:{TICKER}][RSI]buy:{RSI_buy}/sell:{RSI_sell}]\n'
          f'')
    while running:
        get_coin_data(pair=TICKER)
        save_coin_data()
        calculate_rsi(period=14)
        calculate_bollinger(period=20)
        check_triggers()

        status_rapport()
        reset_triggers()

        time.sleep(C_interval)
        print()
