# -*- coding: utf-8 -*-
"""法人/個人 収支の暫定サマリ（利用日ベース・2025/2026）。
セグメント×入出金で 売上/経費/役員勘定/個人収支 を分けて集計。Amazon等の保留は別掲。"""
import csv, os
from collections import defaultdict
BASE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(BASE, "ledger_master.csv"), encoding="utf-8-sig")))
def y(r): return r["use_date"][:4]
def out(r):  # 支出方向か（カードは出金、銀行は出金）
    return r["flow"] == "出金"
A = int

for yr in ["2025", "2026"]:
    rs = [r for r in rows if y(r) == yr]
    sales = sum(A(r["amount"]) for r in rs if r["segment"] == "法人" and r["flow"] == "入金")
    corp_exp = sum(A(r["amount"]) for r in rs if r["segment"] == "法人" and r["flow"] == "出金")
    yakuin_pay = sum(A(r["amount"]) for r in rs if r["segment"] == "役員報酬")
    corp_total_exp = corp_exp + yakuin_pay
    op = sales - corp_total_exp
    # 個人
    p_income = sum(A(r["amount"]) for r in rs if r["segment"] == "役員報酬受取")
    p_living = sum(A(r["amount"]) for r in rs if r["segment"] == "個人候補" and out(r))
    p_bal = p_income - p_living
    # 役員勘定・財務（収支外）
    loan_to = sum(A(r["amount"]) for r in rs if r["segment"] == "役員貸付")
    borrow_from = sum(A(r["amount"]) for r in rs if r["segment"] == "役員借入")
    excl = sum(A(r["amount"]) for r in rs if r["segment"] == "除外")
    todo = sum(A(r["amount"]) for r in rs if r["segment"] == "要確認")
    amazon = sum(A(r["amount"]) for r in rs if "Amazon" in r["account"] and r["segment"] == "要確認")
    print(f"================= {yr} =================")
    print(f"【法人】売上高        {sales:>12,}")
    print(f"      販管費(役員報酬除く) {corp_exp:>12,}")
    print(f"      役員報酬        {yakuin_pay:>12,}")
    print(f"      営業利益(概算)   {op:>12,}")
    print(f"【個人】役員報酬 受取   {p_income:>12,}")
    print(f"      生活費・個人支出  {p_living:>12,}")
    print(f"      個人収支(概算)   {p_bal:>12,}")
    print(f"【役員勘定/財務(収支外)】役員貸付(法人→個人) {loan_to:>10,} / 役員借入(個人→法人) {borrow_from:>10,}")
    print(f"【収支外(除外)合計】 {excl:>12,}（カード決済振替・借入返済・手許現金・自社間振替等）")
    print(f"【保留】Amazon(明細待ち) {amazon:>10,} ／ その他要確認 {todo - amazon:>10,}")
    print()
