# -*- coding: utf-8 -*-
import csv, os
from collections import defaultdict
BASE = os.path.dirname(os.path.abspath(__file__))
rows=[]
with open(os.path.join(BASE,"ledger_master.csv"),encoding="utf-8-sig") as f:
    rows=list(csv.DictReader(f))

def yr(d): return d[:4]
def ym(d): return d[:7]

# カード名義別 × セグメント（2026 1〜6月、利用日）
ow=defaultdict(lambda:defaultdict(int))
for r in rows:
    if yr(r["use_date"])=="2026":
        ow[r["owner"]][r["segment"]]+=int(r["amount"])
print("=== 名義別×セグメント（2026/1〜6・利用日）===")
print(f"{'名義':<6}{'法人':>11}{'個人候補':>11}{'要確認':>11}{'除外':>11}")
for o in ow:
    d=ow[o]
    print(f"{o:<6}{d.get('法人',0):>11,}{d.get('個人候補',0):>11,}{d.get('要確認',0):>11,}{d.get('除外',0):>11,}")

# セグメント別 金額シェア（利用日2025/2026別、除外を分離）
seg=defaultdict(lambda:defaultdict(int))
for r in rows:
    y=yr(r["use_date"]); a=int(r["amount"])
    seg[r["segment"]][y]+=a
print("\n=== セグメント別 金額（全カード合算・利用日・年別）===")
print(f"{'セグメント':<10}{'2025':>12}{'2026':>12}{'その他年':>12}")
for s in ["法人","個人候補","要確認","除外"]:
    d=seg.get(s,{})
    y25=d.get("2025",0); y26=d.get("2026",0)
    oth=sum(v for k,v in d.items() if k not in("2025","2026"))
    print(f"{s:<10}{y25:>12,}{y26:>12,}{oth:>12,}")

# 科目別×年（法人＋要確認＋個人候補、除外のぞく）。2026を主軸、2025比較
acct=defaultdict(lambda:defaultdict(int))
for r in rows:
    if r["segment"]=="除外": continue
    acct[r["account"]][yr(r["use_date"])]+=int(r["amount"])
print("\n=== 科目別 合計（利用日・除外のぞく）2025 / 2026 ===")
print(f"{'2025':>11}{'2026':>11}  科目")
for k in sorted(acct, key=lambda x:-(acct[x].get('2026',0)+acct[x].get('2025',0))):
    d=acct[k]
    print(f"{d.get('2025',0):>11,}{d.get('2026',0):>11,}  {k}")

# 2026 月次（法人セグメントのみ・確定事業費の推移）
print("\n=== 2026 月次：法人セグメント合計（利用日・確定事業費）===")
mon=defaultdict(int)
for r in rows:
    if r["segment"]=="法人" and yr(r["use_date"])=="2026":
        mon[ym(r["use_date"])]+=int(r["amount"])
for k in sorted(mon):
    print(f"{k}  {mon[k]:>10,}")
