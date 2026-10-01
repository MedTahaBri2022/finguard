import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


# =========================================================
# CONFIG
# =========================================================

N_ROWS = 10_000
SEED = 42

random.seed(SEED)
np.random.seed(SEED)


# =========================================================
# MASTER DATA
# =========================================================

suppliers = [
    "Atlas Distribution",
    "Maroc Supply",
    "Casablanca Trading",
    "Rif Wholesale",
    "Maghreb Import",
    "Sahara Suppliers",
    "Tanger Commerce",
    "Marrakech Supply",
]

customers = [
    "Client Alpha",
    "Client Beta",
    "Client Gamma",
    "Client Delta",
    "Client Omega",
    "Client Atlas",
]

products = [
    ("Laptop", "Technology", 6500),
    ("Monitor", "Technology", 1800),
    ("Printer", "Technology", 2200),
    ("Office Chair", "Furniture", 1200),
    ("Desk", "Furniture", 1800),
    ("Paper", "Office Supplies", 45),
    ("Printer Ink", "Office Supplies", 320),
    ("Storage Box", "Office Supplies", 85),
    ("Keyboard", "Technology", 250),
    ("Mouse", "Technology", 120),
    ("Router", "Technology", 650),
    ("Desk Lamp", "Furniture", 280),
]


# =========================================================
# DATE RANGE
# =========================================================

start_date = datetime(2026, 1, 1)


def random_date():
    return start_date + timedelta(
        days=random.randint(0, 234)
    )


# =========================================================
# GENERATE NORMAL TRANSACTIONS
# =========================================================

rows = []

for i in range(N_ROWS):

    transaction_id = f"TX-{i + 1:06d}"

    date = random_date()

    transaction_type = random.choices(
        ["Purchase", "Sale"],
        weights=[45, 55],
        k=1
    )[0]

    supplier = random.choice(suppliers)
    customer = random.choice(customers)

    product, category, base_price = random.choice(products)

    quantity = random.randint(1, 20)

    # Normal price variation ±5%
    unit_price = round(
        base_price * random.uniform(0.95, 1.05),
        2
    )

    total_amount = round(
        quantity * unit_price,
        2
    )

    # Payment status
    payment_status = random.choices(
        ["Paid", "Pending", "Overdue"],
        weights=[75, 15, 10],
        k=1
    )[0]

    due_date = date + timedelta(
        days=random.choice([15, 30, 45, 60])
    )

    if payment_status == "Paid":

        payment_date = due_date - timedelta(
            days=random.randint(0, 20)
        )

        if payment_date < date:
            payment_date = date + timedelta(
                days=random.randint(1, 15)
            )

    elif payment_status == "Pending":

        payment_date = None

    else:

        payment_date = None

    rows.append({
        "transaction_id": transaction_id,
        "date": date.strftime("%Y-%m-%d"),
        "type": transaction_type,
        "supplier": supplier,
        "customer": customer,
        "product": product,
        "category": category,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_amount": total_amount,
        "payment_status": payment_status,
        "due_date": due_date.strftime("%Y-%m-%d"),
        "payment_date": (
            payment_date.strftime("%Y-%m-%d")
            if payment_date
            else None
        ),
    })


df = pd.DataFrame(rows)


# =========================================================
# 1. DUPLICATE PAYMENTS
# =========================================================

duplicate_indexes = random.sample(
    range(len(df)),
    50
)

for index in duplicate_indexes:

    duplicate = df.iloc[index].copy()

    duplicate["transaction_id"] = (
        duplicate["transaction_id"]
    )

    df = pd.concat(
        [
            df,
            pd.DataFrame([duplicate])
        ],
        ignore_index=True
    )


# =========================================================
# 2. SUPPLIER PRICE INCREASES
# =========================================================

price_anomaly_indexes = random.sample(
    range(len(df)),
    100
)

for index in price_anomaly_indexes:

    old_price = df.loc[index, "unit_price"]

    new_price = round(
        old_price * random.uniform(1.20, 1.50),
        2
    )

    df.loc[index, "unit_price"] = new_price

    df.loc[index, "total_amount"] = round(
        new_price * df.loc[index, "quantity"],
        2
    )


# =========================================================
# 3. UNUSUAL EXPENSES
# =========================================================

unusual_indexes = random.sample(
    range(len(df)),
    50
)

for index in unusual_indexes:

    amount = df.loc[index, "total_amount"]

    new_amount = round(
        amount * random.uniform(5, 12),
        2
    )

    df.loc[index, "total_amount"] = new_amount

    quantity = df.loc[index, "quantity"]

    df.loc[index, "unit_price"] = round(
        new_amount / quantity,
        2
    )


# =========================================================
# 4. OVERDUE INVOICES
# =========================================================

overdue_indexes = random.sample(
    range(len(df)),
    150
)

for index in overdue_indexes:

    df.loc[index, "payment_status"] = "Overdue"

    transaction_date = datetime.strptime(
        df.loc[index, "date"],
        "%Y-%m-%d"
    )

    df.loc[index, "due_date"] = (
        transaction_date - timedelta(
            days=random.randint(10, 90)
        )
    ).strftime("%Y-%m-%d")

    df.loc[index, "payment_date"] = None


# =========================================================
# 5. PAYMENT / REVENUE MISMATCH
# =========================================================

mismatch_indexes = random.sample(
    range(len(df)),
    100
)

df["payment_received"] = df["total_amount"]

for index in mismatch_indexes:

    amount = df.loc[index, "total_amount"]

    received = round(
        amount * random.uniform(0.40, 0.85),
        2
    )

    df.loc[index, "payment_received"] = received


# =========================================================
# SHUFFLE
# =========================================================

df = df.sample(
    frac=1,
    random_state=SEED
).reset_index(drop=True)


# =========================================================
# SAVE
# =========================================================

output_dir = Path(__file__).parent.parent / "data"

output_dir.mkdir(
    parents=True,
    exist_ok=True
)

output_file = output_dir / "business_transactions.csv"

df.to_csv(
    output_file,
    index=False
)


# =========================================================
# SUMMARY
# =========================================================

print("=" * 60)
print("AI BUSINESS WATCHDOG - DATASET GENERATED")
print("=" * 60)

print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")
print(f"File: {output_file}")

print("\nColumns:")
for column in df.columns:
    print(f" - {column}")

print("\nPayment status:")
print(
    df["payment_status"]
    .value_counts()
)

print("\nMissing values:")
print(
    df.isnull()
    .sum()
)

print("\nTotal transaction value:")
print(
    f"{df['total_amount'].sum():,.2f} DH"
)

print("=" * 60)