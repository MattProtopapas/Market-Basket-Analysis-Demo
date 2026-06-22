"""
Input data validation / data-quality tests for the Market Basket workbook.

Reads the Products, Transactions and Baskets tabs of
"Market Basket Analysis Demo.xlsx", runs a suite of data-quality checks, prints
a summary, and writes the results to a "Data Quality" tab.

Each test reports: how many rows were checked, how many violated the rule, a
PASS/FAIL status, and a few example offenders to aid debugging.

Usage:
    python validate_data.py
    python validate_data.py --strict     # exit code 1 if any test fails
"""

import argparse
import os
import sys

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKBOOK = os.path.join(BASE_DIR, "Market Basket Analysis Demo.xlsx")
RESULTS_SHEET = "Data Quality"

EXAMPLE_LIMIT = 5  # max example offenders recorded per failing test


class Validator:
    """Collects data-quality test results."""

    def __init__(self):
        self.results = []

    def record(self, test, description, checked, offenders):
        """offenders: an iterable of human-readable offending values."""
        offenders = list(dict.fromkeys(str(o) for o in offenders))  # dedupe
        n = len(offenders)
        self.results.append({
            "test": test,
            "description": description,
            "rows_checked": checked,
            "violations": n,
            "status": "PASS" if n == 0 else "FAIL",
            "examples": "" if n == 0 else "; ".join(offenders[:EXAMPLE_LIMIT]),
        })

    def to_frame(self):
        return pd.DataFrame(self.results, columns=[
            "test", "description", "rows_checked",
            "violations", "status", "examples"])


def load_tabs(workbook):
    products = pd.read_excel(workbook, sheet_name="Products")
    transactions = pd.read_excel(workbook, sheet_name="Transactions")
    baskets = pd.read_excel(workbook, sheet_name="Baskets")
    return products, transactions, baskets


def split_items(cell):
    return [i.strip() for i in str(cell).split(",") if i.strip()]


def run_checks(products, transactions, baskets):
    v = Validator()

    valid_ids = set(products["product_id"])
    valid_names = set(products["product_name"])
    id_to_name = dict(zip(products["product_id"], products["product_name"]))
    id_to_price = dict(zip(products["product_id"], products["unit_price"]))
    id_to_cat = dict(zip(products["product_id"], products["category"]))

    # --- Product catalog integrity ------------------------------------------
    dup_ids = products.loc[products["product_id"].duplicated(), "product_id"]
    v.record("products.unique_id",
             "Each product_id in the catalog is unique",
             len(products), dup_ids)

    dup_names = products.loc[products["product_name"].duplicated(),
                             "product_name"]
    v.record("products.unique_name",
             "Each product_name in the catalog is unique",
             len(products), dup_names)

    cat_nulls = products[products.isnull().any(axis=1)]["product_id"]
    v.record("products.no_missing",
             "No missing values in any catalog column",
             len(products), cat_nulls)

    bad_price = products.loc[
        ~(pd.to_numeric(products["unit_price"], errors="coerce") > 0),
        "product_id"]
    v.record("products.positive_price",
             "Every catalog unit_price is a number greater than 0",
             len(products), bad_price)

    # --- Transactions: referential integrity --------------------------------
    bad_tx_id = transactions.loc[
        ~transactions["product_id"].isin(valid_ids), "product_id"]
    v.record("transactions.product_id_in_catalog",
             "Every transaction product_id exists in the Products catalog",
             len(transactions), bad_tx_id)

    bad_tx_name = transactions.loc[
        ~transactions["product_name"].isin(valid_names), "product_name"]
    v.record("transactions.product_name_in_catalog",
             "Every transaction product_name exists in the Products catalog",
             len(transactions), bad_tx_name)

    # id/name pairing matches the catalog
    name_mismatch = transactions[
        transactions["product_id"].isin(valid_ids) &
        (transactions["product_id"].map(id_to_name)
         != transactions["product_name"])
    ]
    v.record("transactions.id_name_consistency",
             "product_id and product_name agree with the catalog pairing",
             len(transactions),
             name_mismatch["product_id"].astype(str) + "->"
             + name_mismatch["product_name"].astype(str))

    # category matches catalog
    cat_mismatch = transactions[
        transactions["product_id"].isin(valid_ids) &
        (transactions["product_id"].map(id_to_cat) != transactions["category"])
    ]
    v.record("transactions.category_consistency",
             "Transaction category matches the catalog category",
             len(transactions),
             cat_mismatch["product_id"].astype(str) + ":"
             + cat_mismatch["category"].astype(str))

    # --- Transactions: value validity ---------------------------------------
    bad_qty = transactions.loc[
        ~(pd.to_numeric(transactions["quantity"], errors="coerce") > 0),
        "transaction_id"]
    v.record("transactions.positive_quantity",
             "Every transaction quantity is a positive integer",
             len(transactions), bad_qty)

    # unit_price matches catalog
    price_exp = transactions["product_id"].map(id_to_price)
    price_mismatch = transactions[
        transactions["product_id"].isin(valid_ids) &
        ((price_exp - transactions["unit_price"]).abs() > 0.005)
    ]
    v.record("transactions.unit_price_matches_catalog",
             "Transaction unit_price matches the catalog price",
             len(transactions),
             price_mismatch["product_id"].astype(str))

    # line_total == quantity * unit_price
    calc_total = transactions["quantity"] * transactions["unit_price"]
    total_mismatch = transactions[
        (calc_total - transactions["line_total"]).abs() > 0.005]
    v.record("transactions.line_total_correct",
             "line_total equals quantity * unit_price",
             len(transactions),
             total_mismatch["transaction_id"].astype(str))

    # valid dates
    parsed_dates = pd.to_datetime(transactions["date"], errors="coerce")
    bad_dates = transactions.loc[parsed_dates.isna(), "transaction_id"]
    v.record("transactions.valid_dates",
             "Every transaction date is a parseable date",
             len(transactions), bad_dates)

    # --- Baskets: integrity & consistency -----------------------------------
    basket_items = baskets["items"].apply(split_items)

    # every item in a basket exists in the catalog (by name)
    bad_basket_items = set()
    for items in basket_items:
        for it in items:
            if it not in valid_names:
                bad_basket_items.add(it)
    v.record("baskets.items_in_catalog",
             "Every item listed in a basket exists in the Products catalog",
             len(baskets), bad_basket_items)

    # no empty baskets
    empty = baskets.loc[basket_items.apply(len) == 0, "transaction_id"]
    v.record("baskets.non_empty",
             "No basket is empty",
             len(baskets), empty)

    # n_items column matches the actual item count
    count_mismatch = baskets.loc[
        basket_items.apply(len) != baskets["n_items"], "transaction_id"]
    v.record("baskets.n_items_matches",
             "Basket n_items equals the actual number of listed items",
             len(baskets), count_mismatch)

    # no duplicate items within a single basket
    dup_in_basket = baskets.loc[
        basket_items.apply(lambda x: len(x) != len(set(x))),
        "transaction_id"]
    v.record("baskets.no_duplicate_items",
             "No item appears more than once within the same basket",
             len(baskets), dup_in_basket)

    # unique transaction ids in baskets
    dup_bid = baskets.loc[baskets["transaction_id"].duplicated(),
                          "transaction_id"]
    v.record("baskets.unique_transaction_id",
             "Each basket transaction_id is unique",
             len(baskets), dup_bid)

    # --- Cross-tab consistency: Baskets vs Transactions ---------------------
    tx_ids = set(transactions["transaction_id"])
    bk_ids = set(baskets["transaction_id"])
    v.record("crosstab.basket_ids_in_transactions",
             "Every basket transaction_id appears in the Transactions tab",
             len(baskets), bk_ids - tx_ids)
    v.record("crosstab.transaction_ids_in_baskets",
             "Every transaction_id appears in the Baskets tab",
             len(tx_ids), tx_ids - bk_ids)

    # the set of items per transaction matches between the two tabs
    tx_items = (transactions.groupby("transaction_id")["product_name"]
                .apply(lambda s: frozenset(s)))
    bk_items = {row.transaction_id: frozenset(split_items(row.items))
                for row in baskets.itertuples()}
    item_set_mismatch = [
        tid for tid, items in tx_items.items()
        if bk_items.get(tid) != items]
    v.record("crosstab.item_sets_match",
             "Per-transaction item set matches between Transactions and Baskets",
             len(tx_items), item_set_mismatch)

    return v


def main():
    parser = argparse.ArgumentParser(description="Data-quality validation")
    parser.add_argument("--strict", action="store_true",
                        help="Exit with code 1 if any test fails")
    args = parser.parse_args()

    products, transactions, baskets = load_tabs(WORKBOOK)
    print(f"Loaded Products={len(products)}, Transactions={len(transactions)}, "
          f"Baskets={len(baskets)} from {WORKBOOK}\n")

    validator = run_checks(products, transactions, baskets)
    report = validator.to_frame()

    print(report.to_string(index=False))

    n_fail = int((report["status"] == "FAIL").sum())
    n_pass = int((report["status"] == "PASS").sum())
    print(f"\n{n_pass} passed, {n_fail} failed, {len(report)} total checks.")

    with pd.ExcelWriter(WORKBOOK, engine="openpyxl",
                        mode="a", if_sheet_exists="replace") as xl:
        report.to_excel(xl, sheet_name=RESULTS_SHEET, index=False)
    print(f"Report written to '{RESULTS_SHEET}' tab of {WORKBOOK}")

    if args.strict and n_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
