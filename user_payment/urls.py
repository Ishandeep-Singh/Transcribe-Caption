from django.urls import path
from user_payment.views import handle_plan_selection, success, cancel, view_transactions, account

urlpatterns = [
    path('handle_plan_selection/', handle_plan_selection, name='handle_plan_selection'),
    path('handle_plan_selection/success', success, name='success'),
    path('handle_plan_selection/cancel', cancel, name='cancel'),
    path('transactions', view_transactions, name='transactions'),
    path('account', account, name='account'),
    

]
