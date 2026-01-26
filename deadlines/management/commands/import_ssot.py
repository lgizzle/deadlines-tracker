"""
Import data from SSOT markdown files.

SSOT files location: /Users/lesgutches/Library/CloudStorage/OneDrive-NGBSolutions/00_ssot/reference/

This command parses markdown files and creates/updates:
- Entity records (from entity-codes.md)
- Deadline records for insurance renewals
- Deadline records for license expirations
- Deadline records for loan payments
- Deadline records for property taxes
"""

import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from deadlines.models import Deadline, Entity, InsurancePolicy, License, Loan


# SSOT file paths
SSOT_BASE = Path(
    "/Users/lesgutches/Library/CloudStorage/OneDrive-NGBSolutions/00_ssot/reference"
)

# Entity definitions with codes matching entity-codes.md
ENTITY_DEFINITIONS = {
    "TIMBER": {
        "legal_name": "Timberhill Sports LLC",
        "dba_name": "Timberhill Athletic Club",
        "entity_type": "LLC",
        "physical_address": "2855 NW 29th St",
        "physical_city": "Corvallis",
        "physical_state": "OR",
        "physical_zip": "97330-3516",
        "business_phone": "(541) 757-8559",
    },
    "CHEERS": {
        "legal_name": "Victory Spirits LLC",
        "dba_name": "Cheers Liquor Mart",
        "entity_type": "LLC",
        "physical_address": "1105 N Circle Dr",
        "physical_city": "Colorado Springs",
        "physical_state": "CO",
        "physical_zip": "80909-3134",
        "business_phone": "(719) 574-2244",
        "website": "https://www.cheersliquormart.com/",
    },
    "GXM": {
        "legal_name": "GXM LLC",
        "dba_name": "G3 Sports & Fitness",
        "entity_type": "LLC",
        "physical_address": "5520 NW Highway 99 W",
        "physical_city": "Corvallis",
        "physical_state": "OR",
        "physical_zip": "97330",
        "business_phone": "(541) 207-3508",
    },
    "PATLIQ": {
        "legal_name": "BG Capital LLC",
        "dba_name": "Patriots Liquor",
        "entity_type": "LLC",
        "physical_address": "7935 Constitution Ave #140",
        "physical_city": "Colorado Springs",
        "physical_state": "CO",
        "physical_zip": "80951",
        "business_phone": "(719) 574-2050",
    },
    "NWNINTH": {
        "legal_name": "NW Ninth LLC",
        "dba_name": "",
        "entity_type": "LLC",
        "physical_address": "2200 NW 9th St",
        "physical_city": "Corvallis",
        "physical_state": "OR",
        "physical_zip": "97330",
    },
    "FIRS": {
        "legal_name": "Firs Housing LLC",
        "dba_name": "The Firs Apartments",
        "entity_type": "LLC",
        "physical_address": "4788 Skyline Rd S",
        "physical_city": "Salem",
        "physical_state": "OR",
        "physical_zip": "97306",
    },
    "FOURWEST": {
        "legal_name": "Four West LLC",
        "dba_name": "Bensons Properties",
        "entity_type": "LLC",
        "physical_address": "544 SW 4th St",
        "physical_city": "Corvallis",
        "physical_state": "OR",
        "physical_zip": "97330",
    },
    "NC1105": {
        "legal_name": "1105 North Circle LLC",
        "dba_name": "",
        "entity_type": "LLC",
        "physical_address": "1105 N Circle Dr",
        "physical_city": "Colorado Springs",
        "physical_state": "CO",
        "physical_zip": "80909",
    },
    "HUCKBERRY": {
        "legal_name": "Huckberry LLC",
        "dba_name": "",
        "entity_type": "LLC",
    },
    "NGB": {
        "legal_name": "NGB Solutions Consulting",
        "dba_name": "",
        "entity_type": "Sole Proprietorship",
    },
    "PERSONAL": {
        "legal_name": "Personal",
        "dba_name": "",
        "entity_type": "Personal",
        "status": "Active",
    },
}

# Map entity names in SSOT files to entity codes
# Order matters for partial matching - more specific names first
ENTITY_NAME_TO_CODE = {
    # Specific matches first (longer names)
    "four west llc (bensons)": "FOURWEST",
    "four west llc": "FOURWEST",
    "four west": "FOURWEST",
    "bensons": "FOURWEST",
    "timberhill sports llc": "TIMBER",
    "timberhill sports": "TIMBER",
    "timberhill": "TIMBER",
    "victory spirits llc": "CHEERS",
    "victory spirits": "CHEERS",
    "cheers": "CHEERS",
    "gxm llc": "GXM",
    "gxm": "GXM",
    "g3 sports": "GXM",
    "patriots liquor": "PATLIQ",
    "patriots": "PATLIQ",
    "bg capital llc": "PATLIQ",
    "bg capital": "PATLIQ",
    "nw ninth llc": "NWNINTH",
    "nw ninth": "NWNINTH",
    "new ninth st": "NWNINTH",
    "new ninth": "NWNINTH",
    "firs housing llc": "FIRS",
    "firs housing": "FIRS",
    "firs": "FIRS",
    "1105 north circle llc": "NC1105",
    "1105 north circle": "NC1105",
    "north circle": "NC1105",
    "castle pines": "PERSONAL",
    "orchard": "PERSONAL",
    "huckberry": "HUCKBERRY",
    "huckberry llc": "HUCKBERRY",
    "huckberry": "HUCKBERRY",
    "huckberry llc": "HUCKBERRY",
}


class Command(BaseCommand):
    help = "Import data from SSOT markdown files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without making changes",
        )
        parser.add_argument(
            "--entities-only",
            action="store_true",
            help="Only import entity records",
        )

    def handle(self, *args, **options):
        self.dry_run = options["dry_run"]
        self.entities_only = options["entities_only"]
        self.stats = {
            "entities_created": 0,
            "entities_updated": 0,
            "deadlines_created": 0,
            "deadlines_updated": 0,
            "insurance_created": 0,
            "licenses_created": 0,
            "loans_created": 0,
        }

        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))
            self.stdout.write("")

        # Import entities first (required for foreign keys)
        self.import_entities()

        if not self.entities_only:
            # Import deadline data from SSOT files
            self.import_insurance_deadlines()
            self.import_license_deadlines()
            self.import_loan_deadlines()
            self.import_property_tax_deadlines()

        # Print summary
        self.print_summary()

    @transaction.atomic
    def import_entities(self):
        """Import entities from entity definitions."""
        self.stdout.write(self.style.MIGRATE_HEADING("Importing entities..."))

        for code, data in ENTITY_DEFINITIONS.items():
            if self.dry_run:
                self.stdout.write(f"  Would create/update entity: {code}")
                self.stats["entities_created"] += 1
                continue

            entity, created = Entity.objects.update_or_create(
                entity_code=code,
                defaults={
                    "legal_name": data.get("legal_name", ""),
                    "dba_name": data.get("dba_name", ""),
                    "entity_type": data.get("entity_type", ""),
                    "physical_address": data.get("physical_address", ""),
                    "physical_city": data.get("physical_city", ""),
                    "physical_state": data.get("physical_state", ""),
                    "physical_zip": data.get("physical_zip", ""),
                    "business_phone": data.get("business_phone", ""),
                    "website": data.get("website", ""),
                    "status": data.get("status", "Active"),
                },
            )

            if created:
                self.stats["entities_created"] += 1
                self.stdout.write(self.style.SUCCESS(f"  Created: {code}"))
            else:
                self.stats["entities_updated"] += 1
                self.stdout.write(f"  Updated: {code}")

    def import_insurance_deadlines(self):
        """Parse insurance-renewals.md and create deadline records."""
        self.stdout.write(self.style.MIGRATE_HEADING("Importing insurance deadlines..."))

        file_path = SSOT_BASE / "insurance-renewals.md"
        if not file_path.exists():
            self.stdout.write(
                self.style.WARNING(f"  File not found: {file_path}")
            )
            return

        content = file_path.read_text()
        current_entity = None

        # Parse sections by entity
        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Match entity headers like "## Cheers (Victory Spirits LLC)"
            entity_match = re.match(r"^##\s+(.+?)(?:\s*\(|$)", line)
            if entity_match:
                entity_name = entity_match.group(1).strip().lower()
                current_entity = self._resolve_entity_code(entity_name)
                continue

            # Match insurance sections like "### General Liability & Property"
            section_match = re.match(r"^###\s+(.+)", line)
            if section_match and current_entity:
                policy_type = section_match.group(1).strip()

                # Look ahead for details
                details = self._extract_bullet_details(lines, i + 1)

                if details.get("effective") or details.get("renewal"):
                    self._create_insurance_deadline(
                        current_entity, policy_type, details
                    )

    def import_license_deadlines(self):
        """Parse licenses-permits.md and create deadline records."""
        self.stdout.write(self.style.MIGRATE_HEADING("Importing license deadlines..."))

        file_path = SSOT_BASE / "licenses-permits.md"
        if not file_path.exists():
            self.stdout.write(
                self.style.WARNING(f"  File not found: {file_path}")
            )
            return

        content = file_path.read_text()
        current_entity = None

        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Match entity headers like "## Cheers (Victory Spirits LLC)"
            entity_match = re.match(r"^##\s+(.+?)(?:\s*\(|$)", line)
            if entity_match:
                entity_name = entity_match.group(1).strip().lower()
                current_entity = self._resolve_entity_code(entity_name)
                continue

            # Match license sections like "### Colorado Sales Tax License"
            section_match = re.match(r"^###\s+(.+)", line)
            if section_match and current_entity:
                license_type = section_match.group(1).strip()

                # Look ahead for details
                details = self._extract_bullet_details(lines, i + 1)

                if details.get("expiration"):
                    self._create_license_deadline(
                        current_entity, license_type, details
                    )

    def import_loan_deadlines(self):
        """Parse loans-mortgages.md and create deadline records."""
        self.stdout.write(self.style.MIGRATE_HEADING("Importing loan deadlines..."))

        file_path = SSOT_BASE / "loans-mortgages.md"
        if not file_path.exists():
            self.stdout.write(
                self.style.WARNING(f"  File not found: {file_path}")
            )
            return

        content = file_path.read_text()
        lines = content.split("\n")

        current_section = None
        in_active_loans = False
        in_sba_loans = False

        for line in lines:
            # Track current section
            if line.startswith("## "):
                section_name = line[3:].strip().lower()
                in_active_loans = "active loans" in section_name
                in_sba_loans = "sba" in section_name or "eidl" in section_name
                continue

            # Skip non-loan sections (Tax Filing, Entity Addresses, Notes, etc.)
            if line.startswith("## "):
                in_active_loans = False
                in_sba_loans = False
                continue

            # Parse Active Loans table
            # | Property/Entity | Loan Number | Monthly Payment | Lender |
            if in_active_loans and line.startswith("|"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 5:  # Empty + 4 columns + maybe empty
                    entity_name = parts[1]
                    loan_number = parts[2]
                    payment_str = parts[3]
                    lender = parts[4] if len(parts) > 4 else ""

                    # Skip header and separator rows
                    if "Property" in entity_name or "---" in entity_name:
                        continue
                    if not entity_name or not loan_number:
                        continue

                    entity_code = self._resolve_entity_code(entity_name.lower())
                    if not entity_code:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Skipping unrecognized entity: {entity_name}"
                            )
                        )
                        continue

                    # Parse payment amount (remove $ and commas)
                    payment = self._parse_amount(payment_str)

                    self._create_loan_deadline(
                        entity_code,
                        loan_number,
                        payment,
                        lender or "Unknown",
                    )

            # Parse SBA Disaster Loans table
            # | Entity | SBA Loan Number | Principal | Monthly Payment | First Payment |
            if in_sba_loans and line.startswith("|"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 6:  # Empty + 5 columns + maybe empty
                    entity_name = parts[1]
                    loan_number = parts[2]
                    payment_str = parts[4]  # Monthly Payment is column 4

                    # Skip header and separator rows
                    if "Entity" in entity_name or "---" in entity_name:
                        continue
                    if not entity_name or not loan_number:
                        continue

                    entity_code = self._resolve_entity_code(entity_name.lower())
                    if not entity_code:
                        continue

                    payment = self._parse_amount(payment_str)

                    self._create_loan_deadline(
                        entity_code,
                        loan_number,
                        payment,
                        "SBA (EIDL)",
                    )

    def import_property_tax_deadlines(self):
        """Parse property-taxes.md and create deadline records."""
        self.stdout.write(
            self.style.MIGRATE_HEADING("Importing property tax deadlines...")
        )

        file_path = SSOT_BASE / "property-taxes.md"
        if not file_path.exists():
            self.stdout.write(
                self.style.WARNING(f"  File not found: {file_path}")
            )
            return

        content = file_path.read_text()
        current_entity = None
        current_region = None

        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Match region headers like "### Oregon - Benton County"
            region_match = re.match(r"^###\s+(.+)", line)
            if region_match:
                current_region = region_match.group(1).strip()
                continue

            # Match entity headers like "#### NW Ninth LLC"
            entity_match = re.match(r"^####\s+(.+?)(?:\s*\(|$)", line)
            if entity_match:
                entity_name = entity_match.group(1).strip().lower()
                current_entity = self._resolve_entity_code(entity_name)
                continue

            # Match table rows for tax accounts
            # | Account # | Description | Situs Address | Notes |
            table_match = re.match(
                r"\|\s*(\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]*)\s*\|\s*([^|]*)\s*\|",
                line,
            )
            if table_match and current_entity:
                account_num = table_match.group(1).strip()
                description = table_match.group(2).strip()

                self._create_property_tax_deadline(
                    current_entity,
                    account_num,
                    description,
                    current_region or "Unknown",
                )

    def _resolve_entity_code(self, name):
        """Resolve entity name to entity code."""
        name_lower = name.lower().strip()

        # Direct lookup
        if name_lower in ENTITY_NAME_TO_CODE:
            return ENTITY_NAME_TO_CODE[name_lower]

        # Partial match
        for key, code in ENTITY_NAME_TO_CODE.items():
            if key in name_lower or name_lower in key:
                return code

        return None

    def _extract_bullet_details(self, lines, start_idx):
        """Extract key-value pairs from bullet list."""
        details = {}

        for i in range(start_idx, min(start_idx + 20, len(lines))):
            line = lines[i].strip()

            # Stop at next section or empty line after content
            if line.startswith("#") or (not line and details):
                break

            # Parse bullet points like "- **Key**: Value"
            match = re.match(r"^-\s+\*\*([^*]+)\*\*:?\s*(.+)?", line)
            if match:
                key = match.group(1).strip().lower()
                value = match.group(2).strip() if match.group(2) else ""

                # Normalize keys
                if "effective" in key:
                    details["effective"] = value
                elif "expiration" in key or "expires" in key:
                    details["expiration"] = value
                elif "renewal" in key:
                    details["renewal"] = value
                elif "premium" in key:
                    details["premium"] = value
                elif "carrier" in key:
                    details["carrier"] = value
                elif "policy" in key and "#" in key:
                    details["policy_number"] = value
                elif "license" in key and "number" in key:
                    details["license_number"] = value
                elif "issuing" in key:
                    details["issuing_authority"] = value

        return details

    def _parse_date(self, date_str):
        """Parse date string to date object."""
        if not date_str:
            return None

        # Try to extract date from strings like "February 6, 2025 - February 6, 2026"
        # We want the end date (renewal date)
        if " - " in date_str:
            date_str = date_str.split(" - ")[-1].strip()

        # Try various formats
        formats = [
            "%B %d, %Y",  # February 6, 2025
            "%Y-%m-%d",  # 2025-02-06
            "%m/%d/%Y",  # 02/06/2025
            "%B %Y",  # February 2025 (use 1st of month)
            "%B, %Y",  # February, 2025
            "%B %d %Y",  # February 6 2025
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        # Try to extract just month/year
        month_year = re.search(
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*(\d{4})",
            date_str,
            re.IGNORECASE,
        )
        if month_year:
            try:
                return datetime.strptime(
                    f"{month_year.group(1)} 1, {month_year.group(2)}", "%B %d, %Y"
                ).date()
            except ValueError:
                pass

        return None

    def _parse_amount(self, amount_str):
        """Parse amount string to Decimal."""
        if not amount_str:
            return None

        # Remove currency symbols and commas
        cleaned = re.sub(r"[^\d.]", "", amount_str)
        try:
            return Decimal(cleaned)
        except Exception:
            return None

    def _create_insurance_deadline(self, entity_code, policy_type, details):
        """Create insurance renewal deadline."""
        entity = self._get_entity(entity_code)
        if not entity:
            return

        # Get renewal date from effective period or renewal field
        renewal_date = self._parse_date(
            details.get("effective") or details.get("renewal")
        )

        title = f"{policy_type} Renewal"

        if self.dry_run:
            self.stdout.write(
                f"  Would create deadline: {entity_code} - {title} ({renewal_date})"
            )
            self.stats["deadlines_created"] += 1
            return

        deadline, created = Deadline.objects.update_or_create(
            title=title,
            entity=entity,
            defaults={
                "category": "Insurance",
                "frequency": "Annual",
                "next_due": renewal_date or datetime.today().date(),
                "remind_days_before": 30,
                "status": "Active",
                "notes": f"Carrier: {details.get('carrier', 'Unknown')}",
            },
        )

        if created:
            self.stats["deadlines_created"] += 1
            self.stdout.write(self.style.SUCCESS(f"  Created: {title} ({entity_code})"))
        else:
            self.stats["deadlines_updated"] += 1
            self.stdout.write(f"  Updated: {title} ({entity_code})")

        # Also create InsurancePolicy record
        if details.get("policy_number"):
            InsurancePolicy.objects.update_or_create(
                entity=entity,
                policy_number=details["policy_number"],
                defaults={
                    "policy_type": policy_type,
                    "carrier": details.get("carrier", ""),
                    "premium_amount": self._parse_amount(details.get("premium")),
                    "renewal_date": renewal_date,
                    "status": "Active",
                },
            )
            self.stats["insurance_created"] += 1

    def _create_license_deadline(self, entity_code, license_type, details):
        """Create license expiration deadline."""
        entity = self._get_entity(entity_code)
        if not entity:
            return

        expiration_date = self._parse_date(details.get("expiration"))
        title = f"{license_type} Expiration"

        if self.dry_run:
            self.stdout.write(
                f"  Would create deadline: {entity_code} - {title} ({expiration_date})"
            )
            self.stats["deadlines_created"] += 1
            return

        deadline, created = Deadline.objects.update_or_create(
            title=title,
            entity=entity,
            defaults={
                "category": "License",
                "frequency": "Annual",
                "next_due": expiration_date or datetime.today().date(),
                "remind_days_before": 60,
                "status": "Active",
                "notes": f"Authority: {details.get('issuing_authority', 'Unknown')}",
            },
        )

        if created:
            self.stats["deadlines_created"] += 1
            self.stdout.write(self.style.SUCCESS(f"  Created: {title} ({entity_code})"))
        else:
            self.stats["deadlines_updated"] += 1
            self.stdout.write(f"  Updated: {title} ({entity_code})")

        # Also create License record
        if details.get("license_number"):
            License.objects.update_or_create(
                entity=entity,
                license_number=details["license_number"],
                defaults={
                    "license_type": license_type,
                    "issuing_authority": details.get("issuing_authority", ""),
                    "expiration_date": expiration_date,
                    "status": "Active",
                },
            )
            self.stats["licenses_created"] += 1

    def _create_loan_deadline(self, entity_code, loan_number, payment, lender):
        """Create loan payment deadline."""
        entity = self._get_entity(entity_code)
        if not entity:
            return

        title = f"Loan Payment - {lender}"

        if self.dry_run:
            self.stdout.write(
                f"  Would create deadline: {entity_code} - {title} (${payment})"
            )
            self.stats["deadlines_created"] += 1
            return

        # Loan payments are typically monthly, due around the 1st
        from datetime import date

        today = date.today()
        next_month = today.replace(day=1)
        if today.day > 1:
            if today.month == 12:
                next_month = today.replace(year=today.year + 1, month=1, day=1)
            else:
                next_month = today.replace(month=today.month + 1, day=1)

        deadline, created = Deadline.objects.update_or_create(
            title=title,
            entity=entity,
            defaults={
                "category": "Loan Payment",
                "frequency": "Monthly",
                "next_due": next_month,
                "due_day": 1,
                "remind_days_before": 5,
                "estimated_amount": payment,
                "account_number": loan_number if loan_number != "*Pending*" else "",
                "status": "Active",
                "notes": f"Lender: {lender}",
            },
        )

        if created:
            self.stats["deadlines_created"] += 1
            self.stdout.write(self.style.SUCCESS(f"  Created: {title} ({entity_code})"))
        else:
            self.stats["deadlines_updated"] += 1
            self.stdout.write(f"  Updated: {title} ({entity_code})")

        # Also create Loan record
        if loan_number and loan_number != "*Pending*":
            Loan.objects.update_or_create(
                entity=entity,
                account_number=loan_number,
                lender=lender,
                defaults={
                    "loan_type": "Business Loan" if "SBA" not in lender else "SBA EIDL",
                    "payment_amount": payment,
                    "payment_frequency": "Monthly",
                    "status": "Active",
                },
            )
            self.stats["loans_created"] += 1

    def _create_property_tax_deadline(
        self, entity_code, account_num, description, region
    ):
        """Create property tax deadline."""
        entity = self._get_entity(entity_code)
        if not entity:
            return

        title = f"Property Tax - {description}"

        if self.dry_run:
            self.stdout.write(
                f"  Would create deadline: {entity_code} - {title} (Acct: {account_num})"
            )
            self.stats["deadlines_created"] += 1
            return

        # Oregon property taxes due November 15
        # Colorado varies by county
        from datetime import date

        today = date.today()
        if "Oregon" in region:
            # Oregon due November 15
            due_date = date(today.year, 11, 15)
            if today > due_date:
                due_date = date(today.year + 1, 11, 15)
        else:
            # Default to April 30 for other states
            due_date = date(today.year, 4, 30)
            if today > due_date:
                due_date = date(today.year + 1, 4, 30)

        deadline, created = Deadline.objects.update_or_create(
            title=title,
            entity=entity,
            account_number=account_num,
            defaults={
                "category": "Tax Filing",
                "frequency": "Annual",
                "next_due": due_date,
                "remind_days_before": 30,
                "status": "Active",
                "notes": f"Region: {region}",
            },
        )

        if created:
            self.stats["deadlines_created"] += 1
            self.stdout.write(self.style.SUCCESS(f"  Created: {title} ({entity_code})"))
        else:
            self.stats["deadlines_updated"] += 1
            self.stdout.write(f"  Updated: {title} ({entity_code})")

    def _get_entity(self, entity_code):
        """Get entity by code, creating if necessary in dry run mode."""
        if self.dry_run:
            return True  # Return truthy value for dry run

        try:
            return Entity.objects.get(entity_code=entity_code)
        except Entity.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f"  Entity not found: {entity_code}")
            )
            return None

    def print_summary(self):
        """Print import summary."""
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Import Summary"))
        self.stdout.write(
            f"  Entities created: {self.stats['entities_created']}"
        )
        self.stdout.write(
            f"  Entities updated: {self.stats['entities_updated']}"
        )
        self.stdout.write(
            f"  Deadlines created: {self.stats['deadlines_created']}"
        )
        self.stdout.write(
            f"  Deadlines updated: {self.stats['deadlines_updated']}"
        )

        if not self.dry_run:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("Import complete!"))
        else:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING("DRY RUN complete - no changes were made")
            )
