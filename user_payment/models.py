# models.py

from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=500, null=False)
    email= models.EmailField(null=False)
    payment_intent_id = models.CharField(max_length=500, null=False)
    selected_plan = models.CharField(max_length=100, null=False)
    amount = models.CharField(max_length=100, null=False)
    payment_status = models.CharField(max_length=200, null=False)
    address_line1 = models.CharField(max_length=500, null=False)
    address_line2 = models.CharField(max_length=500, null=False)
    city = models.CharField(max_length=500, null=False)
    state = models.CharField(max_length=500, null=False)
    country = models.CharField(max_length=500, null=False)
    postal_code = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    plan_expire_on = models.DateTimeField()
    transaction_count = models.IntegerField()
    remaining_transaction = models.IntegerField()


    def __str__(self):
        return f'Transaction ID: {self.id}'
