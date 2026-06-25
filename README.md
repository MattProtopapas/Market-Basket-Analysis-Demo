# Market Basket Analysis Demo

A self-contained demo that generates (or accepts) retail transaction data,
validates its quality, and mines **association rules** ("customers who bought X
also bought Y") using the Apriori algorithm. All data and results live in a
single Excel workbook: **`Market Basket Analysis Demo.xlsx`**.

Read more about the [benefits of Market Basket Analysis](./Market_Basket_Analysis_Benefits.md) for Small and Medium Enterprises.


---

## Contents

- [What's in this project](#whats-in-this-project)
- [1. One-time setup: create the virtual environment](#1-one-time-setup-create-the-virtual-environment)
- [2. Import the data (two options)](#2-import-the-data-two-options)
  - [Option A — Generate synthetic sample data](#option-a--generate-synthetic-sample-data)
  - [Option B — Use your own real data](#option-b--use-your-own-real-data)
- [3. Validate and run the analysis](#3-validate-and-run-the-analysis)
- [Where the results go](#where-the-results-go)
- [Understanding the results (support, confidence, lift)](#understanding-the-results-support-confidence-lift)
- [Reference: data schemas](#reference-data-schemas)
- [Troubleshooting](#troubleshooting)

---

## What's in this project

| File | Type | Purpose |
|------|------|---------|
| `generate_data.py` | Python script | Generates synthetic sample data into the `data/` folder as three CSVs (`products.csv`, `transactions.csv`, `baskets.csv`). Co-purchase patterns (e.g. Bread→Butter, Pasta→Tomato Sauce, Beer→Chips, Diapers→Baby Wipes) are intentionally injected so the analysis surfaces meaningful rules. Reproducible (fixed random seed). |
| `import_to_excel.py` | Python script | Loads the three CSVs from `data/` into separate tabs of the Excel workbook: **Products**, **Transactions**, **Baskets**. Preserves the Results / Data Quality tabs. |
| `validate_data.py` | Python script | Runs 20 data-quality checks against the workbook tabs (referential integrity, value validity, cross-tab consistency) and writes a pass/fail report to the **Data Quality** tab. `--strict` makes it exit non-zero if any check fails. |
| `analyze.py` | Python script | Reads the **Baskets** tab, one-hot encodes the transactions, mines frequent itemsets (Apriori) and association rules, and writes them ranked by lift to the **Results** tab. Accepts `--min-support`, `--min-confidence`, `--top`. |
| `run_analysis.py` | Python script | **Gated pipeline runner.** Runs `validate_data.py --strict` first; only if every check passes does it run `analyze.py`. Forwards any extra args to the analysis. |
| `requirements.txt` | Dependencies | `pandas`, `numpy`, `mlxtend`, `openpyxl`. |
| `Market Basket Analysis Demo.xlsx` | Excel workbook | The single source of data and results. Tabs: **Products**, **Transactions**, **Baskets**, **Results**, **Data Quality**. |
| `data/` | Folder | The CSV inputs: `products.csv`, `transactions.csv`, `baskets.csv`. |
| `.gitignore` | Config | Excludes `.venv/` and Python caches from version control. |

**Typical end-to-end flow:** `generate_data.py` (or drop in your own CSVs) →
`import_to_excel.py` → `run_analysis.py` (validate → analyze).

---

## 1. One-time setup: create the virtual environment

These steps use **Windows PowerShell** from the project root.

```powershell
# 1. Create a virtual environment in .venv (uses your system Python 3.x)
python -m venv .venv

# 2. Install the dependencies into it
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> **Behind a corporate proxy / SSL inspection ?**
> If `pip install` fails with `SSLError: CERTIFICATE_VERIFY_FAILED`, add the
> trusted-host flags:
>
> ```powershell
> .\.venv\Scripts\python.exe -m pip install -r requirements.txt `
>   --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org
> ```

**Running the scripts.** You can either call the venv's interpreter directly
(no activation needed):

```powershell
.\.venv\Scripts\python.exe <script>.py
```

…or **activate** the environment first and then just use `python`:

```powershell
.\.venv\Scripts\Activate.ps1     # prompt now shows (.venv)
python <script>.py
deactivate                        # when finished
```

> If activation is blocked by execution policy, run once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

The examples below use the direct-interpreter form so they work whether or not
the environment is activated.

---

## 2. Import the data (two options)

Both options end the same way: the three CSVs in `data/` are loaded into the
workbook by `import_to_excel.py`.

### Option A — Generate synthetic sample data

Best for demos and trying the pipeline. Recreates the CSVs from scratch.

```powershell
.\.venv\Scripts\python.exe generate_data.py      # writes data/*.csv
.\.venv\Scripts\python.exe import_to_excel.py     # loads them into the workbook tabs
```

Tune the volume by editing the constants near the top of `generate_data.py`
(`N_TRANSACTIONS`, `START_DATE`, `DAYS`), the catalog in `PRODUCTS`, and the
injected co-purchase patterns in `RULES`.

### Option B — Use your own real data

Replace the CSV files in `data/` with your own, **keeping the same file names
and column headers** (see [data schemas](#reference-data-schemas)), then import:

```powershell
# 1. Overwrite these three files with your real exports (same columns):
#      data\products.csv
#      data\transactions.csv
#      data\baskets.csv
#
# 2. Load them into the workbook:
.\.venv\Scripts\python.exe import_to_excel.py
```

> **Do not run `generate_data.py` in this option** — it would overwrite your
> real CSVs with synthetic data.

Notes for real data:
- All three files must be **mutually consistent** (same transactions, matching
  item sets, prices that match the catalog) or the validation step will flag it.
  The validator tells you exactly which rows fail.
- The analysis itself only needs the **Baskets** tab. The Products and
  Transactions tabs power the data-quality cross-checks. If you only have
  basket-level data, you can still run the analysis, but several validation
  tests will report failures for the missing/inconsistent tabs.

---

## 3. Validate and run the analysis

**Recommended — gated run (validate first, analyze only on clean data):**

```powershell
.\.venv\Scripts\python.exe run_analysis.py
```

Pass analysis parameters straight through:

```powershell
.\.venv\Scripts\python.exe run_analysis.py --min-support 0.01 --min-confidence 0.2 --top 30
```

**Or run the steps individually:**

```powershell
.\.venv\Scripts\python.exe validate_data.py          # writes the Data Quality tab
.\.venv\Scripts\python.exe validate_data.py --strict  # same, but exits 1 on any failure
.\.venv\Scripts\python.exe analyze.py                 # writes the Results tab
```

**Analysis parameters (`analyze.py` / forwarded via `run_analysis.py`):**

| Flag | Default | Meaning |
|------|---------|---------|
| `--min-support` | `0.02` | Minimum fraction of baskets an itemset must appear in to be "frequent". Lower = more (rarer) itemsets. |
| `--min-confidence` | `0.30` | Minimum confidence for a rule to be kept. |
| `--top` | `20` | How many top rules/itemsets to print to the console. |

Each run **rewrites** its own tab (Results / Data Quality) in place; the other
tabs are left untouched, so nothing goes stale.

---

## Where the results go

Everything is written back into **`Market Basket Analysis Demo.xlsx`**:

| Tab | Written by | Contents |
|-----|------------|----------|
| **Products** | `import_to_excel.py` | The product catalog. |
| **Transactions** | `import_to_excel.py` | Line-item level transactions. |
| **Baskets** | `import_to_excel.py` | One row per transaction (the analysis input). |
| **Data Quality** | `validate_data.py` | One row per check: test, description, rows checked, violations, PASS/FAIL, example offenders. |
| **Results** | `analyze.py` | Association rules: antecedents, consequents, support, confidence, lift (sorted by lift). |

---

## Understanding the results (support, confidence, lift)

Market basket analysis looks for **association rules** of the form
**`{antecedents} → {consequents}`**, read as *"when a basket contains the
antecedent item(s), it also tends to contain the consequent item(s)."* For
example `{Bread, Butter} → {Jam}` means baskets with bread and butter often also
contain jam.

The **Results** tab scores every rule with three metrics. Below, "baskets" =
transactions, and `P(X)` = the fraction of baskets that contain itemset `X`.

### Support — *how common is this combination?*

> **support(X → Y) = (baskets containing both X and Y) / (total baskets)**

The share of all baskets in which the whole rule appears. Range `0`–`1`.

- **High support** = a frequent, mainstream combination worth acting on.
- **Low support** = a niche pattern; even a strong rule may be too rare to
  matter commercially.
- Example: support `0.026` → the combination shows up in 2.6% of all baskets.
- This is also the knob behind `--min-support`: itemsets below it are discarded
  before rules are even formed.

### Confidence — *how reliable is the rule?*

> **confidence(X → Y) = support(X and Y) / support(X)**

Of the baskets that contain the antecedent `X`, the fraction that *also* contain
the consequent `Y`. Range `0`–`1`; think of it as a conditional probability
`P(Y | X)`.

- Confidence `0.82` for `{Butter} → {Bread}` means **82% of baskets containing
  butter also contain bread**.
- **Caveat:** confidence ignores how popular `Y` is on its own. If almost every
  basket has milk, then `{anything} → {Milk}` will look highly confident just
  because milk is everywhere — not because of a real relationship. That's what
  *lift* corrects for.
- This is the knob behind `--min-confidence`.

### Lift — *is the association real, or just coincidence?*

> **lift(X → Y) = confidence(X → Y) / support(Y)**

How much more likely `Y` is when `X` is present, compared to `Y`'s baseline rate
across all baskets. **This is usually the most useful metric for ranking rules**
(and the column the Results tab is sorted by).

- **lift > 1** → `X` and `Y` appear together *more* than chance: a positive
  association. The higher, the stronger. `lift = 10` means the pair occurs 10×
  more often than if the items were unrelated.
- **lift = 1** → no association; `X` tells you nothing about `Y` (statistically
  independent).
- **lift < 1** → `X` and `Y` appear together *less* than chance: buying one makes
  the other *less* likely (e.g. two substitute brands).

### Reading a row, end to end

| antecedents | consequents | support | confidence | lift |
|-------------|-------------|---------|------------|------|
| Butter, Jam | Bread | 0.026 | 1.000 | 10.83 |

> This combination appears in **2.6%** of baskets (support). **100%** of baskets
> that contain butter *and* jam also contain bread (confidence). And bread is
> **10.8× more likely** to be in those baskets than in an average basket (lift) —
> a strong, real association, not an artifact of bread being popular.

### Turning rules into action

- **Recommendations / "frequently bought together":** high-confidence, high-lift
  rules.
- **Store layout & bundling:** high-support *and* high-lift rules (common enough
  to be worth the shelf space).
- **Cross-sell / promotions:** high-lift rules where the consequent is higher
  margin than the antecedent.
- Always sanity-check **support** before acting — a dazzling lift on a rule that
  occurs in 0.1% of baskets rarely justifies a business change.

> **Note on direction.** `X → Y` and `Y → X` have the *same* support and lift but
> usually *different* confidence, so both directions can appear in the Results
> tab. Pick the direction that matches the decision you're making ("given they
> bought X, recommend Y").

---

## Reference: data schemas

Keep these exact column headers when supplying your own data (Option B).

**`data/products.csv`**

| Column | Example | Notes |
|--------|---------|-------|
| `product_id` | `P001` | Unique. |
| `product_name` | `Bread` | Unique. |
| `category` | `Bakery` | |
| `unit_price` | `2.49` | Number > 0. |

**`data/transactions.csv`** (long format — one row per item per transaction)

| Column | Example | Notes |
|--------|---------|-------|
| `transaction_id` | `T00001` | Groups items into a basket. |
| `date` | `2025-06-13` | Parseable date. |
| `product_id` | `P024` | Must exist in Products. |
| `product_name` | `Bananas` | Must match the catalog for that `product_id`. |
| `category` | `Produce` | Must match the catalog. |
| `quantity` | `2` | Integer > 0. |
| `unit_price` | `1.49` | Must match the catalog price. |
| `line_total` | `2.98` | Must equal `quantity * unit_price`. |

**`data/baskets.csv`** (wide format — one row per transaction)

| Column | Example | Notes |
|--------|---------|-------|
| `transaction_id` | `T00001` | Unique; should match Transactions. |
| `date` | `2025-06-13` | |
| `n_items` | `4` | Must equal the count of items in `items`. |
| `items` | `Bananas, Chicken Breast, Lettuce, Rice` | Comma-separated product names; each must exist in the catalog; no duplicates. |

---

## Troubleshooting

- **`PermissionError` / "file is being used by another process"** — close
  `Market Basket Analysis Demo.xlsx` in Excel before running any script that
  writes to it (`import_to_excel.py`, `validate_data.py`, `analyze.py`,
  `run_analysis.py`). Windows locks open files.
- **`SSLError: CERTIFICATE_VERIFY_FAILED` during `pip install`** — use the
  `--trusted-host` flags shown in the
  [setup section](#1-one-time-setup-create-the-virtual-environment).
- **Analysis was skipped** — `run_analysis.py` only proceeds when validation
  passes. Open the **Data Quality** tab to see which checks failed and the
  example offending rows, fix the source data, re-import, and run again.
- **No rules / no itemsets** — your thresholds are too high for the data. Lower
  `--min-support` and/or `--min-confidence`.
- **Unicode errors when printing to the console** — set
  `$env:PYTHONIOENCODING='utf-8'` in PowerShell before running.

> **Disclaimer** — This software is provided for educational and demonstration purposes only. Use it at your own risk. See the full [Disclaimer & EULA](./DISCLAIMER.md) for details.