from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction, models
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
import csv

from .models import Account, Transaction, ProfitRecord, MoneyRequest, WithdrawalRequest
from .forms import TransferForm, WithdrawForm, RequestMoneyForm, AdminUserForm, AdminDepositForm
from .utils import generate_qr_image

def is_admin(user):
    return user.is_superuser

def logout_view(request):
    logout(request)
    return redirect('login')

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')
    
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages

@login_required
def admin_add_user(request):
    if not request.user.is_superuser:
        return redirect('dashboard')  # or wherever normal users go

    users = User.objects.all()
    context = {
        'users': users
    }
    return render(request, 'core/admin_add_users.html', context)

@login_required
def user(request):
    if not request.user.is_superuser:
        return redirect('dashboard')  # or wherever normal users go

    users = User.objects.all()
    context = {
        'users': users
    }
    return render(request, 'core/admin_users.html', context)



@login_required
def admin_users(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return redirect('admin_add_user')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('admin_add_user')

        user = User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, f"User {username} created successfully.")
        return redirect('admin_users')

    return render(request, 'core/admin_add_user.html')




def profit_report_csv(request):
    # Create the HTTP response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="profit_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'User', 'Profit'])

    # Example: loop through transactions and calculate profit
    transactions = Transaction.objects.all()
    for t in transactions:
        writer.writerow([t.date, t.user.username, t.profit])

    return response



@login_required
def admin_delete_user(request, user_id):
    if not request.user.is_superuser:  # only admin can delete
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)

    if user.is_superuser:
        messages.error(request, "You cannot delete the superuser account.")
        return redirect('admin_users')

    user.delete()
    messages.success(request, "User deleted successfully.")
    return redirect('admin_users')


@login_required
def dashboard(request):
    account, _ = Account.objects.get_or_create(user=request.user)
    today = timezone.localdate()
    txs = Transaction.objects.filter(created_at__date=today).order_by('-created_at')[:10]
    pending_withdraw = WithdrawalRequest.objects.filter(user=request.user, status=WithdrawalRequest.PENDING).order_by('-created_at')
    return render(request, 'core/dashboard.html', {
        'account': account,
        'txs': txs,
        'pending_withdraw': pending_withdraw,
    })

@login_required
def view_qr(request):
    account, _ = Account.objects.get_or_create(user=request.user)
    if not account.qr_image:
        path_suffix = f"/account/{account.id}/pay/"
        account.qr_image = generate_qr_image(path_suffix)
        account.save()
    pay_url = f"{settings.QR_BASE_URL}/account/{account.id}/pay/"
    return render(request, 'core/account_qr.html', {'account': account, 'pay_url': pay_url})

@login_required
def scan_qr(request):
    return render(request, 'core/scan.html')

@login_required
def pay_account(request, account_id):
    target = get_object_or_404(Account, id=account_id)
    me = Account.objects.get_or_create(user=request.user)[0]
    if request.method == 'POST':
        action = request.POST.get('action')
        amount = Decimal(request.POST.get('amount','0') or '0')
        note = request.POST.get('note','')
        if amount <= 0:
            messages.error(request, "Invalid amount.")
            return redirect('pay_account', account_id=account_id)
        if action == 'send':
            if me.id == target.id:
                messages.error(request, "Cannot send to self.")
                return redirect('pay_account', account_id=account_id)
            do_transfer(me, target, amount, note)
            messages.success(request, f"Sent Rs.{amount} to {target.user.username}.")
            return redirect('dashboard')
        elif action == 'request':
            MoneyRequest.objects.create(requester=target, target=me, amount=amount, note=note)
            messages.success(request, f"Request of Rs.{amount} sent to {target.user.username}.")
            return redirect('dashboard')
    return render(request, 'core/pay.html', {'target': target})

def fee_amount(amount: Decimal, percent: float):
    return (amount * Decimal(str(percent)) / Decimal('100')).quantize(Decimal('0.01'))

@transaction.atomic
def do_transfer(from_acc: Account, to_acc: Account, amount: Decimal, note: str=''):
    if from_acc.balance < amount:
        raise ValueError("Insufficient funds")
    fee = fee_amount(amount, settings.TRANSFER_FEE_PERCENT)
    total = amount + fee
    if from_acc.balance < total:
        raise ValueError("Insufficient funds for amount + fee.")
    from_acc.balance -= total
    to_acc.balance += amount
    from_acc.save()
    to_acc.save()
    tx = Transaction.objects.create(
        from_account=from_acc, to_account=to_acc, amount=amount, fee=fee, type=Transaction.TRANSFER, note=note
    )
    ProfitRecord.objects.create(transaction=tx, amount=fee)
    return tx

@login_required
def transfer(request):
    account = Account.objects.get_or_create(user=request.user)[0]
    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            to_username = form.cleaned_data['to_username']
            amount = form.cleaned_data['amount']
            note = form.cleaned_data.get('note','')
            try:
                to_user = User.objects.get(username=to_username)
                to_acc = Account.objects.get_or_create(user=to_user)[0]
                do_transfer(account, to_acc, amount, note)
                messages.success(request, f"Transferred Rs.{amount} to {to_username}.")
                return redirect('transactions')
            except User.DoesNotExist:
                messages.error(request, "User not found.")
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = TransferForm()
    return render(request, 'core/transfer.html', {'form': form})

@login_required
def withdraw(request):
    # User creates a withdrawal request (no immediate balance change)
    if request.method == 'POST':
        form = WithdrawForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            note = form.cleaned_data.get('note','')
            WithdrawalRequest.objects.create(user=request.user, amount=amount, note=note)
            messages.success(request, f"Withdrawal request of Rs.{amount} submitted for admin approval.")
            return redirect('dashboard')
    else:
        form = WithdrawForm()
    return render(request, 'core/withdraw.html', {'form': form})

@login_required
def transactions(request):
    account = Account.objects.get_or_create(user=request.user)[0]
    txs = Transaction.objects.filter(from_account=account) | Transaction.objects.filter(to_account=account)
    txs = txs.order_by('-created_at')[:200]
    return render(request, 'core/transactions.html', {'txs': txs})

@login_required
def requests_view(request):
    account = Account.objects.get_or_create(user=request.user)[0]
    incoming = MoneyRequest.objects.filter(target=account).order_by('-created_at')
    outgoing = MoneyRequest.objects.filter(requester=account).order_by('-created_at')
    return render(request, 'core/requests.html', {'incoming': incoming, 'outgoing': outgoing})

@login_required
def approve_request(request, req_id):
    req = get_object_or_404(MoneyRequest, id=req_id)
    if req.target.user != request.user:
        return HttpResponseForbidden("Not allowed.")
    if req.status != MoneyRequest.PENDING:
        messages.info(request, "Request already processed.")
        return redirect('requests')
    try:
        do_transfer(req.target, req.requester, req.amount, note=f"Approve request #{req.id}")
        req.status = MoneyRequest.APPROVED
        req.save()
        messages.success(request, f"Sent Rs.{req.amount} to {req.requester.user.username}.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect('requests')

@login_required
def reject_request(request, req_id):
    req = get_object_or_404(MoneyRequest, id=req_id)
    if req.target.user != request.user:
        return HttpResponseForbidden("Not allowed.")
    if req.status == MoneyRequest.PENDING:
        req.status = MoneyRequest.REJECTED
        req.save()
        messages.success(request, "Request rejected.")
    return redirect('requests')

@user_passes_test(is_admin)
def admin_dashboard(request):
    today = timezone.localdate()
    total_balance = Account.objects.aggregate(total=models.Sum('balance'))['total'] or Decimal('0.00')
    today_profit = ProfitRecord.objects.filter(created_at__date=today).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    txs = Transaction.objects.order_by('-created_at')[:200]
    pending_withdrawals = WithdrawalRequest.objects.filter(status=WithdrawalRequest.PENDING).order_by('-created_at')
    return render(request, 'core/admin_dashboard.html', {
        'total_balance': total_balance,
        'today_profit': today_profit,
        'txs': txs,
        'transfer_fee': settings.TRANSFER_FEE_PERCENT,
        'deposit_fee': settings.DEPOSIT_FEE_PERCENT,
        'withdraw_fee': settings.WITHDRAW_FEE_PERCENT,
        'pending_withdrawals': pending_withdrawals,
    })

@user_passes_test(is_admin)
def admin_deposit(request):
    # Admin deposits into a user's account (fee recorded)
    if request.method == 'POST':
        form = AdminDepositForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            amount = form.cleaned_data['amount']
            note = form.cleaned_data.get('note','')
            try:
                user = User.objects.get(username=username)
                acc = Account.objects.get_or_create(user=user)[0]
                fee = fee_amount(amount, settings.DEPOSIT_FEE_PERCENT)
                acc.balance += (amount - fee)
                acc.save()
                tx = Transaction.objects.create(from_account=None, to_account=acc, amount=amount, fee=fee, type=Transaction.DEPOSIT, note=f"Admin deposit: {note}")
                ProfitRecord.objects.create(transaction=tx, amount=fee)
                messages.success(request, f"Deposited Rs.{amount} (fee Rs.{fee}) to {username}.")
                return redirect('admin_deposit')
            except User.DoesNotExist:
                messages.error(request, "User not found.")
    else:
        form = AdminDepositForm()
    return render(request, 'core/admin_deposit.html', {'form': form})

@user_passes_test(is_admin)
@transaction.atomic
def admin_withdraw_approve(request, wid):
    wr = get_object_or_404(WithdrawalRequest, id=wid)
    if wr.status != WithdrawalRequest.PENDING:
        messages.info(request, "Already processed.")
        return redirect('admin_withdrawals')
    acc = Account.objects.get_or_create(user=wr.user)[0]
    fee = fee_amount(wr.amount, settings.WITHDRAW_FEE_PERCENT)
    total = wr.amount + fee
    if acc.balance < total:
        messages.error(request, "Insufficient user balance for amount + fee.")
        return redirect('admin_withdrawals')
    # Deduct and record transaction
    acc.balance -= total
    acc.save()
    tx = Transaction.objects.create(from_account=acc, to_account=None, amount=wr.amount, fee=fee, type=Transaction.WITHDRAW, note=f"Admin approved withdrawal #{wr.id}")
    ProfitRecord.objects.create(transaction=tx, amount=fee)
    wr.status = WithdrawalRequest.APPROVED
    wr.save()
    messages.success(request, f"Withdrawal of Rs.{wr.amount} approved for {wr.user.username}.")
    return redirect('admin_withdrawals')

@user_passes_test(is_admin)
def admin_withdraw_reject(request, wid):
    wr = get_object_or_404(WithdrawalRequest, id=wid)
    if wr.status == WithdrawalRequest.PENDING:
        wr.status = WithdrawalRequest.REJECTED
        wr.save()
        messages.success(request, "Withdrawal request rejected.")
    return redirect('admin_withdrawals')

@user_passes_test(is_admin)
def admin_withdrawals(request):
    pending = WithdrawalRequest.objects.filter(status=WithdrawalRequest.PENDING).order_by('-created_at')
    processed = WithdrawalRequest.objects.exclude(status=WithdrawalRequest.PENDING).order_by('-created_at')[:200]
    return render(request, 'core/admin_withdrawals.html', {'pending': pending, 'processed': processed})
