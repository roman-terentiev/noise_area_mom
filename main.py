import pandas as pd

from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys

from modules.prep import back_adj, get_sessions, to_wide_frames
from modules.feats import get_vwap, get_noise_area
from modules.bt import get_trades, get_sized_trades_equity
from modules.stats import get_stats, get_rets_heat
from config import *


if __name__ == "__main__":
    utc_time = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    runs_dir = Path("runs")
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_dir = runs_dir / utc_time
    run_dir.mkdir(parents=True, exist_ok=True)

    in_dir = run_dir / "in"
    out_dir = run_dir / "out"
    in_dir.mkdir()
    out_dir.mkdir()

    shutil.copy2("config.py", in_dir / "config.py")
    with (in_dir / "requirements.txt").open("w") as file:
        subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=file, check=True)

    df = pd.read_parquet(DATA_PATH)
    df.describe().round(2).to_csv(out_dir / "describe_data.csv")

    df = back_adj(df, save_dir=out_dir)
    df.describe().round(2).to_csv(out_dir / "describe_back_adj.csv")

    df_sessions = get_sessions(
        df, 
        time_start=SESSION_TIME_START, 
        time_end=SESSION_TIME_END
    )
    wide_dict = to_wide_frames(df_sessions)
    wide_dict = get_vwap(wide_dict)
    wide_dict = get_noise_area(
        df_sessions, 
        wide_dict=wide_dict, 
        window=NOISE_AREA_WINDOW
    )
    pd.concat([
        frame.stack().rename(name) for name, frame in wide_dict.items()
    ], axis=1).describe().round(2).to_csv(out_dir / "describe_wide_dict.csv")

    calendar = wide_dict["mean_ret_from_open"].index.unique()
    trades = get_trades(
        calendar, 
        wide_dict=wide_dict, 
        contract_mult=CONTRACT_MULT, 
        comm_usd=COMM_USD, 
        spread_usd=SPREAD_USD, 
        slipp_rate=SLIPP_RATE, 
        toll_rate=TOLL_RATE
    )
    equity = get_sized_trades_equity(
        df,
        trades=trades,
        calendar=calendar, 
        init_balance=INIT_BALANCE, 
        daily_vol_span=DAILY_VOL_SPAN, 
        daily_target_vol=DAILY_TARGET_VOL, 
        max_leverage=MAX_LEVERAGE, 
        contract_mult=CONTRACT_MULT,
        save_dir=out_dir,
    )

    get_stats(
        equity,
        num_periods=STATS_NUM_PERIODS, 
        save_dir=out_dir,
    )
    get_rets_heat(equity, save_dir=out_dir)
