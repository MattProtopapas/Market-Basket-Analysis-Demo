"""
Import the synthetic CSV data into the Excel workbook.

Reads data/products.csv, data/transactions.csv, data/baskets.csv and writes
each into its own tab of "Market Basket Analysis Demo.xlsx":
    Products | Transactions | Baskets

Any existing "Results" tab is preserved.
"""

import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
WORKBOOK = os.path.join(BASE_DIR, "Market Basket Analysis Demo.xlsx")

SHEETS = {
    "Products": "products.csv",
    "Transactions": "transactions.csv",
    "Baskets": "baskets.csv",
}


def main():
    frames = {
        sheet: pd.read_csv(os.path.join(DATA_DIR, csv))
        for sheet, csv in SHEETS.items()
    }

    # If the workbook already exists, append/replace these sheets so a
    # previously written "Results" tab survives the re-import.
    if os.path.exists(WORKBOOK):
        writer_kwargs = dict(mode="a", if_sheet_exists="replace")
    else:
        writer_kwargs = dict(mode="w")

    with pd.ExcelWriter(WORKBOOK, engine="openpyxl", **writer_kwargs) as xl:
        for sheet, df in frames.items():
            df.to_excel(xl, sheet_name=sheet, index=False)
            print(f"Wrote {len(df):>5} rows -> '{sheet}' tab")

        # Drop the empty default sheet openpyxl creates with a new workbook
        # (named "Sheet"/"Φύλλο1"/etc. depending on locale).
        wb = xl.book
        for name in list(wb.sheetnames):
            ws = wb[name]
            if name not in frames and name != "Results" and ws.max_row <= 1:
                del wb[name]

    print(f"\nWorkbook saved: {WORKBOOK}")


if __name__ == "__main__":
    main()
