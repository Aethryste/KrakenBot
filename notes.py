import krakenex
from pykrakenapi import KrakenAPI
import pprint
import pandas as pd

api = krakenex.API()
k = KrakenAPI(api)

data = k.get_asset_info()
pprint.pprint(data)

