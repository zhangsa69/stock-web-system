#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特朗普持仓数据更新脚本 (元基鉴股 · 美国持仓监控)
从 Kadoa Congress Trading Monitor 拉取特朗普的最新披露数据，
聚合成前端可视化所需的 JSON 和 JS 两份文件。

用法:
  python3 update_trump_data.py
  或 crontab 定时调用。

依赖:
  - 网络可访问 raw.githubusercontent.com (443)
"""
import json, os, sys, re, urllib.request, urllib.parse
from collections import defaultdict
from datetime import datetime

# ==================== 配置 ====================
RAW_URL = (
    "https://raw.githubusercontent.com/kadoa-org/"
    "congress-trading-monitor/main/public/data/filer/oge_donald_trump.json"
)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 项目输出目录(scripts 与 congress-dist 同级)
OUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "congress-dist", "data"))
RAW_CACHE = os.path.join(OUT_DIR, "trump_raw.json")
JSON_OUT = os.path.join(OUT_DIR, "trump.json")
JS_OUT = os.path.join(OUT_DIR, "trump.js")
CREDS_UA = "yuanji-stock-web-system/1.0 (data-monitor)"

# 允许的数据源站点(仅这些域名可拉取)
ALLOWED_HOSTS = {"raw.githubusercontent.com", "github.com", "www.kadoa.com"}


def fetch(url):
    """带 UA 和 TLS 的下载，仅允许白名单域名"""
    host = urllib.parse.urlparse(url).hostname
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"拒绝访问非白名单域名: {host}")
    req = urllib.request.Request(url, headers={"User-Agent": CREDS_UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def mid(t):
    """金额区间 -> 中位估计金额"""
    lo, hi = t.get("amount_range_low"), t.get("amount_range_high")
    if lo is not None and hi is not None:
        return (lo + hi) / 2.0
    return None


def solve_name(asset_name, ticker):
    n = (asset_name or "").strip()
    if not n:
        return ticker or "未知资产"
    if n.isupper():
        return n.title()
    return n


def aggregate(trades):
    """核心聚合逻辑，返回前端数据结构"""
    n_total = len(trades)
    with_ticker = [t for t in trades if t.get("ticker")]
    n_stock = len(with_ticker)
    n_bond = n_total - n_stock
    buys = [t for t in trades if t.get("transaction_type") == "Purchase"]
    sells = [t for t in trades if t.get("transaction_type") and t.get("transaction_type") != "Purchase"]
    est_volume = sum(mid(t) or 0 for t in trades)
    late = sum(1 for t in trades if t.get("is_late"))
    delays = sorted([t.get("days_to_file") for t in trades if t.get("days_to_file") is not None])
    med_delay = delays[len(delays) // 2] if delays else None

    # 持仓(按ticker聚合)
    h = defaultdict(lambda: {"buy_count": 0, "sell_count": 0, "est_low": 0, "est_high": 0,
                             "rets": [], "last_trade": None, "name": None})
    for t in with_ticker:
        tick = t["ticker"]
        x = h[tick]
        if t.get("transaction_type") == "Purchase":
            x["buy_count"] += 1
        else:
            x["sell_count"] += 1
        x["est_low"] += t.get("amount_range_low") or 0
        x["est_high"] += t.get("amount_range_high") or 0
        if t.get("ret_30d") is not None:
            x["rets"].append(t["ret_30d"])
        if not x["last_trade"] or (t.get("transaction_date") and t["transaction_date"] > x["last_trade"]["date"]):
            x["last_trade"] = {"date": t.get("transaction_date"), "type": t.get("transaction_type"),
                               "amount": t.get("amount_range_label")}
        if not x["name"]:
            x["name"] = solve_name(t.get("asset_name"), tick)
    holdings = []
    for tick, x in h.items():
        holdings.append({
            "ticker": tick, "name": x["name"],
            "buy_count": x["buy_count"], "sell_count": x["sell_count"],
            "est_low": x["est_low"], "est_high": x["est_high"],
            "est_volume": (x["est_low"] + x["est_high"]) / 2,
            "ret_30d_avg": (sum(x["rets"]) / len(x["rets"])) if x["rets"] else None,
            "last_trade": x["last_trade"],
        })
    holdings.sort(key=lambda x: -x["est_volume"])

    # 时间趋势(按月买卖额)
    tl = defaultdict(lambda: {"buy": 0, "sell": 0})
    for t in trades:
        dt = t.get("transaction_date")
        if not dt:
            continue
        m = mid(t)
        if m is None:
            continue
        if t.get("transaction_type") == "Purchase":
            tl[dt[:7]]["buy"] += m
        else:
            tl[dt[:7]]["sell"] += m
    timeline = [{"month": k, "buy": v["buy"], "sell": v["sell"]} for k, v in sorted(tl.items())]

    # 资产类别
    sectors = defaultdict(lambda: {"count": 0, "est_volume": 0})
    for t in trades:
        cat = "美股个股" if t.get("ticker") else "市政债券及固收"
        m = mid(t) or 0
        sectors[cat]["count"] += 1
        sectors[cat]["est_volume"] += m
    sector = [{"name": k, "count": v["count"], "est_volume": v["est_volume"]} for k, v in sectors.items()]

    # 重大交易Top30
    top = sorted(trades, key=lambda t: -(mid(t) or 0))[:30]
    topTrades = [{
        "date": t.get("transaction_date"),
        "name": solve_name(t.get("asset_name"), t.get("ticker")),
        "ticker": t.get("ticker"),
        "type": "买入" if t.get("transaction_type") == "Purchase" else "卖出",
        "amount": t.get("amount_range_label"),
        "ret_30d": t.get("ret_30d"),
        "is_late": bool(t.get("is_late")),
    } for t in top]

    return {
        "total": n_total, "stock": n_stock, "bond": n_bond,
        "buy": len(buys), "sell": len(sells), "est_volume": round(est_volume),
        "late_rate": round(late / n_total * 100, 1) if n_total else 0,
        "median_delay": med_delay,
        "holdings": holdings, "timeline": timeline, "sector": sector,
        "topTrades": topTrades,
    }


def main():
    print(f"[1/4] 拉取原始数据: {RAW_URL}")
    raw = fetch(RAW_URL)
    data = json.loads(raw)
    filer = data.get("filer", {})
    trades = data.get("trades", [])
    print(f"      披露人: {filer.get('full_name')} · {len(trades)} 笔交易")

    # 缓存原始
    with open(RAW_CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print("[2/4] 聚合数据…")
    agg = aggregate(trades)

    ts = datetime.now()
    out = {
        "meta": {
            "name": filer.get("full_name", "Donald J Trump"),
            "office": filer.get("office", "President"),
            "agency": filer.get("agency"),
            "updated": ts.strftime("%Y-%m-%d %H:%M"),
            "source": "Kadoa Congress Trading Monitor (STOCK Act 披露)",
            "source_url": "https://www.kadoa.com/congress/",
            "note": "数据来自美国《STOCK Act》官方披露，仅作研究参考",
        },
        "summary": agg,
        "holdings": agg["holdings"],
        "timeline": agg["timeline"],
        "sector": agg["sector"],
        "topTrades": agg["topTrades"],
    }

    print("[3/4] 写出 JSON…")
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("[4/4] 写出 JS(browser变量)…")
    js = "// 特朗普持仓数据 —— 由 update_trump_data.py 自动生成\n" \
         "// 生成时间: " + ts.strftime("%Y-%m-%d %H:%M:%S") + "\n" \
         "window.TRUMP_DATA = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n"
    with open(JS_OUT, "w", encoding="utf-8") as f:
        f.write(js)

    print(f"\n✅ 完成: {len(trades)} 笔交易 → {os.path.basename(JSON_OUT)} + {os.path.basename(JS_OUT)}")
    print(f"   股票持仓 {agg['stock']} · 固收 {agg['bond']} · 估算额 ${agg['est_volume']:,}")


if __name__ == "__main__":
    sys.exit(main())
