from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('profit-report.csv', views.profit_report_csv, name='profit_report_csv'),
    path('qr/', views.view_qr, name='view_qr'),
    path('scan/', views.scan_qr, name='scan_qr'),
    path('transfer/', views.transfer, name='transfer'),
    path('profit-report.csv', views.profit_report_csv, name='profit_report_csv'),

    # Withdraw is a request for admin approval
    path('withdraw/', views.withdraw, name='withdraw'),
    path('user/', views.user, name='user'),
    path('transactions/', views.transactions, name='transactions'),
    path('requests/', views.requests_view, name='requests'),
    path('requests/<int:req_id>/approve/', views.approve_request, name='approve_request'),
    path('requests/<int:req_id>/reject/', views.reject_request, name='reject_request'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    # Admin-only operations
    path('admin/deposit/', views.admin_deposit, name='admin_deposit'),
    path('admin/withdrawals/', views.admin_withdrawals, name='admin_withdrawals'),
    path('admin/withdrawals/<int:wid>/approve/', views.admin_withdraw_approve, name='admin_withdraw_approve'),
    path('admin/withdrawals/<int:wid>/reject/', views.admin_withdraw_reject, name='admin_withdraw_reject'),
    path('admin/users/add/', views.admin_add_user, name='admin_add_user'),

]
