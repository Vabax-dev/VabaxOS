"""The settings of the automatic check, and when it last ran.

    ~/.config/vabaxos/update.json       {"frequency": "daily", "notify": "security"}
    ~/.local/state/vabaxos/update.json  {"last_check": 1730000000}

frequency: daily, weekly or never; notify: security (only security updates
are announced, the default) or all.
"""

import json
import os

DEFAULTS = {"frequency": "daily", "notify": "security"}
FREQUENCIES = ("daily", "weekly", "never")
NOTIFY = ("security", "all")
DAY = 24 * 3600


def _dir(variable, fallback):
    return os.path.join(os.environ.get(variable) or os.path.expanduser(fallback), "vabaxos")


def config_path():
    return os.path.join(_dir("XDG_CONFIG_HOME", "~/.config"), "update.json")


def state_path():
    return os.path.join(_dir("XDG_STATE_HOME", "~/.local/state"), "update.json")


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    os.replace(tmp, path)


def load():
    data = dict(DEFAULTS)
    data.update(_load(config_path()))
    if data["frequency"] not in FREQUENCIES:
        data["frequency"] = DEFAULTS["frequency"]
    if data["notify"] not in NOTIFY:
        data["notify"] = DEFAULTS["notify"]
    return data


def save(data):
    _save(config_path(), {key: data[key] for key in DEFAULTS if key in data})


def last_check():
    value = _load(state_path()).get("last_check", 0)
    return value if isinstance(value, (int, float)) else 0


def mark_checked(now):
    state = _load(state_path())
    state["last_check"] = int(now)
    _save(state_path(), state)


def check_due(data, last, now):
    """Whether the automatic check runs now."""
    if data["frequency"] == "never":
        return False
    period = DAY if data["frequency"] == "daily" else 7 * DAY
    # A little less than the period: the timer itself runs once a day.
    return now - last >= period - 3600
