import pandas as pd
import numpy as np



# ---------- Helper functions ----------

def align_execution_times_to_intraday(df_executions, df_intraday):
    if df_executions.empty or df_intraday.empty:
        return df_executions.copy()

    def to_seconds(t):
        if pd.isnull(t): return np.nan
        if isinstance(t, pd.Timestamp): t = t.time()
        return t.hour * 3600 + t.minute * 60 + t.second

    intraday_secs = np.array([to_seconds(t) for t in df_intraday["Time"]])
    exec_secs = np.array([to_seconds(t) for t in df_executions["Time"]])

    def find_nearest(exec_sec):
        idx = np.abs(intraday_secs - exec_sec).argmin()
        return df_intraday["Time"].iloc[idx]

    df = df_executions.copy()
    df["Time"] = [find_nearest(t) for t in exec_secs]
    return df


def align_execution_times_to_30mins(df_executions, df_30min):
    if df_executions.empty or df_30min.empty:
        return df_executions.copy()

    def to_seconds(t):
        if pd.isnull(t): return np.nan
        if isinstance(t, pd.Timestamp): t = t.time()
        return t.hour * 3600 + t.minute * 60 + t.second

    intraday_secs = np.array([to_seconds(t) for t in df_30min["Date"]])
    exec_secs = np.array([to_seconds(t) for t in df_executions["Time"]])

    def find_nearest(exec_sec):
        idx = np.abs(intraday_secs - exec_sec).argmin()
        return df_30min["Date"].iloc[idx].time()

    df = df_executions.copy()
    df["Time"] = [find_nearest(t) for t in exec_secs]
    return df
