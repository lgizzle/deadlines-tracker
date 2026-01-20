#!/usr/bin/env python
import csv
import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bizops.settings")
django.setup()

from datetime import datetime

from deadlines.models import Deadline, Entity

# Import entities
print("Importing entities...")
with open("../csv-exports/Entities.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        Entity.objects.update_or_create(
            entity_code=row["EntityCode"],
            defaults={
                "legal_name": row.get("LegalName", ""),
                "dba_name": row.get("DBAName", ""),
                "ein": row.get("EIN", ""),
                "status": row.get("Status", "Active"),
                "notes": row.get("Notes") or "",
            },
        )
print(f"✓ {Entity.objects.count()} entities imported")

# Import deadlines
print("Importing deadlines...")
with open("../csv-exports/BusinessDeadlines.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        entity = Entity.objects.filter(entity_code=row["EntityCode"]).first()
        if entity:
            try:
                next_due = datetime.strptime(row["NextDue"], "%Y-%m-%d").date()
            except:
                continue
            Deadline.objects.update_or_create(
                title=row["Title"],
                entity=entity,
                defaults={
                    "category": row.get("Category", "Other"),
                    "frequency": row.get("Frequency", "Monthly"),
                    "next_due": next_due,
                    "due_day": int(row["DueDay"]) if row.get("DueDay") else None,
                    "remind_days_before": int(row.get("RemindDaysBefore", 7)),
                    "autopay": row.get("Autopay", "").upper() == "TRUE",
                    "account_number": row.get("AccountNumber", ""),
                    "estimated_amount": (
                        float(row["EstimatedAmount"].replace(",", ""))
                        if row.get("EstimatedAmount")
                        else None
                    ),
                    "status": row.get("Status", "Active"),
                    "notes": row.get("Notes") or "",
                },
            )
print(f"✓ {Deadline.objects.count()} deadlines imported")
print("\n✓ Import complete!")
