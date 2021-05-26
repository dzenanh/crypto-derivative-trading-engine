from diversifly.components.globals import Client
from diversifly.components.core.executor import DFlyExecutor
from diversifly.components.products.strategies.strategy2 import DFlyMarketNeutralStrat2
from diversifly.components.products.strategies.strategy3 import DFlyMarketNeutralStrat3
from diversifly.components.products.strategies.strategy4 import DFlyMarketNeutralStrat4

MYKEY = 'MY_KEY'
MYSECRET = 'MY_SECRET'
# own client for testing
client = Client(MYKEY, MYSECRET)
# public API for fetching prices
public_client = Client()
'''
list_of_keys2 = [
    {'user_id':"User1", 'key': "OTHER_KEY", 'secret': "OTHER_SECRET"},
    {'user_id':"User2", 'key': MYKEY, 'secret': MYSECRET}]
'''
list_of_keys = [{'user_id':"User1", 'key': MYKEY, 'secret': MYSECRET}]


usdt_amount_to_trade = 10
trade_mode = "DRYRUN" #"DRYRUN" # "LIVE"
list_of_strategies = [DFlyMarketNeutralStrat2("Emp MN2", None, 20),
                      DFlyMarketNeutralStrat3("Emp MN3", None, 30),
                      DFlyMarketNeutralStrat4("Emp MN4", None, 30)]

# run
DFlyExecutor("DFlyExecutor", list_of_strategies, public_client, list_of_keys, trade_mode).execute()