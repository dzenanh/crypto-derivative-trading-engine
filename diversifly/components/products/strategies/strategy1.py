# Import statsmodels package
import statsmodels.api as sm
import statsmodels.tsa.stattools as ts
from diversifly.components.globals import np, logging

class DFlyMarketNeutralStrat:

    def __init__(self, name, data, asset_list, moneyAmount):
        logging.info(f"{__class__} - Initializing DFlyMarketNeutralStrat:{name}")
        self.name = name
        self.data = data
        self.asset_list = asset_list
        self.moneyAmount = moneyAmount
        self.signal_df = self.__calculate_signals()

    def get_signal(self):
        return self.signal_df.tail(1)[["asset1", "asset2", "position", "moneyAmount"]].to_dict('records')[0]

    def get_signal_df(self):
        return self.signal_df

    def __calculate_signals(self):
        # Create a dataframe df and store the closing price of BTC/USD and XRM/USD in a column name BTC and XRM respectively. 
        df = self.data.copy()
        asset1, asset2 = self.asset_list[0], self.asset_list[1]
        df["asset1"], df["asset2"], df["moneyAmount"] = asset1, asset2, self.moneyAmount
        # Create and fit the linear model
        length = 90
        reg = sm.OLS(df[asset1].iloc[:length], df[asset2].iloc[:length]).fit()
        # Extract the parameter
        hedge_ratio = reg.params[0]
        # Calculate the spread
        df['spread'] = df[asset1] - hedge_ratio * df[asset2]
        # Check cointegration using the adfuller function
        coint = ts.adfuller(df.spread.iloc[:90])
        # print(coint)
        # Calculte Moving Average 
        length = 10
        df['moving_average'] = df.spread.rolling(length).mean()
        # Calculate Moving Standard deviation
        df['moving_std_dev'] = df.spread.rolling(length).std()
        # Calcuate Upper band, middle band and lower band
        std = 0.4
        df['upper_band'] = df.moving_average + std * df.moving_std_dev
        df['middle_band'] = df.moving_average
        df['lower_band'] = df.moving_average - std * df.moving_std_dev

        # Long Entry
        df['long_position'] = np.where((df.spread < df.lower_band), 1, 0)
        # Long Exit
        df['long_position'] = np.where(df.spread >= df.middle_band, 0, df.long_position)
        # Short Entry
        df['short_position'] = np.where((df.spread > df.upper_band), -1, 0)
        # Short exit
        df['short_position'] = np.where(df.spread <= df.middle_band, 0, df.short_position)
        # Fill NaN values
        df = df.fillna(method='ffill')
        # Combine the positions
        df['position'] = df.long_position + df.short_position
        return df