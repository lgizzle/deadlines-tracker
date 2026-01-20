import csv
from datetime import datetime

from deadlines.models import (
    BankAccount,
    Contact,
    CreditCard,
    Deadline,
    Entity,
    InsurancePolicy,
    License,
    Loan,
)
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Import data from CSV files in csv-exports directory"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv-dir",
            type=str,
            default="../csv-exports",
            help="Directory containing CSV files",
        )

    def handle(self, *args, **options):
        csv_dir = options["csv_dir"]

        self.stdout.write(self.style.SUCCESS("Starting CSV import..."))

        # Import in order of dependencies
        self.import_entities(csv_dir)
        self.import_deadlines(csv_dir)
        self.import_bank_accounts(csv_dir)
        self.import_credit_cards(csv_dir)
        self.import_insurance(csv_dir)
        self.import_licenses(csv_dir)
        self.import_loans(csv_dir)
        self.import_contacts(csv_dir)

        self.stdout.write(self.style.SUCCESS("✓ Import complete!"))

    @transaction.atomic
    def import_entities(self, csv_dir):
        self.stdout.write("Importing entities...")
        file_path = f"{csv_dir}/Entities.csv"

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    Entity.objects.update_or_create(
                        entity_code=row["EntityCode"],
                        defaults={
                            "legal_name": row.get("LegalName", ""),
                            "dba_name": row.get("DBAName", ""),
                            "ein": row.get("EIN", ""),
                            "entity_type": row.get("EntityType", ""),
                            "tax_filing_type": row.get("TaxFilingType", ""),
                            "status": row.get("Status", "Active"),
                            "physical_address": row.get("PhysicalAddress", ""),
                            "physical_city": row.get("PhysicalCity", ""),
                            "physical_state": row.get("PhysicalState", ""),
                            "physical_zip": row.get("PhysicalZip", ""),
                            "mailing_address": row.get("MailingAddress", ""),
                            "business_phone": row.get("BusinessPhone", ""),
                            "website": row.get("Website", ""),
                            "manager_name": row.get("ManagerName", ""),
                            "manager_phone": row.get("ManagerPhone", ""),
                            "manager_email": row.get("ManagerEmail", ""),
                            "sos_number": row.get("SOSNumber", ""),
                            "sos_state": row.get("SOSState", ""),
                            "sos_renewal_date": self.parse_date(
                                row.get("SOSRenewalDate")
                            ),
                            "partnership_splits": row.get("PartnershipSplits", ""),
                            "formation_date": self.parse_date(row.get("FormationDate")),
                            "notes": row.get("Notes") or "",
                        },
                    )
                    count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Imported {count} entities"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f"  ⚠ File not found: {file_path}"))

    @transaction.atomic
    def import_deadlines(self, csv_dir):
        self.stdout.write("Importing deadlines...")
        file_path = f"{csv_dir}/BusinessDeadlines.csv"

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    entity = Entity.objects.filter(
                        entity_code=row["EntityCode"]
                    ).first()
                    if not entity:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ⚠ Entity {row["EntityCode"]} not found for deadline: {row["Title"]}'
                            )
                        )
                        continue

                    Deadline.objects.update_or_create(
                        title=row["Title"],
                        entity=entity,
                        defaults={
                            "category": row.get("Category", "Other"),
                            "frequency": row.get("Frequency", "Monthly"),
                            "next_due": self.parse_date(row.get("NextDue"))
                            or datetime.today().date(),
                            "due_day": (
                                int(row["DueDay"]) if row.get("DueDay") else None
                            ),
                            "remind_days_before": int(row.get("RemindDaysBefore", 7)),
                            "autopay": row.get("Autopay", "").upper() == "TRUE",
                            "account_number": row.get("AccountNumber", ""),
                            "estimated_amount": self.parse_decimal(
                                row.get("EstimatedAmount")
                            ),
                            "status": row.get("Status", "Active"),
                            "notes": row.get("Notes", ""),
                        },
                    )
                    count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Imported {count} deadlines"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f"  ⚠ File not found: {file_path}"))

    @transaction.atomic
    def import_bank_accounts(self, csv_dir):
        self.stdout.write("Importing bank accounts...")
        file_path = f"{csv_dir}/BankAccounts.csv"

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    entity = Entity.objects.filter(
                        entity_code=row["EntityCode"]
                    ).first()
                    if not entity:
                        continue

                    BankAccount.objects.update_or_create(
                        entity=entity,
                        bank_name=row["BankName"],
                        account_number_last4=row.get("AccountNumberLast4", "0000"),
                        defaults={
                            "account_type": row.get("AccountType", ""),
                            "routing_number": row.get("RoutingNumber", ""),
                            "status": row.get("Status", "Active"),
                            "notes": row.get("Notes", ""),
                        },
                    )
                    count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Imported {count} bank accounts")
                )
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f"  ⚠ File not found: {file_path}"))

    @transaction.atomic
    def import_credit_cards(self, csv_dir):
        self.stdout.write("Importing credit cards...")
        file_path = f"{csv_dir}/CreditCards.csv"

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    entity = Entity.objects.filter(
                        entity_code=row.get("EntityCode", "")
                    ).first()
                    if not entity:
                        continue

                    # Handle different CSV formats
                    card_name = row.get("CardName") or row.get("EntityCode", "Unknown")
                    last4 = row.get("Last4") or row.get("CardLast4", "0000")

                    CreditCard.objects.update_or_create(
                        entity=entity,
                        last4=last4,
                        defaults={
                            "card_name": card_name,
                            "network": row.get("Network", ""),
                            "credit_limit": self.parse_decimal(row.get("CreditLimit")),
                            "status": row.get("Status", "Active"),
                            "notes": row.get("Notes") or "",
                        },
                    )
                    count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Imported {count} credit cards")
                )
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f"  ⚠ File not found: {file_path}"))

    @transaction.atomic
    def import_insurance(self, csv_dir):
        self.stdout.write("Importing insurance policies...")
        file_path = f"{csv_dir}/InsurancePolicies.csv"

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    entity = Entity.objects.filter(
                        entity_code=row["EntityCode"]
                    ).first()
                    if not entity:
                        continue

                    InsurancePolicy.objects.update_or_create(
                        entity=entity,
                        policy_number=row["PolicyNumber"],
                        defaults={
                            "policy_type": row.get("PolicyType", ""),
                            "carrier": row.get("Carrier", ""),
                            "coverage_amount": self.parse_decimal(
                                row.get("CoverageAmount")
                            ),
                            "premium_amount": self.parse_decimal(
                                row.get("PremiumAmount")
                            ),
                            "renewal_date": self.parse_date(row.get("RenewalDate")),
                            "status": row.get("Status", "Active"),
                            "notes": row.get("Notes", ""),
                        },
                    )
                    count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Imported {count} insurance policies")
                )
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f"  ⚠ File not found: {file_path}"))

    @transaction.atomic
    def import_licenses(self, csv_dir):
        self.stdout.write("Importing licenses...")
        file_path = f"{csv_dir}/Licenses.csv"

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    entity = Entity.objects.filter(
                        entity_code=row["EntityCode"]
                    ).first()
                    if not entity:
                        continue

                    License.objects.update_or_create(
                        entity=entity,
                        license_number=row["LicenseNumber"],
                        defaults={
                            "license_type": row.get("LicenseType", ""),
                            "issuing_authority": row.get("IssuingAuthority", ""),
                            "issue_date": self.parse_date(row.get("IssueDate")),
                            "expiration_date": self.parse_date(
                                row.get("ExpirationDate")
                            ),
                            "renewal_fee": self.parse_decimal(row.get("RenewalFee")),
                            "status": row.get("Status", "Active"),
                            "notes": row.get("Notes", ""),
                        },
                    )
                    count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Imported {count} licenses"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f"  ⚠ File not found: {file_path}"))

    @transaction.atomic
    def import_loans(self, csv_dir):
        self.stdout.write("Importing loans...")
        file_path = f"{csv_dir}/Loans.csv"

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    entity = Entity.objects.filter(
                        entity_code=row["EntityCode"]
                    ).first()
                    if not entity:
                        continue

                    Loan.objects.update_or_create(
                        entity=entity,
                        account_number=row.get("AccountNumber", ""),
                        lender=row["Lender"],
                        defaults={
                            "loan_type": row.get("LoanType", ""),
                            "original_amount": self.parse_decimal(
                                row.get("OriginalAmount")
                            ),
                            "current_balance": self.parse_decimal(
                                row.get("CurrentBalance")
                            ),
                            "interest_rate": self.parse_decimal(
                                row.get("InterestRate")
                            ),
                            "payment_amount": self.parse_decimal(
                                row.get("PaymentAmount")
                            ),
                            "payment_frequency": row.get("PaymentFrequency", ""),
                            "origination_date": self.parse_date(
                                row.get("OriginationDate")
                            ),
                            "maturity_date": self.parse_date(row.get("MaturityDate")),
                            "status": row.get("Status", "Active"),
                            "notes": row.get("Notes", ""),
                        },
                    )
                    count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Imported {count} loans"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f"  ⚠ File not found: {file_path}"))

    @transaction.atomic
    def import_contacts(self, csv_dir):
        self.stdout.write("Importing contacts...")
        file_path = f"{csv_dir}/Contacts.csv"

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    entity = None
                    if row.get("EntityCode"):
                        entity = Entity.objects.filter(
                            entity_code=row["EntityCode"]
                        ).first()

                    Contact.objects.update_or_create(
                        first_name=row["FirstName"],
                        last_name=row["LastName"],
                        email=row.get("Email", ""),
                        defaults={
                            "entity": entity,
                            "contact_type": row.get("ContactType", "Other"),
                            "company_name": row.get("CompanyName", ""),
                            "title": row.get("Title", ""),
                            "phone": row.get("Phone", ""),
                            "mobile": row.get("Mobile", ""),
                            "address": row.get("Address", ""),
                            "notes": row.get("Notes", ""),
                        },
                    )
                    count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Imported {count} contacts"))
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f"  ⚠ File not found: {file_path}"))

    def parse_date(self, date_str):
        """Parse date string to date object"""
        if not date_str or date_str.strip() == "":
            return None

        # Try different date formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"]:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        return None

    def parse_decimal(self, decimal_str):
        """Parse decimal string to decimal"""
        if not decimal_str or decimal_str.strip() == "":
            return None
        try:
            # Remove currency symbols and commas
            cleaned = decimal_str.replace("$", "").replace(",", "").strip()
            return float(cleaned)
        except ValueError:
            return None
