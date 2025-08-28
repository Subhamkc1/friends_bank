from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    qr_image = models.ImageField(upload_to='qrcodes/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - Rs. {self.balance}"

class Transaction(models.Model):
    TRANSFER = 'transfer'
    DEPOSIT = 'deposit'
    WITHDRAW = 'withdraw'
    TYPES = [
        (TRANSFER, 'Transfer'),
        (DEPOSIT, 'Deposit'),
        (WITHDRAW, 'Withdraw'),
    ]
    from_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing')
    to_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    type = models.CharField(max_length=10, choices=TYPES)
    created_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return f"{self.type} Rs.{self.amount} (fee Rs.{self.fee})"

class ProfitRecord(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='profit_record')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Profit Rs.{self.amount} on {self.transaction_id}"

class MoneyRequest(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUSES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    requester = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='requests_made')
    target = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='requests_received')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    status = models.CharField(max_length=10, choices=STATUSES, default=PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return f"Req Rs.{self.amount} {self.requester} -> {self.target} ({self.status})"

class WithdrawalRequest(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUSES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    status = models.CharField(max_length=10, choices=STATUSES, default=PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return f"Withdrawal Rs.{self.amount} by {self.user.username} ({self.status})"
