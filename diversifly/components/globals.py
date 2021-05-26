import time as time
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import itertools as itertools

from unsync import unsync
from enum import Enum
import logging as logging
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

# python binance
from binance.client import Client

# sockets
from binance.websockets import BinanceSocketManager
from twisted.internet import reactor


def utc_to_local(utc_dt):
    LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=LOCAL_TIMEZONE)


def is_finished_bar(local_timezone_dt):
    LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo
    return 1 if local_timezone_dt < datetime.now(LOCAL_TIMEZONE) else 0


# TODO: this should be paralelized
@unsync
def get_finished_bars(client, symbol, STRATEGY_RUN_INTERVAL, since, MARKET):
    if MARKET == "SPOT":
        currency_bars = pd.DataFrame(client.get_historical_klines(symbol, STRATEGY_RUN_INTERVAL, since),
                                     columns=['date', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'QAV',
                                              'numberOfTrades', 'd1', 'd2', 'd3'])  # .tail(1)
    elif MARKET == "FUT":
        currency_bars = pd.DataFrame(client.futures_klines(symbol=symbol, interval=STRATEGY_RUN_INTERVAL),
                                     columns=['date', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'QAV',
                                              'numberOfTrades', 'd1', 'd2', 'd3'])

    currency_bars.closeTime = pd.to_datetime(currency_bars.closeTime, unit='ms')
    currency_bars.date = pd.to_datetime(currency_bars.date, unit='ms')
    currency_bars["closeTimeLocal"] = currency_bars.closeTime.apply(utc_to_local)  # closeTime, unit='ms')
    currency_bars["finishedBar"] = currency_bars.closeTimeLocal.apply(is_finished_bar)
    currency_bars = currency_bars[currency_bars.finishedBar == 1]
    currency_bars.index = currency_bars.date
    return currency_bars


@unsync
def get_finished_bars2(client, symbol, STRATEGY_RUN_INTERVAL, since, MARKET, limit):
    def is_finished_bar(local_timezone_dt):
        LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo
        return 1 if local_timezone_dt < datetime.now(LOCAL_TIMEZONE) else 0

    try:
        if MARKET == "S":
            currency_bars = pd.DataFrame(client.get_historical_klines(symbol, STRATEGY_RUN_INTERVAL, since),
                                         columns=['date', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'QAV',
                                                  'numberOfTrades', 'd1', 'd2', 'd3'])
        elif MARKET == "F":
            currency_bars = pd.DataFrame(
                client.futures_klines(symbol=symbol, interval=STRATEGY_RUN_INTERVAL, limit=limit),
                columns=['date', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'QAV',
                         'numberOfTrades', 'd1', 'd2', 'd3'])

        currency_bars.date = pd.to_datetime(currency_bars.date, unit='ms')
        currency_bars.index = currency_bars.date
        return currency_bars
    except Exception as e:
        logging.info(f"get_finished_bars - Exception: {e}")
        return None