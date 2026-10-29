"""Synthetic syslog-style event generator (simulates rsyslog output from the lab VMs)."""
import random
from datetime import datetime, timedelta

USERS = {
    "mazen": {"host": "192.168.42.130", "proc": "winlogon"},
    "Finance_manager": {"host": "192.168.42.131", "proc": "winlogon"},
    "Developer": {"host": "192.168.42.133", "proc": "sshd"},
    "Guest": {"host": "192.168.42.133", "proc": "sshd"},
}

# Relative event frequencies per user (higher = more likely)
BASE = {
    "login_success": 50, "login_failed": 8, "file_access": 25,
    "sensitive_file_access": 3, "privilege_escalation": 1,
    "usb_insert": 2, "large_download": 2, "after_hours_login": 2,
}
OVERRIDES = {
    "Guest": {"login_failed": 25, "privilege_escalation": 8, "sensitive_file_access": 10,
              "usb_insert": 8, "after_hours_login": 10},
    "Developer": {"privilege_escalation": 5, "large_download": 6},
    "Finance_manager": {"sensitive_file_access": 12, "large_download": 5},
}


def generate_logs(n=500, seed=None):
    rng = random.Random(seed)
    now = datetime.now()
    lines = []
    for _ in range(n):
        user = rng.choice(list(USERS))
        weights = {**BASE, **OVERRIDES.get(user, {})}
        event = rng.choices(list(weights), weights=list(weights.values()))[0]
        ts = now - timedelta(seconds=rng.randint(0, 24 * 3600))
        if event == "after_hours_login":
            ts = ts.replace(hour=rng.choice([0, 1, 2, 3, 4, 23]))
        src = f"10.0.{rng.randint(0, 5)}.{rng.randint(2, 250)}"
        info = USERS[user]
        lines.append(
            f"{ts.strftime('%b %d %H:%M:%S')} {info['host']} {info['proc']}: "
            f"user={user} event={event} src={src}"
        )
    return lines
