#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
TRADES_PATH = DATA_DIR / "trades.json"
LATEST_PATH = DATA_DIR / "latest.json"
CONFIG_PATH = DATA_DIR / "config.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, data):
    with path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def compute_cost_change(action: str, qty: int, price_hkd: float, fee_hkd: float) -> float:
    gross = qty * price_hkd
    if action == "BUY":
        return round(gross + fee_hkd, 6)
    return round(-(gross - fee_hkd), 6)


def to_float(value):
    return float(value) if value is not None else None


def append_trade(action: str, qty: int, price_hkd: float, fee_hkd: float, ts: str | None, note: str | None):
    trades = load_json(TRADES_PATH)
    latest = load_json(LATEST_PATH)

    last_seq = int(latest.get("last_seq", len(trades)))
    prev_position = int(latest["position_shares"])
    prev_total_cost = to_float(latest["total_cost_hkd"])

    delta_position = qty if action == "BUY" else -qty
    new_position = prev_position + delta_position
    cost_change = compute_cost_change(action, qty, price_hkd, fee_hkd)
    new_total_cost = round(prev_total_cost + cost_change, 6)
    new_avg_cost = round(new_total_cost / new_position, 10) if new_position > 0 else 0.0

    item = {
        "seq": last_seq + 1,
        "action": action,
        "qty": qty,
        "price_hkd": price_hkd,
        "fee_hkd": fee_hkd,
        "cost_change_hkd": cost_change,
        "position_shares": new_position,
        "total_cost_hkd": new_total_cost,
        "avg_cost_hkd": new_avg_cost
    }
    if ts:
        item["timestamp"] = ts
    if note:
        item["note"] = note

    trades.append(item)
    save_json(TRADES_PATH, trades)

    latest_out = dict(latest)
    latest_out["as_of"] = ts or datetime.now().astimezone().isoformat(timespec="seconds")
    latest_out["position_shares"] = new_position
    latest_out["total_cost_hkd"] = new_total_cost
    latest_out["avg_cost_hkd"] = new_avg_cost
    latest_out["last_seq"] = item["seq"]
    latest_out["last_action"] = action
    latest_out["last_qty"] = qty
    latest_out["last_price_hkd"] = price_hkd
    save_json(LATEST_PATH, latest_out)

    print(f"Appended seq={item['seq']} action={action} qty={qty} price={price_hkd}")
    print(f"Position={new_position} TotalCost={new_total_cost} AvgCost={new_avg_cost}")


def rebuild():
    trades = load_json(TRADES_PATH)
    if not trades:
        raise SystemExit("No trades found")

    position = 0
    total_cost = 0.0
    for index, item in enumerate(trades, start=1):
        action = str(item["action"]).upper()
        qty = int(item["qty"])
        price_hkd = float(item["price_hkd"])
        fee_hkd = float(item.get("fee_hkd", 0))

        cost_change = compute_cost_change(action, qty, price_hkd, fee_hkd)
        position += qty if action == "BUY" else -qty
        total_cost = round(total_cost + cost_change, 6)
        avg_cost = round(total_cost / position, 10) if position > 0 else 0.0

        item["seq"] = index
        item["action"] = action
        item["qty"] = qty
        item["price_hkd"] = price_hkd
        item["fee_hkd"] = fee_hkd
        item["cost_change_hkd"] = cost_change
        item["position_shares"] = position
        item["total_cost_hkd"] = total_cost
        item["avg_cost_hkd"] = avg_cost

    save_json(TRADES_PATH, trades)

    last = trades[-1]
    latest = load_json(LATEST_PATH)
    latest["as_of"] = datetime.now().astimezone().isoformat(timespec="seconds")
    latest["position_shares"] = last["position_shares"]
    latest["total_cost_hkd"] = last["total_cost_hkd"]
    latest["avg_cost_hkd"] = last["avg_cost_hkd"]
    latest["last_seq"] = last["seq"]
    latest["last_action"] = last["action"]
    latest["last_qty"] = last["qty"]
    latest["last_price_hkd"] = last["price_hkd"]
    save_json(LATEST_PATH, latest)

    print("Rebuilt all derived fields from formula")
    print(f"Position={last['position_shares']} TotalCost={last['total_cost_hkd']}")


def main():
    parser = argparse.ArgumentParser(description="Append Xiaomi 01810 trade and update latest snapshot")
    parser.add_argument("--action", choices=["BUY", "SELL"], help="Trade action")
    parser.add_argument("--qty", type=int, help="Share quantity")
    parser.add_argument("--price", type=float, help="Trade price in HKD")
    parser.add_argument("--fee", type=float, default=None, help="Fee in HKD, default from config.json")
    parser.add_argument("--time", type=str, default=None, help="ISO timestamp, optional")
    parser.add_argument("--note", type=str, default=None, help="Optional note")
    parser.add_argument("--rebuild", action="store_true", help="Recompute all derived fields from history")
    args = parser.parse_args()

    if args.rebuild:
        rebuild()
        return

    if not (args.action and args.qty and args.price is not None):
        raise SystemExit("Require --action --qty --price or use --rebuild")

    config = load_json(CONFIG_PATH)
    fee_hkd = float(args.fee) if args.fee is not None else float(config["default_fee_hkd"])
    append_trade(args.action, args.qty, float(args.price), fee_hkd, args.time, args.note)


if __name__ == "__main__":
    main()

