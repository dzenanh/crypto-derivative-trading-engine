from diversifly.components.globals import *
from diversifly.components.core.data_download import DFlyDataDownload


# public API
public_client = Client("", "")


list_of_assets = ["DEFIUSDT","BANDUSDT","BTCUSDT","ETHUSDT"]
data = DFlyDataDownload("TEST", public_client, "1h", 400, 1000, list_of_assets, 10).get_data()
print(data)
# run strategy
#pair_signal = DFlyMarketNeutralStrat("MarketNeutral-DEFIBAND", data, list_of_assets, 40).get_signal()
#pair_info = ({"asset1":"DEFIUSDT","asset2":"BANDUSDT","position":0, "moneyAmount":58},)
#pair_info = (pair_signal,)