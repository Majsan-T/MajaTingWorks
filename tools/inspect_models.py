# inspect_models.py
# List tables and columns in the model

from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    print("\n📋 Tabellen och kolumner i modellen:\n")
    for table in db.metadata.sorted_tables:
        print(f"🗂 Tabell: {table.name}")
        for column in table.columns:
            print(f"   ↳ {column.name} ({column.type})")
        print()

    for column in table.columns:
        flags = []
        if column.primary_key:
            flags.append("PK")
        if not column.nullable:
            flags.append("NOT NULL")
        print(f"   ↳ {column.name} ({column.type}) {' '.join(flags)}")
