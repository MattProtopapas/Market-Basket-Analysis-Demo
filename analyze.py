"""
Market Basket Analysis on the synthetic data in the Excel workbook.

Reads the "Baskets" tab of "Market Basket Analysis Demo.xlsx", one-hot encodes
the baskets, mines frequent itemsets with the Apriori algorithm, derives
association rules ranked by lift, and writes them back to a "Results" tab in the
same workbook (the data tabs are preserved).

Usage:
    python analyze.py                       # defaults below
    python analyze.py --min-support 0.02 --min-confidence 0.3 --top 20
"""

import argparse
import os

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKBOOK = os.path.join(BASE_DIR, "Market Basket Analysis Demo.xlsx")
BASKETS_SHEET = "Baskets"
RESULTS_SHEET = "Results"


def load_baskets(workbook, sheet):
    """Return a list of item-lists from the wide 'Baskets' tab."""
    df = pd.read_excel(workbook, sheet_name=sheet)
    return [
        [item.strip() for item in str(row).split(",") if item.strip()]
        for row in df["items"]
    ]


def one_hot(transactions):
    """One-hot encode transactions into a boolean DataFrame (tx x item)."""
    items = sorted({item for tx in transactions for item in tx})
    rows = [{item: (item in set(tx)) for item in items} for tx in transactions]
    return pd.DataFrame(rows, columns=items).astype(bool)


def main():
    parser = argparse.ArgumentParser(description="Market Basket Analysis demo")
    parser.add_argument("--min-support", type=float, default=0.02,
                        help="Minimum support for frequent itemsets (default 0.02)")
    parser.add_argument("--min-confidence", type=float, default=0.30,
                        help="Minimum confidence for rules (default 0.30)")
    parser.add_argument("--top", type=int, default=20,
                        help="How many top rules to display (default 20)")
    args = parser.parse_args()

    transactions = load_baskets(WORKBOOK, BASKETS_SHEET)
    print(f"Loaded {len(transactions)} transactions from "
          f"'{BASKETS_SHEET}' tab of {WORKBOOK}")

    basket_df = one_hot(transactions)
    print(f"One-hot matrix: {basket_df.shape[0]} transactions x "
          f"{basket_df.shape[1]} items\n")

    # 1) Frequent itemsets
    frequent = apriori(basket_df, min_support=args.min_support,
                       use_colnames=True)
    if frequent.empty:
        print("No frequent itemsets at this support level. Lower --min-support.")
        return
    frequent = frequent.sort_values("support", ascending=False)

    print(f"=== Top frequent itemsets (min_support={args.min_support}) ===")
    top_sets = frequent.head(args.top).copy()
    top_sets["itemsets"] = top_sets["itemsets"].apply(
        lambda s: ", ".join(sorted(s)))
    print(top_sets.to_string(index=False,
          formatters={"support": "{:.3f}".format}))
    print()

    # 2) Association rules ranked by lift
    rules = association_rules(frequent, metric="confidence",
                              min_threshold=args.min_confidence)
    if rules.empty:
        print("No rules at this confidence level. Lower --min-confidence.")
        return

    rules = rules.sort_values(["lift", "confidence"], ascending=False)
    rules["antecedents"] = rules["antecedents"].apply(
        lambda s: ", ".join(sorted(s)))
    rules["consequents"] = rules["consequents"].apply(
        lambda s: ", ".join(sorted(s)))

    cols = ["antecedents", "consequents", "support", "confidence", "lift"]
    print(f"=== Top {args.top} association rules by lift "
          f"(min_confidence={args.min_confidence}) ===")
    print(rules[cols].head(args.top).to_string(
        index=False,
        formatters={
            "support": "{:.3f}".format,
            "confidence": "{:.3f}".format,
            "lift": "{:.2f}".format,
        },
    ))

    results = rules[cols].reset_index(drop=True)
    with pd.ExcelWriter(WORKBOOK, engine="openpyxl",
                        mode="a", if_sheet_exists="replace") as xl:
        results.to_excel(xl, sheet_name=RESULTS_SHEET, index=False)
    print(f"\nFull rule set ({len(results)} rules) written to "
          f"'{RESULTS_SHEET}' tab of {WORKBOOK}")


if __name__ == "__main__":
    main()
