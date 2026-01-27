from datetime import date, timedelta

from django.core.validators import MinValueValidator
from django.db import models
from encrypted_model_fields.fields import EncryptedCharField


class Entity(models.Model):
    """Business entities tracked in the system"""

    entity_code = models.CharField(max_length=20, unique=True, primary_key=True)
    legal_name = models.CharField(max_length=200, blank=True)
    dba_name = models.CharField(max_length=200, blank=True, verbose_name="DBA Name")
    ein = models.CharField(max_length=20, blank=True, verbose_name="EIN")

    # Classification
    entity_type = models.CharField(max_length=50, blank=True)
    tax_filing_type = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=100, default="Active")

    # Contact & Location
    physical_address = models.TextField(blank=True)
    physical_city = models.CharField(max_length=100, blank=True)
    physical_state = models.CharField(max_length=2, blank=True)
    physical_zip = models.CharField(max_length=10, blank=True)
    mailing_address = models.TextField(blank=True)
    business_phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)

    # Manager info
    manager_name = models.CharField(max_length=100, blank=True)
    manager_phone = models.CharField(max_length=50, blank=True)
    manager_email = models.EmailField(blank=True)

    # Secretary of State info
    sos_number = models.CharField(max_length=50, blank=True, verbose_name="SOS Number")
    sos_state = models.CharField(max_length=2, blank=True, verbose_name="SOS State")
    sos_renewal_date = models.DateField(
        null=True, blank=True, verbose_name="SOS Renewal Date"
    )

    # Other
    partnership_splits = models.TextField(blank=True)
    formation_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["entity_code"]
        verbose_name_plural = "Entities"

    def __str__(self):
        return f"{self.entity_code} - {self.dba_name or self.legal_name}"


class Deadline(models.Model):
    """Business deadlines and recurring obligations"""

    FREQUENCY_CHOICES = [
        ("Daily", "Daily"),
        ("Weekly", "Weekly"),
        ("Bi-Weekly", "Bi-Weekly"),
        ("Monthly", "Monthly"),
        ("Quarterly", "Quarterly"),
        ("Semi-Annual", "Semi-Annual"),
        ("Annual", "Annual"),
        ("One-Time", "One-Time"),
    ]

    CATEGORY_CHOICES = [
        ("Sales Tax", "Sales Tax"),
        ("Utility", "Utility"),
        ("Insurance", "Insurance"),
        ("License", "License"),
        ("Payroll", "Payroll"),
        ("Tax Filing", "Tax Filing"),
        ("Loan Payment", "Loan Payment"),
        ("Rent/Lease", "Rent/Lease"),
        ("Subscription", "Subscription"),
        ("Compliance", "Compliance"),
        ("Other", "Other"),
    ]

    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Autopay", "Autopay"),
        ("Inactive", "Inactive"),
        ("Suspended", "Suspended"),
    ]

    title = models.CharField(max_length=200)
    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="deadlines"
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)

    # Due date management
    next_due = models.DateField()
    due_day = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Day of month for recurring deadlines",
        null=True,
        blank=True,
    )
    remind_days_before = models.IntegerField(
        default=7,
        validators=[MinValueValidator(0)],
        help_text="Days before due date to send reminder",
    )

    # Payment info
    autopay = models.BooleanField(default=False)
    account_number = models.CharField(max_length=100, blank=True)
    estimated_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="Active")
    notes = models.TextField(blank=True)

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["next_due", "title"]

    def __str__(self):
        return f"{self.title} - {self.entity.entity_code} ({self.next_due})"

    @property
    def is_due_soon(self):
        """Check if deadline is coming up within reminder window"""
        if not self.next_due:
            return False
        today = date.today()
        reminder_date = self.next_due - timedelta(days=self.remind_days_before)
        return today >= reminder_date and today <= self.next_due

    @property
    def is_overdue(self):
        """Check if deadline is past due"""
        return self.next_due < date.today() if self.next_due else False

    @property
    def days_until_due(self):
        """Calculate days until due date"""
        if not self.next_due:
            return None
        return (self.next_due - date.today()).days


class BankAccount(models.Model):
    """Bank accounts for entities"""

    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="bank_accounts"
    )
    bank_name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=50)
    account_number_last4 = models.CharField(
        max_length=4, help_text="Last 4 digits only"
    )
    full_account_number = EncryptedCharField(
        max_length=50, blank=True, help_text="Full account number (encrypted)"
    )
    routing_number = models.CharField(max_length=9, blank=True)
    status = models.CharField(max_length=100, default="Active")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["entity", "bank_name"]

    def __str__(self):
        return f"{self.entity.entity_code} - {self.bank_name} (...{self.account_number_last4})"


class CreditCard(models.Model):
    """Credit cards for entities"""

    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="credit_cards"
    )
    card_name = models.CharField(max_length=100)
    last4 = models.CharField(max_length=4, help_text="Last 4 digits")
    full_card_number = EncryptedCharField(
        max_length=20, blank=True, help_text="Full card number (encrypted)"
    )
    expiration = EncryptedCharField(
        max_length=7, blank=True, help_text="MM/YYYY (encrypted)"
    )
    cvv = EncryptedCharField(
        max_length=4, blank=True, help_text="CVV (encrypted)"
    )
    network = models.CharField(
        max_length=50, blank=True, help_text="Visa, Mastercard, Amex, etc."
    )
    credit_limit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(max_length=100, default="Active")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["entity", "card_name"]

    def __str__(self):
        return f"{self.entity.entity_code} - {self.card_name} (...{self.last4})"


class InsurancePolicy(models.Model):
    """Insurance policies"""

    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="insurance_policies"
    )
    policy_type = models.CharField(max_length=100)
    carrier = models.CharField(max_length=100)
    policy_number = models.CharField(max_length=100)
    coverage_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    premium_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    renewal_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=100, default="Active")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["entity", "policy_type"]
        verbose_name_plural = "Insurance Policies"

    def __str__(self):
        return f"{self.entity.entity_code} - {self.policy_type} ({self.carrier})"


class License(models.Model):
    """Business licenses and permits"""

    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="licenses"
    )
    license_type = models.CharField(max_length=100)
    license_number = models.CharField(max_length=100)
    issuing_authority = models.CharField(max_length=200)
    issue_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    renewal_fee = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(max_length=100, default="Active")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["entity", "license_type"]

    def __str__(self):
        return f"{self.entity.entity_code} - {self.license_type}"


class Loan(models.Model):
    """Loans and financing"""

    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name="loans")
    loan_type = models.CharField(max_length=100)
    lender = models.CharField(max_length=200)
    account_number = models.CharField(max_length=100, blank=True)
    original_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    current_balance = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=3, null=True, blank=True
    )
    payment_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    payment_frequency = models.CharField(max_length=20, blank=True)
    origination_date = models.DateField(null=True, blank=True)
    maturity_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=100, default="Active")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["entity", "loan_type"]

    def __str__(self):
        return f"{self.entity.entity_code} - {self.loan_type} ({self.lender})"


class Contact(models.Model):
    """Business contacts"""

    CONTACT_TYPE_CHOICES = [
        ("Vendor", "Vendor"),
        ("Service Provider", "Service Provider"),
        ("Customer", "Customer"),
        ("Partner", "Partner"),
        ("Employee", "Employee"),
        ("Contractor", "Contractor"),
        ("Other", "Other"),
    ]

    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="contacts", null=True, blank=True
    )
    contact_type = models.CharField(max_length=50, choices=CONTACT_TYPE_CHOICES)
    company_name = models.CharField(max_length=200, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    ssn = EncryptedCharField(
        max_length=11, blank=True, help_text="SSN: XXX-XX-XXXX (encrypted)"
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        name = f"{self.first_name} {self.last_name}"
        if self.company_name:
            name += f" ({self.company_name})"
        return name

    @property
    def ssn_masked(self):
        """Return masked SSN (XXX-XX-1234)"""
        if self.ssn and len(self.ssn) >= 4:
            return f"XXX-XX-{self.ssn[-4:]}"
        return ""

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class StateAccount(models.Model):
    """State-level accounts (unemployment, sales tax, revenue online)"""

    ACCOUNT_TYPE_CHOICES = [
        ("Unemployment Insurance", "Unemployment Insurance"),
        ("Sales Tax", "Sales Tax"),
        ("Revenue Online", "Revenue Online"),
        ("Withholding Tax", "Withholding Tax"),
        ("Other", "Other"),
    ]

    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="state_accounts"
    )
    state = models.CharField(max_length=2, help_text="State abbreviation (e.g., OR, CO)")
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPE_CHOICES)
    account_number = models.CharField(max_length=100, blank=True)
    portal_name = models.CharField(
        max_length=100, blank=True, help_text="e.g., MYUI, Revenue Online"
    )
    portal_url = models.URLField(blank=True)
    login_email = models.EmailField(blank=True, help_text="Login email (not password)")
    status = models.CharField(max_length=100, default="Active")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["entity", "state", "account_type"]
        verbose_name = "State Account"
        verbose_name_plural = "State Accounts"

    def __str__(self):
        return f"{self.entity.entity_code} - {self.state} {self.account_type}"


class MerchantProcessor(models.Model):
    """Card payment processing accounts"""

    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="merchant_processors"
    )
    processor_name = models.CharField(max_length=100, help_text="e.g., Square, Toast, AccessOne")
    merchant_id = models.CharField(max_length=100, blank=True)
    terminal_id = models.CharField(max_length=100, blank=True)
    portal_url = models.URLField(blank=True)
    dba_name = models.CharField(max_length=200, blank=True, verbose_name="DBA Name on Processor")
    status = models.CharField(max_length=100, default="Active")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["entity", "processor_name"]
        verbose_name = "Merchant Processor"
        verbose_name_plural = "Merchant Processors"

    def __str__(self):
        return f"{self.entity.entity_code} - {self.processor_name}"


class Vendor(models.Model):
    """Vendor and supplier accounts"""

    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="vendors"
    )
    vendor_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=100, blank=True)
    service_location = models.TextField(blank=True, help_text="Address where service is provided")
    purpose = models.CharField(max_length=200, blank=True, help_text="What this vendor provides")
    contact_phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    status = models.CharField(max_length=100, default="Active")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["entity", "vendor_name"]

    def __str__(self):
        return f"{self.entity.entity_code} - {self.vendor_name}"
