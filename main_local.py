from diversifly.components.globals import Client
from diversifly.components.core.executor import DFlyExecutor


MYKEY = 'MY_KEY'
MYSECRET = 'MY_SECRET'
# own client for testing
client = Client(MYKEY, MYSECRET)
# public API for fetching prices
public_client = Client("","")
'''
list_of_keys2 = [
    {'user_id':"User1", 'key': "OTHER_KEY", 'secret': "OTHER_SECRET"},
    {'user_id':"User2", 'key': MYKEY, 'secret': MYSECRET}]
'''
list_of_keys = [{'user_id':"User1", 'key': MYKEY, 'secret': MYSECRET}]


assets_to_trade = ["LINKUSDT","BANDUSDT"]
usdt_amount_to_trade = 20
trade_mode = "DRYRUN" # "LIVE"
interval = Client.KLINE_INTERVAL_1MINUTE

# run
DFlyExecutor("DFlyExecutor", interval, public_client, assets_to_trade, usdt_amount_to_trade, list_of_keys, trade_mode).execute()