from django.contrib import admin
from .models import Account, Transaction, ProfitRecord, MoneyRequest

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user','balance')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('type','from_account','to_account','amount','fee','created_at')

@admin.register(ProfitRecord)
class ProfitRecordAdmin(admin.ModelAdmin):
    list_display = ('transaction','amount','created_at')

@admin.register(MoneyRequest)
class MoneyRequestAdmin(admin.ModelAdmin):
    list_display = ('requester','target','amount','status','created_at')
