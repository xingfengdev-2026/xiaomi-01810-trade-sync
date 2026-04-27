# Xiaomi 01810 Trade Sync

This repo stores Xiaomi (`01810.HK`) position, cost, and full trade history in JSON files so your software can pull the latest state from `raw.githubusercontent.com`.

## Data files

- `data/latest.json`: latest position and cost snapshot.
- `data/trades.json`: full trade history with rolling fields.
- `data/config.json`: static config such as fee and lot size.

## Raw URLs

- Latest snapshot  
  `https://raw.githubusercontent.com/xingfengdev-2026/xiaomi-01810-trade-sync/main/data/latest.json`
- Trade history  
  `https://raw.githubusercontent.com/xingfengdev-2026/xiaomi-01810-trade-sync/main/data/trades.json`
- Config  
  `https://raw.githubusercontent.com/xingfengdev-2026/xiaomi-01810-trade-sync/main/data/config.json`

## Append a trade

```bash
python scripts/update_trade.py --action SELL --qty 200 --price 31.6 --note "reduce risk"
```

Optional arguments:

- `--fee 15`
- `--time 2026-04-27T10:30:00+08:00`

## Rebuild from formula

Use this only when you want to force all derived fields to be recalculated from history:

```bash
python scripts/update_trade.py --rebuild
```

## Suggested sync flow

1. Your software writes a new trade via `update_trade.py`.
2. Commit and push to `main`.
3. Any client fetches latest values from the raw URLs.

