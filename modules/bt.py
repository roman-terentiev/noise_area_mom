import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def get_df_day(date, wide_dict):
    df = pd.DataFrame()
    df["open"] = wide_dict["open"].loc[date]
    df["close"] = wide_dict["close"].loc[date]
    df["adj_close"] = wide_dict["adj_close"].loc[date]
    df["vwap"] = wide_dict["vwap"].loc[date]
    df["upper_band"] = wide_dict["upper_band"].loc[date]
    df["lower_band"] = wide_dict["lower_band"].loc[date]   
    return df


def get_trades_day(df, contract_mult, comm_usd, spread_usd, slipp_rate, toll_rate):
    # Trade every 30 minutes
    minutes = df.index.map(lambda t: t.minute)
    signal_rows = df.loc[minutes % 30 == 29].iloc[:-1]
    trade_rows  = df.loc[minutes % 30 == 0].iloc[1:]
    if len(signal_rows) != len(trade_rows):
        trade_rows = trade_rows.iloc[:len(signal_rows)]

    round_trip_cost = comm_usd * 2 + spread_usd

    trades = []
    trade = None
    
    for i in range(len(trade_rows)):
        signal_row = signal_rows.iloc[i]
        trade_row = trade_rows.iloc[i]

        if trade is None:
            # Entry long
            if signal_row["adj_close"] > signal_row["upper_band"]:
                trade = {
                    "trade_type": "long",
                    "start_time": trade_row.name,
                    "end_time": None,
                    "entry_price": trade_row["open"] * (1 + slipp_rate),
                }
  
            # Entry short
            elif signal_row["adj_close"] < signal_row["lower_band"]:
                trade = {
                    "trade_type": "short",
                    "start_time": trade_row.name,
                    "end_time": None,
                    "entry_price": trade_row["open"] * (1 - slipp_rate),
                }
        else:
            # Exit long
            if trade["trade_type"] == "long":
                is_below_upper = signal_row["adj_close"] < signal_row["upper_band"] * (1 + toll_rate)
                is_below_vwap = signal_row["adj_close"] < signal_row["vwap"] * (1 + toll_rate)
                if is_below_upper or is_below_vwap:
                    trade["end_time"] = trade_row.name
                    trade["exit_price"] = trade_row["open"] * (1 - slipp_rate)
                    trade["round_trip_cost"] = round_trip_cost
                    trade["pnl"] = (trade["exit_price"] - trade["entry_price"]) * contract_mult - round_trip_cost
                    trade["ret"] = trade["pnl"] / (trade["entry_price"] * contract_mult)
                    
                    if is_below_upper:
                        trade["exit_reason"] = "is_below_upper"
                    elif is_below_vwap:
                        trade["exit_reason"] = "is_below_vwap"

                    trades.append(trade)

                    # Reverse when the signal has crossed the opposite band
                    if signal_row["adj_close"] < signal_row["lower_band"]:
                        trade = {
                            "trade_type": "short",
                            "start_time": trade_row.name,
                            "end_time": None,
                            "entry_price": trade_row["open"] * (1 - slipp_rate),
                        }
                    else:
                        trade = None

            # Exit short
            elif trade["trade_type"] == "short":
                is_above_lower = signal_row["adj_close"] > signal_row["lower_band"] * (1 - toll_rate)
                is_above_vwap = signal_row["adj_close"] > signal_row["vwap"] * (1 - toll_rate)
                if is_above_lower or is_above_vwap:
                    trade["end_time"] = trade_row.name
                    trade["exit_price"] = trade_row["open"] * (1 + slipp_rate)
                    trade["round_trip_cost"] = round_trip_cost
                    trade["pnl"] = (trade["entry_price"] - trade["exit_price"]) * contract_mult - round_trip_cost
                    trade["ret"] = trade["pnl"] / (trade["entry_price"] * contract_mult)
                    
                    if is_above_lower:
                        trade["exit_reason"] = "is_above_lower"
                    elif is_above_vwap:
                        trade["exit_reason"] = "is_above_vwap"

                    trades.append(trade)

                    # Reverse when the signal has crossed the opposite band
                    if signal_row["adj_close"] > signal_row["upper_band"]:
                        trade = {
                            "trade_type": "long",
                            "start_time": trade_row.name,
                            "end_time": None,
                            "entry_price": trade_row["open"] * (1 + slipp_rate),
                        }
                    else:
                        trade = None
                    
    if trade is not None and trade["end_time"] is None:
        eod_row = df.iloc[-1]
        trade["end_time"] = eod_row.name
        
        # Exit long
        if trade["trade_type"] == "long":
            trade["exit_price"] = eod_row["close"] * (1 - slipp_rate)
            trade["round_trip_cost"] = round_trip_cost
            trade["pnl"] = (trade["exit_price"] - trade["entry_price"]) * contract_mult - round_trip_cost
            trade["ret"] = trade["pnl"] / (trade["entry_price"] * contract_mult)

        # Exit short
        elif trade["trade_type"] == "short":
            trade["exit_price"] = eod_row["close"] * (1 + slipp_rate)
            trade["round_trip_cost"] = round_trip_cost
            trade["pnl"] = (trade["entry_price"] - trade["exit_price"]) * contract_mult - round_trip_cost
            trade["ret"] = trade["pnl"] / (trade["entry_price"] * contract_mult)

        if trade.get("exit_reason") is None:
            trade["exit_reason"] = "eod"
            
        trades.append(trade)
        
    return trades


def get_trades(calendar, wide_dict, contract_mult, comm_usd, spread_usd, slipp_rate, toll_rate):
    trades = []
    for date in calendar:
        df = get_df_day(date, wide_dict)
        trades_day = get_trades_day(
            df, 
            contract_mult=contract_mult, 
            comm_usd=comm_usd, 
            spread_usd=spread_usd, 
            slipp_rate=slipp_rate, 
            toll_rate=toll_rate
        )
        
        if len(trades_day) > 0:
            for trade in trades_day:
                for column in ("start_time", "end_time"):
                    trade[column] = pd.Timestamp.combine(date, trade[column])
                trades.append(trade)

    trades = pd.DataFrame(trades)
    if trades.empty:
        return trades

    trades.index = pd.to_datetime(trades["start_time"].dt.date)
    trades.index.name = "date"
    trades["duration"] = (trades["end_time"] - trades["start_time"]).dt.total_seconds() / 60
    return trades


def get_sized_trades_equity(
    df,
    trades,
    calendar, 
    init_balance, 
    daily_vol_span, 
    daily_target_vol, 
    max_leverage, 
    contract_mult, 
    save_dir, 
    ):
    trades = trades.copy()
    trades["daily_vol"] = np.nan
    trades["vol_rate"] = np.nan
    trades["num_contracts"] = np.nan

    balance = init_balance
    equity = pd.Series(init_balance, index=calendar, name="equity", dtype=float)
    daily_ret = df["adj_close"].resample("D").last().pct_change(fill_method=None).tz_convert(None)

    for date in calendar:
        if not trades.empty and date in trades.index:
            for i in np.flatnonzero(trades.index == date):
                trade = trades.iloc[i]
                
                daily_vol = daily_ret.loc[daily_ret.index < date].tail(daily_vol_span).std()
                vol_rate = min(max_leverage, daily_target_vol / daily_vol) if daily_vol > 0 else max_leverage
                num_contracts = int(round(balance * vol_rate / (trade["entry_price"] * contract_mult), 0))
                balance += num_contracts * trade["pnl"]

                trades.iloc[i, trades.columns.get_loc("daily_vol")] = daily_vol
                trades.iloc[i, trades.columns.get_loc("vol_rate")] = vol_rate
                trades.iloc[i, trades.columns.get_loc("num_contracts")] = num_contracts

        equity.loc[date] = balance

    fig, ax = plt.subplots(figsize=(12, 6))
    equity.plot(ax=ax)
    ax.set_title("Equity Curve")
    ax.set_xlabel("Time")
    ax.set_ylabel("Equity")
    fig.savefig(save_dir / "equity.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    trades.to_csv(save_dir / "trades.csv")
    equity.to_csv(save_dir / "equity.csv")
    return equity
