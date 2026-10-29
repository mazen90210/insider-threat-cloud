"""Log parsing and risk scoring engine (Pandas)."""
import re
import pandas as pd

LINE_RE = re.compile(
    r"^(?P<ts>\w{3}\s+\d+\s[\d:]{8})\s(?P<host>\S+)\s(?P<proc>[^:]+):\s"
    r"user=(?P<user>\S+)\sevent=(?P<event>\S+)\ssrc=(?P<src>\S+)$"
)

# Risk points per event type (adjust to match the original ITI rules)
RISK_RULES = {
    "login_success": 0,
    "file_access": 1,
    "login_failed": 5,
    "after_hours_login": 10,
    "usb_insert": 15,
    "large_download": 20,
    "sensitive_file_access": 25,
    "privilege_escalation": 40,
}

LEVELS = [(0, "Low"), (1200, "Medium"), (2000, "High"), (3000, "Critical")]


def parse_logs(lines):
    rows = [m.groupdict() for m in (LINE_RE.match(l) for l in lines) if m]
    return pd.DataFrame(rows, columns=["ts", "host", "proc", "user", "event", "src"])


def score(df):
    df = df.copy()
    df["points"] = df["event"].map(RISK_RULES).fillna(0).astype(int)
    return df


def level_for(total):
    label = LEVELS[0][1]
    for threshold, name in LEVELS:
        if total >= threshold:
            label = name
    return label


def user_summary(df):
    scored = score(df)
    agg = (
        scored.groupby("user")
        .agg(events=("event", "count"), risk_score=("points", "sum"))
        .reset_index()
        .sort_values("risk_score", ascending=False)
    )
    agg["level"] = agg["risk_score"].apply(level_for)
    return agg


def event_breakdown(df):
    return df.groupby("event").size().sort_values(ascending=False)
