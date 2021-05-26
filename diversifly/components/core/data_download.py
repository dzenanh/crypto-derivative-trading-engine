from diversifly.components.globals import pd,logging, unsync, time, get_finished_bars, timedelta, datetime
#
# Class DFlyDataDownload
#
class DFlyDataDownload:
    """
    @Description
    TODO

    @Params
    name : factor name
    """

    def __init__(self, name, exchange_client, timeframe, nr_days, limit, asset_list, batch_size):
        logging.info(f"{name} - Initializing...")
        self.name = name
        self.client = exchange_client
        self.timeframe = timeframe
        self.asset_list = asset_list
        self.nr_days_from = nr_days
        self.limit = limit
        self.dataframe = None
        self.batch_size = batch_size
        # download data
        self.__download_data()

    # just for representation
    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def show_data(self):
        print(self.dataframe.tail(5))

    def get_data(self):
        return self.dataframe

    @unsync  # this runs in parallel
    def __fetch_data_for_asset(self, asset, interval, since_days, limit):
        logging.info(f"{self.name} fetch_ohlc_data - Starting download for: {asset}, timeframe:{interval}")

        start_date = datetime.now() - timedelta(since_days)
        timestamp = str(start_date.timestamp() * 1000)
        df_currency_bars = get_finished_bars(self.client, asset, interval, None, "FUT").result()
        df_currency_bars.rename(columns={'close': asset}, inplace=True)

        logging.info(f"{self.name} fetch_ohlc_data - Finished download for: {asset}, timeframe:{interval}")
        return df_currency_bars[[asset]]

    def __fetch_data_for_assets(self, list_of_assets, interval, since_days, limit):
        '''
        @Params
        TODO
        (asset, interval, since_days, limit)
        ("BTCUSDT", "1h", 10, 20)
        '''
        logging.critical(f"{self.name} Starting download...")

        start = time.time()
        # TODO: run in batch of 10
        task_queue = []

        df_asset_close_global = pd.DataFrame()
        # do it in baches (max 10 pro batch)
        for i in range(0, len(list_of_assets), self.batch_size):
            # process_list(my_list[i:i+100])
            tasks = [self.__fetch_data_for_asset(asset, interval, since_days, limit) for asset in
                     list_of_assets[i:i + self.batch_size]]
            # call multiple asynchronously
            task_queue = [task.result() for task in tasks]
            df_asset_close = pd.concat(task_queue, axis=1).apply(pd.to_numeric)
            df_asset_close_global = pd.concat([df_asset_close_global, df_asset_close], axis=1).apply(pd.to_numeric)
            # df_pricing = df_pricing+task_queue
            logging.critical(f"{self.name} __fetch_data_for_assets - Finished batch {i}")

        # select finished bars
        logging.critical(f"{self.name} __fetch_data_for_assets - Finished everything. Took {time.time() - start} seconds.")
        # print(df_asset_close_global.tail(5))
        return df_asset_close_global

    def __download_data(self):
        logging.info(f"{self.name} - Downloading data...")
        self.dataframe = self.__fetch_data_for_assets(self.asset_list, self.timeframe, self.nr_days_from, self.limit)
        self.dataframe = self.dataframe.loc[:, ~self.dataframe.columns.duplicated()]
        self.dataframe = self.dataframe.dropna()
        # get_data
