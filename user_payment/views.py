# views.py
from datetime import timedelta, datetime
from django.utils import timezone
from .models import Transaction
import stripe
from django.shortcuts import render, redirect, HttpResponse
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY
def handle_plan_selection(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            selected_plan = request.POST.get('selected_plan')
            token = request.POST.get('stripeToken')
            token = 'tok_visa'
            stripe.api_key = settings.STRIPE_SECRET_KEY
            try:
                if selected_plan == 'Standard Plan':
                    plan_price = 2900
                elif selected_plan == 'Pro Plan':
                    plan_price = 5900
                else:
                    raise ValueError('Invalid plan selected')
                
                session = stripe.checkout.Session.create(
                    line_items=[{
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': selected_plan,
                            },
                            'unit_amount': plan_price,
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                
                    success_url=settings.YOUR_DOMAIN +"/handle_plan_selection/success?session_id={CHECKOUT_SESSION_ID}",
                    cancel_url=settings.YOUR_DOMAIN +"/handle_plan_selection/cancel",
                )
                payment_url = session.url
                # print(payment_url)

                return redirect(session.url, code=303)
            except stripe.error.CardError as e:
                error_message = e.error.message
                return render(request, 'error.html', {'error_message': error_message})
            except ValueError as e:
                return render(request, 'error.html', {'error_message': str(e)})
    else:
        return HttpResponse("You must be logged in to complete this transaction.")

def success(request):
    if request.user.is_authenticated:
        user= request.user
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session_id = request.GET.get('session_id')
        session = stripe.checkout.Session.retrieve(session_id)
        payment_intent_id = session['payment_intent']
        amount_received = session['amount_total']
        payment_status = session['payment_status']
        if amount_received==2900:
            selected_plan="Standard Plan"
            transaction_count=10
        elif amount_received==5900:
            selected_plan="Pro Plan"
            transaction_count=50

        # plan_expire_on = datetime.now() + timedelta(days=30)
        plan_expire_on = timezone.now() + timedelta(days=30)
        
        # Store the information in the database
        payment_info = Transaction.objects.create(
            user = request.user,
            username = session['customer_details']['name'],
            email= session['customer_details']['email'],
            amount = amount_received//100,
            payment_intent_id=payment_intent_id,
            payment_status = payment_status,
            address_line1 = session['customer_details']['address']['line1'],
            address_line2 = session['customer_details']['address']['line2'],
            city = session['customer_details']['address']['city'],
            postal_code = session['customer_details']['address']['postal_code'],
            state = session['customer_details']['address']['state'],
            country = session['customer_details']['address']['country'],
            selected_plan = selected_plan,
            plan_expire_on = plan_expire_on,
            transaction_count=transaction_count,
            remaining_transaction = transaction_count
            
        )
        payment_info.save()
        details = {
            'session_id':session_id,
            'amount':amount_received//100,
            'payment_status':payment_status
        }
        return render(request, 'payment_success.html', {'details': details})
    else:
        return HttpResponse("you must be logged in to complete this transaction")

def cancel(request):
    return render(request, 'payment_cancel.html')

# views.py

def view_transactions(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'transactions.html', {'transactions': transactions})


def account(request):
    account = Transaction.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'account.html', {'account': account})