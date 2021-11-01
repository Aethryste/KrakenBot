import websocket
import json
import pandas as pd

SOCKET = 'wss://ws.kraken.com/'

price_high = 0
price_low = 0
price_close = 0
df_prices = pd.DataFrame()


def ws_open(ws):
    print("[This script will now track '[ETH/EUR]' on 'Kraken']")
    print("[opened connection.]")
    ws.send('{"event":"subscribe", "subscription":{"name":"ohlc"}, "pair":["ETH/EUR"]}')


def ws_close():
    print("[connection closed.]")


def last_values():  # Testing function
    print(f'current high price: [€{round(float(price_high), 2)}]')
    print(f'current low price: [€{round(float(price_low), 2)}]')
    print(f'current closing price: [€{round(float(price_close), 2)}]')
    print()


def ws_message(ws, message):
    global df_prices, price_high, price_low, price_close
    # print("[Received message.]")
    json_message = json.loads(message)
    price_high = json_message[1][3]
    price_low = json_message[1][4]
    price_close = json_message[1][5]

    main()


def append_dataframe():
    global df_prices, price_high, price_low, price_close
    df_update = pd.DataFrame(
        data={
            'high': price_high,
            'low': price_low,
            'close': price_close
        },
        columns=('high', 'low', 'close'),
        index=[0])
    df_prices = df_prices.append(df_update, ignore_index=True)
    print(f"[Dataframe] {len(df_prices['close'])} data sets have been collected.")


def calculate_rsi(df, period=14):
    global df_prices
    if len(df_prices['close']) >= period:
        print('CP1 passed')
        delta = df_prices['close'].diff(1)
        print(delta)

    else:
        print('[RSI] waiting for data..')
        print()


def main():
    global df_prices
    append_dataframe()
    last_values()
    calculate_rsi(df=df_prices, period=3)


ws = websocket.WebSocketApp(SOCKET, on_open=ws_open, on_close=ws_close, on_message=ws_message)
ws.run_forever()
