"""
Generate sample retail transaction data for Market Basket Analysis.

Produces three files in ./data:
  - products.csv      : product catalog (id, name, category, price)
  - transactions.csv  : long format, one row per item per transaction
  - baskets.csv       : wide format, one row per transaction (comma-joined items)

The generator intentionally injects co-purchase "rules" (e.g. bread -> butter,
pasta -> tomato sauce, beer -> chips) so that association-rule mining will find
meaningful lift/confidence patterns rather than pure noise.
"""

import csv
import os
import random
from datetime import datetime, timedelta

import numpy as np

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

N_TRANSACTIONS = 3000
START_DATE = datetime(2025, 1, 1)
DAYS = 180
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# --- Product catalog: name -> (category, price) -------------------------------
PRODUCTS = {
    "Bread":            ("Bakery", 2.49),
    "Butter":           ("Dairy", 3.99),
    "Jam":              ("Pantry", 3.29),
    "Milk":             ("Dairy", 1.99),
    "Eggs":             ("Dairy", 3.49),
    "Cheese":           ("Dairy", 5.49),
    "Cereal":           ("Breakfast", 4.29),
    "Coffee":           ("Beverages", 7.99),
    "Sugar":            ("Pantry", 2.19),
    "Tea":              ("Beverages", 4.49),
    "Pasta":            ("Pantry", 1.79),
    "Tomato Sauce":     ("Pantry", 2.89),
    "Parmesan":         ("Dairy", 6.49),
    "Ground Beef":      ("Meat", 8.99),
    "Onions":           ("Produce", 1.29),
    "Garlic":           ("Produce", 0.89),
    "Beer":             ("Alcohol", 9.99),
    "Chips":            ("Snacks", 3.49),
    "Salsa":            ("Snacks", 3.79),
    "Soda":             ("Beverages", 2.49),
    "Wine":             ("Alcohol", 12.99),
    "Diapers":          ("Baby", 14.99),
    "Baby Wipes":       ("Baby", 4.99),
    "Bananas":          ("Produce", 1.49),
    "Apples":           ("Produce", 2.99),
    "Lettuce":          ("Produce", 1.99),
    "Tomatoes":         ("Produce", 2.49),
    "Chicken Breast":   ("Meat", 7.49),
    "Rice":             ("Pantry", 3.99),
    "Yogurt":           ("Dairy", 4.49),
}

ALL_ITEMS = list(PRODUCTS.keys())

# --- Association rules: trigger item -> [(companion, probability), ...] -------
# When the trigger lands in a basket, each companion is added with given prob.
RULES = {
    "Bread":         [("Butter", 0.65), ("Jam", 0.40), ("Milk", 0.35)],
    "Pasta":         [("Tomato Sauce", 0.70), ("Parmesan", 0.45), ("Garlic", 0.30)],
    "Tomato Sauce":  [("Onions", 0.40), ("Ground Beef", 0.35)],
    "Beer":          [("Chips", 0.60), ("Salsa", 0.40)],
    "Chips":         [("Salsa", 0.55), ("Soda", 0.45)],
    "Diapers":       [("Baby Wipes", 0.75), ("Beer", 0.30)],
    "Cereal":        [("Milk", 0.70), ("Bananas", 0.40)],
    "Coffee":        [("Sugar", 0.50), ("Milk", 0.45)],
    "Tea":           [("Sugar", 0.45), ("Milk", 0.30)],
    "Ground Beef":   [("Onions", 0.50), ("Garlic", 0.40)],
    "Chicken Breast":[("Rice", 0.55), ("Lettuce", 0.30)],
    "Wine":          [("Cheese", 0.55), ("Parmesan", 0.25)],
}

# Items that show up frequently on their own as "seed" purchases.
POPULAR_SEEDS = [
    "Bread", "Milk", "Eggs", "Bananas", "Coffee", "Pasta", "Beer",
    "Cereal", "Chicken Breast", "Apples", "Cheese", "Chips", "Diapers",
    "Wine", "Tea", "Yogurt", "Soda", "Tomatoes", "Lettuce", "Rice",
]


def build_basket():
    """Construct one transaction as a set of item names."""
    basket = set()

    # 1-3 independent seed items to start the basket.
    n_seeds = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15])[0]
    for item in random.sample(POPULAR_SEEDS, n_seeds):
        basket.add(item)

    # Apply association rules (iterate over a snapshot since basket grows).
    for trigger in list(basket):
        for companion, prob in RULES.get(trigger, []):
            if random.random() < prob:
                basket.add(companion)

    # A little random noise: occasionally toss in a random extra item.
    if random.random() < 0.30:
        basket.add(random.choice(ALL_ITEMS))

    return basket


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # products.csv
    products_path = os.path.join(OUT_DIR, "products.csv")
    with open(products_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["product_id", "product_name", "category", "unit_price"])
        for i, (name, (cat, price)) in enumerate(PRODUCTS.items(), start=1):
            w.writerow([f"P{i:03d}", name, cat, f"{price:.2f}"])

    name_to_id = {name: f"P{i:03d}" for i, name in enumerate(PRODUCTS, start=1)}

    # transactions.csv (long) + baskets.csv (wide)
    tx_path = os.path.join(OUT_DIR, "transactions.csv")
    basket_path = os.path.join(OUT_DIR, "baskets.csv")

    total_items = 0
    with open(tx_path, "w", newline="", encoding="utf-8") as ftx, \
         open(basket_path, "w", newline="", encoding="utf-8") as fbk:
        tx_writer = csv.writer(ftx)
        bk_writer = csv.writer(fbk)
        tx_writer.writerow(
            ["transaction_id", "date", "product_id", "product_name",
             "category", "quantity", "unit_price", "line_total"]
        )
        bk_writer.writerow(["transaction_id", "date", "n_items", "items"])

        for t in range(1, N_TRANSACTIONS + 1):
            tx_id = f"T{t:05d}"
            day_offset = random.randint(0, DAYS - 1)
            date = (START_DATE + timedelta(days=day_offset)).strftime("%Y-%m-%d")

            items = sorted(build_basket())
            total_items += len(items)

            for item in items:
                qty = random.choices([1, 2, 3], weights=[0.7, 0.22, 0.08])[0]
                price = PRODUCTS[item][1]
                cat = PRODUCTS[item][0]
                tx_writer.writerow(
                    [tx_id, date, name_to_id[item], item, cat,
                     qty, f"{price:.2f}", f"{qty * price:.2f}"]
                )

            bk_writer.writerow([tx_id, date, len(items), ", ".join(items)])

    print(f"Wrote {len(PRODUCTS)} products       -> {products_path}")
    print(f"Wrote {N_TRANSACTIONS} transactions  -> {tx_path}")
    print(f"Wrote {N_TRANSACTIONS} baskets        -> {basket_path}")
    print(f"Avg basket size: {total_items / N_TRANSACTIONS:.2f} items")


if __name__ == "__main__":
    main()
