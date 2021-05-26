from binance.exceptions import BinanceAPIException

from diversifly.components.globals import logging, Client, pd, get_finished_bars, get_finished_bars2, datetime, BinanceSocketManager, itertools
from diversifly.components.core.data_download import DFlyDataDownload
from diversifly.components.products.strategies.strategy2 import DFlyMarketNeutralStrat2
from diversifly.components.products.strategies.strategy3 import DFlyMarketNeutralStrat3
from diversifly.components.core.broker import DFlyBroker

class DFlyExecutor:
    '''
    mode: "LIVE" | "DRYRUN"
    '''

    def __init__(self, name, strategy_list, exchange_client, list_of_dict_user_product_info, mode):
        self.LAST_MINUTE = -1
        self.LAST_HOUR = -1
        self.LAST_WEEK = -1
        self.LAST_FORMED_BAR = -1
        self.name = name
        self.client = exchange_client
        #self.STRATEGY_RUN_INTERVAL = timeinterval
        self.list_of_assets = []
        self.user_info_list = list_of_dict_user_product_info
        self.ticker_error = {'error': False}
        self.bsm = None
        self.conn_key = None
        self.client_conn_list = []
        self.init_clients()
        self.mode = mode
        ### list of strategies
        self.strategy_list = strategy_list
        self.init_asset_list()

    def get_public_bars(self, STRATEGY_RUN_INTERVAL):
        try:
            return get_finished_bars(self.client, 'BTCUSDT', STRATEGY_RUN_INTERVAL, "60 minute ago UTC", "FUT").result()

        except (Exception ,ConnectionError, ConnectionResetError, BinanceAPIException) as e:
            logging.critical(f"{self.name} in get_public_bars Exception: ConnectionError")
            logging.info(f"{self.name} Initializing new Client()")
            self.client = Client()
            self.get_public_bars(STRATEGY_RUN_INTERVAL)



    def get_public_connection(self):
        '''
        TODO
        :return:
        '''
        return None

    def init_asset_list(self):
        '''
        generate list of assets from all strategies
        :return: [assets]
        '''
        assert len(self.strategy_list) > 0
        # get list of assets
        self.list_of_assets = []
        for empty_strategy in self.strategy_list:
            self.list_of_assets.append(empty_strategy.get_assets())
        self.list_of_assets = list(itertools.chain(*self.list_of_assets))


    def init_clients(self):
        ### Execute trade TODO:for all users
        for user in self.user_info_list:
            user_id = user["user_id"]
            key = user["key"]
            secret = user["secret"]
            logging.info(f"{self.name} Initializing client connections {user_id}")
            self.client_conn_list.append({"user_id":user_id, "client":Client(key,secret)})

    def execute(self):
        # init and start the WebSocket
        self.bsm = BinanceSocketManager(self.client)
        self.conn_key = self.bsm.start_symbol_ticker_socket('BTCUSDT', self.__analyse_ticker_socket)
        self.bsm.start()

    def stop(self):
        # stop websocket
        self.bsm.stop_socket(self.conn_key)
        # properly terminate WebSocket
        #reactor.stop()

    def restart_socket(self):
        self.stop()
        self.execute()

    def __analyse_ticker_socket(self, msg):

        ''' define how to process incoming WebSocket messages '''
        if msg['e'] != 'error':
            timestamp = datetime.fromtimestamp(msg['E'] / 1000)
            week = timestamp.isocalendar()[1]
            hour = timestamp.hour
            minute = timestamp.minute
            new_formed_bar = None

            # the magic happens here!
            if minute != self.LAST_MINUTE:
                logging.info(f"{self.name} minute has changed...: {minute}")
                try:


                    # get timeinterval
                    STRATEGY_RUN_INTERVAL = self.strategy_list[0].get_timeinterval()
                    #currency_bars = get_finished_bars(self.client, 'BTCUSDT', STRATEGY_RUN_INTERVAL,
                    #                                  "60 minute ago UTC", "FUT").result()
                    currency_bars = self.get_public_bars(STRATEGY_RUN_INTERVAL)

                    assert currency_bars is not None
                    assert len(currency_bars) > 0
                    new_formed_bar = currency_bars.tail(1).index.values[0]
                    logging.info(f"{self.name} new_formed_bar: {new_formed_bar} last_formed_bar: {self.LAST_FORMED_BAR}")

                    # check if new bar has formed
                    new_bar = not (self.LAST_FORMED_BAR == new_formed_bar)
                    # condition to run the strategy
                    if new_bar and (self.LAST_FORMED_BAR != -1) and (self.LAST_FORMED_BAR is not None):
                        logging.info(f"{self.name} RUNNING {STRATEGY_RUN_INTERVAL} STRATEGY: {new_formed_bar}")
                        # download data needed for strategy input
                        data = DFlyDataDownload("DataDownloader", self.client, STRATEGY_RUN_INTERVAL, 7, 80,
                                                self.list_of_assets, 10).get_data()
                        assert len(data) > 0
                        # get asset infos (pricing and quantity precision)
                        asset_info = {}
                        # get current prices of assets
                        asset_info["current_price"] = data.tail(1).to_dict('records')[0]
                        # get asset quantity precision
                        asset_q_precision_df = pd.DataFrame(self.client.futures_exchange_info()["symbols"])
                        asset_info["asset_quantity_precision"] = asset_q_precision_df[asset_q_precision_df["symbol"].isin(data.columns.values)][
                            ["symbol", "quantityPrecision"]].set_index('symbol').T.to_dict('records')[0]
                        # TODO: set leverage level for symbols for all users (somewhere)
                        # get signals from strategy
                        pair_info = ()
                        for empty_strategy in self.strategy_list:
                            empty_strategy.set_data(data)
                            pair_info += (empty_strategy.get_signal(),)

                        logging.info(f"{self.name} RUNNING {STRATEGY_RUN_INTERVAL} STRATEGY for pair: {pair_info}")
                        ### Execute trade TODO:for all users
                        for client in self.client_conn_list:
                            logging.info(f"{self.name} Starting broker for {client['user_id']}")
                            DFlyBroker(f"Broker {client['user_id']}", client, pair_info, asset_info, self.mode).run_ls_trade()

                ### update time spots
                except Exception as err:
                    logging.critical(f"{self.name} in __analyse_ticker_socket Exception: {err}")

                # update
                self.LAST_MINUTE = minute
                if new_formed_bar is not None:
                    self.LAST_FORMED_BAR = new_formed_bar

        else:
            logging.critical(f"{self.name} in __analyse_ticker_socket Socket error occured. Trying to restart the socket...")
            #self.ticker_error['error'] = True
            self.restart_socket()

