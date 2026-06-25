import pandas as pd
import matplotlib.pyplot as plt


def get_sessions(df, time_start, time_end):
    df = df.between_time(time_start, time_end, inclusive="left")
    return df


def to_wide_frames(df):
    df = df.copy()
    df["date"] = df.index.date
    df["time"] = df.index.time

    wide_dict = {}
    for col in ["open", "close", "adj_open", "adj_high", "adj_low", "adj_close"]:
        df_wide = pd.pivot(df, values=col, index="date", columns="time").ffill(axis=1)
        df_wide.index = pd.to_datetime(df_wide.index)
        wide_dict[col] = df_wide

    volume = pd.pivot(df, values="volume", index="date", columns="time").fillna(0)
    volume.index = pd.to_datetime(volume.index)
    wide_dict["volume"] = volume
    return wide_dict


def back_adj(df, save_dir):
    df = df.sort_index().copy()
    roll_ids = df["instrument_id"]
    roll_mask = roll_ids.notna() & roll_ids.shift().notna() & roll_ids.ne(roll_ids.shift())
    roll_gaps = df["open"].astype(float).where(roll_mask) - df["close"].astype(float).shift().where(roll_mask)
    adj = roll_gaps.fillna(0.0)[::-1].cumsum()[::-1].shift(-1).fillna(0.0)

    price_cols = ["open", "high", "low", "close"]
    for col in price_cols:
        df[f"adj_{col}"] = df[col].astype(float) + adj

    fig, ax = plt.subplots(figsize=(12, 6))
    df[["close", "adj_close"]].plot(ax=ax)
    ax.set_title("Back-Adjustment")
    ax.set_xlabel("Time")
    ax.set_ylabel("Price")
    fig.savefig(save_dir / "back_adj.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    return df[["open", "close", "adj_open", "adj_high", "adj_low", "adj_close", "volume"]]
