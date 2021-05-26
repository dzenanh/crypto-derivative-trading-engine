from binance.exceptions import BinanceAPIException, BinanceOrderException

from diversifly.components.globals import pd, logging, unsync, Enum, np, Client


class DFlyBroker:

    def __init__(self, name, exchange_client, pair_info, asset_info, mode):
        self.order_response_type = Client.ORDER_RESP_TYPE_RESULT
        logging.info(f"{name} - Initializing...")
        self.name = name
        self.user_id = exchange_client["user_id"]
        self.client = exchange_client["client"]
        self.pair_info = pair_info # positions
        self.asset_info = asset_info # prices
        self.mode = mode
        #self.run_ls_trade()

    # grab asset quantity precision
    def __getQuantityPrecision(self, symbol):
        #exchange_info_df = pd.DataFrame(self.client.futures_exchange_info()["symbols"])
        #return int(exchange_info_df[exchange_info_df.symbol == symbol]["quantityPrecision"].values[0])
        return int(self.asset_info["asset_quantity_precision"][symbol])

    class OpenedPositions(Enum):
        NO = 0
        YES = 1
        PAIR_ERROR = 3

    @unsync  # ADDED
    def __execute_trade_market(self, action):
        """
        Examples:
        ['BATUSDT' 'BUY' 501.2] -> buyback amount of 501.2 BATs
        ['BANDUSDT' 'SELL' '0' '35.0'] -> long or short BAND for 35.0 USDT
        """
        # get current symbol price {'symbol': 'ETHUSDT', 'price': '465.75', 'time': 1605779655268}
        symbol = action[0]
        symbol_current_price = float(self.asset_info["current_price"][symbol])

        logging.info(f"{self.name}-{action} - Submiting trade.")
        logging.info(f"{self.name}-{action} - Current asset {symbol} price: {symbol_current_price}")
        # this is response from commited trade
        order_response = None

        # check if buyback
        if len(action) == 3:
            logging.info(f"{self.name}{action} - Posting BUYBACK trade with amount: {action[2]}")
            asset_amount = round(abs(float(action[2])), self.__getQuantityPrecision(action[0]))
            try:
                if self.mode == "LIVE":
                    order_response = self.client.futures_create_order(symbol=symbol, side=action[1], type='MARKET',
                                                             quantity=str(asset_amount), reduceOnly='true', newOrderRespType=self.order_response_type)

            except BinanceAPIException as e:
                logging.ERROR(f"{self.name}-{action}{e.__class__} - API Exception : {e}")
                #TODO @dzenan: decide how to handle this

            except BinanceOrderException as e:
                logging.ERROR(f"{self.name}-{action}{e.__class__} - ORDER Exception : {e}")
                # TODO @dzenan: decide how to handle this


        # check if long/short order
        if len(action) == 4:
            leverage = 1
            marginType="CROSS"
            # make sure leverage and margin type of the coins is as defined (same)
            logging.info(f"{self.name}-{action} - Changing leverage&margin for {symbol} to:{leverage},{marginType}")
            response_leverage = self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            response_margin_type = None#self.client.futures_change_margin_type(symbol=symbol, marginType="ISOLATED")
            #binance.exceptions.BinanceAPIException: APIError(code=-4046): No need to change margin type.
            logging.info(f"{self.name}-{action} - Changing leverage&margin for {symbol}:{response_leverage},{response_margin_type}")

            money_amount = float(action[3])
            asset_amount = round(money_amount*leverage / symbol_current_price * .995, self.__getQuantityPrecision(action[0]))
            logging.info(f"{self.name}-{action} - Posting LONG/SHORT trade with amount: {action[3]} USDT")
            try:
                if self.mode == "LIVE":
                    order_response = self.client.futures_create_order(symbol=symbol, side=action[1], type='MARKET',
                                                             quantity=str(asset_amount), newOrderRespType=self.order_response_type)
                else:
                    order_response = {'orderId': 4492369393, 'symbol': 'BANDUSDT', 'status': 'FILLED', 'clientOrderId': 'bRhFSRYJMXhWKubCxC3vti', 'price': '0', 'avgPrice': '6.62690', 'origQty': '1.5', 'executedQty': '1.5', 'cumQty': '1.5', 'cumQuote': '9.94035', 'timeInForce': 'GTC', 'type': 'MARKET', 'reduceOnly': True, 'closePosition': False, 'side': 'SELL', 'positionSide': 'BOTH', 'stopPrice': '0', 'workingType': 'CONTRACT_PRICE', 'priceProtect': False, 'origType': 'MARKET', 'updateTime': 1608014102308}

            except BinanceAPIException as e:
                logging.ERROR(f"{self.name}-{action}{e.__class__} - API Exception : {e}")
                # TODO @dzenan: decide how to handle this

            except BinanceOrderException as e:
                logging.ERROR(f"{self.name}-{action}{e.__class__} - ORDER Exception : {e}")
                # TODO @dzenan: decide how to handle this

        # client.futures_create_order(symbol=self.symbol, side='BUY', type='MARKET', quantity=1, reduceOnly='true')
        logging.info(f"{self.name}-{action} - Trade successful. Order Response: {order_response}")
        return order_response

    @unsync  # ADDED
    def __run(self, action):
        """
        Run the bot cycle once now for a markets.

        1. Reads market data from an API
        2. Reads data from a database
        3. (once both are available) Calculates some logic to decide on a trade
        4. (if logic says we should trade) Executes a trade via an API
        5. (when trade is completed) updates the database

        Returns - action result of this cycle
        """

        logging.critical(f"{self.name}-{action} - Starting trade execution.")

        ### TODO @Manuel: implement these things
        # database_data = get_database_data(action)

        if action is not None:
            trade_response = self.__execute_trade_market(action).result()  # ADDED .result() to await result before moving on
        else:
            trade_response = None
            logging.info(f"{self.name}-{action} - No trade to post.")

        # TODO @Manuel: save the result of a trade (trade_response) exchange response
        # updates = update_database(
        #    self.pair_info
        #    self.asset_info
        #    trade response
        # )#.result()  # ADDED .result() to await before moving on

        logging.critical(f"{self.name}-{action} - Finished trade execution.")
        return action

    '''
    pair -> ({"asset1":"DEFIUSDT","asset2":"BANDUSDT","position":-1, "amount":50},)
    '''

    @unsync
    def __futures_get_position_df(self, pair):
        position_inf = pd.DataFrame(self.client.futures_position_information())
        position_inf[["positionAmt", "entryPrice", "markPrice", "unRealizedProfit", "leverage"]] = position_inf[
            ["positionAmt", "entryPrice", "markPrice", "unRealizedProfit", "leverage"]].apply(pd.to_numeric)
        position_inf = position_inf[position_inf.positionAmt != 0]  #
        # check if not empty
        if len(position_inf) > 0:
            position_inf["amount"] = (position_inf.positionAmt * position_inf.entryPrice)
            position_inf["currentPosition"] = position_inf["positionAmt"].apply(lambda x: 'long' if x > 0 else 'short')
            position_inf["buybackPosition"] = position_inf["currentPosition"].apply(
                lambda x: 'SELL' if x == "long" else 'BUY')
            position_inf["buybackAmt"] = position_inf["positionAmt"].apply(lambda x: -x)
        return position_inf[(position_inf.symbol == pair["asset1"]) | (position_inf.symbol == pair["asset2"])]

    @unsync
    def __pair_execution_logic(self, pair):
        logging.info(f"{self.name}-{pair}__pair_execution_logic - Starting")
        try:
            opened_positions = self.OpenedPositions.NO

            # check if suficient funds available
            accountFundsAvailable = float(self.client.futures_account_balance()[0]["withdrawAvailable"])
            if pair["moneyAmount"] > accountFundsAvailable and pair["position"] != 0:
                logging.info(
                    f"{self.name}-{pair} - No enough funds ({accountFundsAvailable} USDT) for this transaction. Exiting...")
                # TODO @dzenan: but check if already in position
                return

            # TODO: check if both assets tradable
            # client.get_symbol_info(symbol="BANDUSDT")
            # {'symbol': 'BANDUSDT',
            # 'status': 'TRADING',
            # 'baseAsset': 'BAND',

            # current position DF
            pos_df = self.__futures_get_position_df(pair).result()
            logging.info(f"{self.name}-{pair} Current number of positions: {len(pos_df)}. This may cause trouble...")
            ### check if one pair positioned and other one not -> raise error
            if (len(pos_df[pos_df.symbol == pair["asset1"]]) != len(pos_df[pos_df.symbol == pair["asset2"]])):
                logging.info(f"{self.name}-{pair} - Pair mismatch. Exiting...")
                return
            # check if none assets in position
            if ((len(pos_df[pos_df.symbol == pair["asset1"]]) == 0) & (
                    len(pos_df[pos_df.symbol == pair["asset2"]]) == 0)):
                logging.info(f"{self.name}-{pair} - No Positions for given pairs.")
                opened_positions = self.OpenedPositions.NO
            # check if both assets in position
            elif ((len(pos_df[pos_df.symbol == pair["asset1"]]) == 1) & (
                    len(pos_df[pos_df.symbol == pair["asset2"]]) == 1)):
                logging.info(f"{self.name}-{pair} - Given pairs in position. Can buyback...")
                opened_positions = self.OpenedPositions.YES
                # check if long-short without exiting positions first
                if ((pair["position"] == 1) | (pair["position"] == -1)):
                    logging.info(f"{self.name}-{pair} - Only Buyback posible. Exiting...")
                    return

            # buyback
            if opened_positions == self.OpenedPositions.YES:
                if pair["position"] == 0:
                    # TODO find short and buyback
                    # Binance.futures_create_order(symbol=self.symbol, side='BUY', type='MARKET', quantity=1, reduceOnly='true')
                    buyback_array = pos_df[["symbol", "buybackPosition", "buybackAmt"]].values
                    logging.info(f"{self.name}-{pair} Buyback positions: {buyback_array}")
                    return buyback_array

            # take position
            if opened_positions == self.OpenedPositions.NO:
                moneyAmount = int(pair["moneyAmount"]) / 2

                # check if
                if pair["position"] == 0:
                    logging.info(f"{self.name}-{pair} - Buyback not possible! No positions!")
                    return

                if pair["position"] == 1:
                    position = np.array(
                        [[pair["asset1"], "BUY", "0", moneyAmount], [pair["asset2"], "SELL", "0", moneyAmount]])
                    logging.info(f"{self.name}-{pair} long asset1, short asset2: {position}")
                    return position
                if pair["position"] == -1:
                    position = np.array(
                        [[pair["asset1"], "SELL", "0", moneyAmount], [pair["asset2"], "BUY", "0", moneyAmount]])
                    logging.info(f"{self.name}-{pair} short asset1, long asset2: {position}")
                    return position
        except Exception as err:
            logging.critical(f"{self.name}-{pair} __pair_execution_logic Exception: {err}")
            raise Exception(f"{self.name}-{__class__} Sorry, some shit went down. Check logs...")

    @unsync
    def run_ls_trade(self):
        '''
        Example 1:
        long asset1, short asset 2:
        pair_info = ({"asset1":"DEFIUSDT","asset2":"BANDUSDT","position":1, "moneyAmount":70},)
        Example 2: short asset1, long asset 2:
        pair_info = ({"asset1":"DEFIUSDT","asset2":"BANDUSDT","position":-1, "moneyAmount":70},)
        Example 3: exit positions for given assets:
        pair_info = ({"asset1":"DEFIUSDT","asset2":"BANDUSDT","position":0, "moneyAmount":70},)

        position order: 1 -> 0 -> -1 or other way around
        '''
        for pair in self.pair_info:
            try:
                #print(pair)
                logging.info(f"{self.name} - pair: {pair}")
                pair_info = self.__pair_execution_logic(pair).result()
                #print(pair_info)
                logging.info(f"{self.name} - pair_info: {pair_info}")
                if pair_info is not None:
                    for asset_info in pair_info:
                        # test_method_for_asset_exec(asset_info)
                        self.__run(asset_info)
                else:
                    logging.critical(f"{self.name}-{pair} - pair_info is NONE. Check logs for details...")
                    # TODO: raise exception
            except Exception as err:
                logging.critical(f"Exception: {err}")