import pandas as pd


def get_vwap(wide_dict):
    price = (wide_dict["adj_high"] + wide_dict["adj_low"] + wide_dict["adj_close"]) / 3
    cum_volume = wide_dict["volume"].cumsum(axis=1)
    cum_price_volume = (price * wide_dict["volume"]).cumsum(axis=1)
    wide_dict["vwap"] = cum_price_volume / cum_volume
    return wide_dict

def get_noise_area(df_sessions, wide_dict, window):
    # Open prices
    session_opens = df_sessions["adj_open"].groupby(df_sessions.index.date).first()
    session_opens.index = pd.to_datetime(session_opens.index)

    # Mean return from open price
    wide_dict["ret_from_open"] = (wide_dict["adj_close"].div(session_opens, axis=0) - 1).abs()
    wide_dict["mean_ret_from_open"] = wide_dict["ret_from_open"].rolling(window=window).mean().shift().dropna()

    # Max/min prices
    max_min = df_sessions[["adj_open", "adj_close"]]
    max_min = max_min.groupby(max_min.index.date).agg({"adj_open": "first", "adj_close": "last"})
    max_min["prev_adj_close"] = max_min["adj_close"].shift()
    max_min["max_price"] = max_min[["adj_open", "prev_adj_close"]].max(axis=1)
    max_min["min_price"] = max_min[["adj_open", "prev_adj_close"]].min(axis=1)

    # Breakout bands
    wide_dict["upper_band"] = (1 + wide_dict["mean_ret_from_open"]).mul(max_min["max_price"], axis=0)
    wide_dict["lower_band"] = (1 - wide_dict["mean_ret_from_open"]).mul(max_min["min_price"], axis=0)
    return wide_dict
