from talib import STDDEV, EMA
from diversifly.components.globals import Client
from diversifly.components.globals import np, logging

class DFlyMarketNeutralStrat4:

    def __init__(self, name, data, moneyAmount):
        logging.info(f"{__class__} - Initializing DFlyMarketNeutralStrat:{name}")
        self.name = name
        self.moneyAmount = moneyAmount
        self.asset1 = "LINKUSDT"
        self.asset2 = "BANDUSDT"
        self.timeinterval = Client.KLINE_INTERVAL_15MINUTE
        if data is not None:
            self.data = data[[self.asset1, self.asset2]].copy()

    def set_data(self, data):
        self.data = data[[self.asset1, self.asset2]].copy()

    def get_assets(self):
        return [self.asset1, self.asset2]

    def get_timeinterval(self):
        return self.timeinterval


    def get_signal(self):
        self.signal_df = self.__calculate_signals()
        return self.signal_df.tail(1)[["asset1", "asset2", "position", "moneyAmount"]].to_dict('records')[0]

    def get_signal_df(self):
        return self.signal_df


    def __calculate_signals(self):
        # Create a dataframe df and store the closing price of BTC/USD and XRM/USD in a column name BTC and XRM respectively. 
        df = self.data#.copy()
        asset1, asset2 = self.asset1, self.asset2
        df["asset1"], df["asset2"], df["moneyAmount"] = asset1, asset2, self.moneyAmount

        #print(df.head())

        #leverage = 10
        std = 1.5
        corr_coef = 0.3
        ma_length = 30
        roll_correlation_len = 5
        std_length = 80
        volatility = 0.01

        df["corr"] = df[asset1].rolling(roll_correlation_len).corr(df[asset2])
        # Calculate the spread
        df['spread'] = df[asset1] / df[asset2]
        # spread volatility
        df["volatility"] = STDDEV(df["spread"].pct_change(), 8)

        # Calculte Moving Average
        df['moving_average'] = EMA(df.spread, ma_length)  # df.spread.rolling(ma_length).mean()#+0.5
        # Calculate Moving Standard deviation
        df['moving_std_dev'] = df.spread.rolling(std_length).std()
        # Calcuate Upper band, middle band and lower band

        df['upper_band'] = df.moving_average + std * df.moving_std_dev
        df['middle_band'] = df.moving_average
        df['lower_band'] = df.moving_average - std * df.moving_std_dev

        # additional shit
        df["spread_to_mid"] = df[["spread", "middle_band"]].pct_change(axis=1)["middle_band"]

        # Long Entry
        df['long_position'] = np.where(
            ((df.spread < df.lower_band) & (df["corr"] > corr_coef) & (df["volatility"] > volatility)), 1, 0)
        # Long Exit
        df['long_position'] = np.where((df.spread >= df.middle_band) | (df["corr"] < corr_coef), 0, df.long_position)
        # Short Entry
        df['short_position'] = np.where(
            ((df.spread > df.upper_band) & (df["corr"] > corr_coef) & (df["volatility"] > volatility)), -1, 0)  #
        # Short exit
        df['short_position'] = np.where((df.spread <= df.middle_band) | (df["corr"] < corr_coef), 0, df.short_position)
        # Fill NaN values
        df = df.fillna(method='ffill')
        # Combine the positions
        df['position'] = df.long_position + df.short_position
        return df