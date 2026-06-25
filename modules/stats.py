import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def get_stats(equity, num_periods, save_dir):
    num_years = (equity.index[-1] - equity.index[0]).days / 365.25
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / num_years) - 1

    rets = equity.pct_change(fill_method=None).fillna(0)
    ann_mean = rets.mean() * num_periods
    ann_vol = rets.std() * np.sqrt(num_periods)
    dd = equity / equity.cummax() - 1
    max_dd = dd.min()
    ann_sharpe = ann_mean / ann_vol if ann_vol != 0 else np.nan
    skew = rets.skew()

    stats = pd.Series({
        "CAGR [%]": cagr * 100,
        "Volatility (Ann.) [%]": ann_vol * 100,
        "Max Drawdown [%]": max_dd * 100,
        "Sharpe Ratio (Ann.)": ann_sharpe,
        "Skew": skew,
    }).round(2).to_frame("value")
    stats.index.name = "stat"

    stats.to_csv(save_dir / "stats.csv")


def get_rets_heat(equity, save_dir):
    rets = equity.pct_change(fill_method=None).fillna(0)
    mon_rets = (1 + rets).resample("ME").prod() - 1
    mon_rets = mon_rets.to_frame("mon_rets")
    mon_rets["year"] = mon_rets.index.year
    mon_rets["month"] = mon_rets.index.month

    tab = mon_rets.pivot(index="year", columns="month", values="mon_rets")

    tab["Annual Return [%]"] = (1 + mon_rets["mon_rets"]).groupby(mon_rets["year"]).prod() - 1
    year_equity = (1 + mon_rets["mon_rets"]).groupby(mon_rets["year"]).cumprod()
    dd = year_equity / year_equity.groupby(mon_rets["year"]).cummax() - 1
    tab["Max Drawdown [%]"] = dd.groupby(mon_rets["year"]).min()
    tab["Sharpe Ratio (Ann.)"] = (
        mon_rets["mon_rets"].groupby(mon_rets["year"]).mean()
        / mon_rets["mon_rets"].groupby(mon_rets["year"]).std()
    ) * np.sqrt(12)

    tab = tab.rename(columns={
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }).sort_index(ascending=False)

    tab_display = tab * 100
    tab_display["Sharpe Ratio (Ann.)"] = tab["Sharpe Ratio (Ann.)"]

    fig, ax = plt.subplots(figsize=(14, 6))
    sns.heatmap(
        tab_display,
        annot=True,
        fmt=".2f",
        cmap="RdYlGn",
        center=0,
        vmin=-15,
        vmax=15,
        cbar=False,
        linewidths=0.5,
        linecolor="white",
        ax=ax,
    )
    ax.set_title("Monthly Returns")
    ax.set_xlabel("Month")
    ax.set_ylabel("Year")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    fig.savefig(save_dir / "rets_heat.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
