from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from .models import Product, Review, Profile, CartItem, Notification
from .forms import ProductForm, ReviewForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from collections import Counter
import plotly.express as px
import json
import plotly
from plotly.offline import plot
import plotly.graph_objs as go
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import never_cache
import random
import string

import logging

logger = logging.getLogger(__name__)

def my_view(request):
    logger.debug('User object in request: %s', request.user)
    # Your view logic here

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if Profile.objects.get(user=user).is_farmer:
                return redirect('farmer_home')
            else:
                return redirect('product_list')
        else:
            error_message = "Invalid username or password. Please try again."
            return render(request, 'login.html', {'error_message': error_message})
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))    
    return render(request, 'login.html', {'random_string': random_string})


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        fullname = request.POST['fullname']
        mail = request.POST['mail']
        phone_number = request.POST['phonenumber']
        is_farmer = request.POST.get('is_farmer')  # Assuming a checkbox or similar input in the form
        
        if is_farmer is not None:
            f = True
        else:
            f = False
        user = User.objects.create_user(username=username, password=password)
        Profile.objects.create(user=user, is_farmer=f, fullname=fullname, mail=mail, phone_number=phone_number)
        
        # Automatically log in the user after registration
        login(request, user)
        
        if is_farmer:
            return redirect('user_login')
        else:
            return redirect('user_login')
    return render(request, 'register.html')

def product_list(request):
    products = Product.objects.all()
    profile=Profile.objects.get(user=request.user)
    return render(request, 'product_list.html', {'products': products, 'customer_name': profile})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product)
    customers = []
    for review in reviews:
        profile = Profile.objects.get(user=review.user)
        customers.append({
            'customer_name': profile.fullname,
        })
    review_customer_pairs = zip(reviews, customers)
    return render(request, 'product_detail.html', {'product': product, 'review_customer_pairs': review_customer_pairs})

def farmer_home(request):
    return render(request, 'farmer_home.html')

@login_required
def farmer_report(request):
    products = Product.objects.filter(farmer=request.user)
    total_owe = 0
    ordered_products = products.filter(cartitem__is_ordered=True)

    product_counts = Counter(ordered_products.values_list('name', flat=True))
    product_details = []

    for product_name, count in product_counts.items():
        product = products.get(name=product_name)
        total_owe += product.price * count
        product_details.append({'product': product, 'product_name': product.name, 'count': count, 'total_amount': product.price * count})
    notifications = Notification.objects.filter(user=request.user)

    # graph for prducts sold and amount earned
    product_names = [product_detail['product_name'] for product_detail in product_details]
    total_earned = [product_detail['total_amount'] for product_detail in product_details]

     # Creating scatter plot
    trace = go.Scatter(
        x=product_names,
        y=total_earned,
        mode='markers',
        marker=dict(
            color='rgb(55, 83, 109)',
            size=12,
            line=dict(
                color='white',
                width=0.5
            )
        ),
        name='Products Sold'
    )

    # Layout for the scatter plot
    layout = go.Layout(
        title='Products Sold',
        xaxis=dict(title='Product Name'),
        yaxis=dict(title='Amount Earned in Dollars $'),
        showlegend=True
    )
    fig = go.Figure(data=[trace], layout=layout)

    # Create the scatter plot
    chart_div = plot(fig, output_type='div', include_plotlyjs=False, show_link=False)

    # Data for scatter plot: actual quantity available and quantity sold
    products_sold = [product_detail['count'] for product_detail in product_details]

    actual_product_quantities = {}

# Iterate through products and add their quantities to the dictionary
    for product in products:
        product_name = product.name
        product_quantity = product.quantity
        
        # Check if the product name exists in product_details
        # If it does, add the quantities together
        if any(product_name == pd['product'].name for pd in product_details):
            for pd in product_details:
                if product_name == pd['product'].name:
                    product_quantity += pd['count']
        
        # Store the total quantity in the dictionary
        actual_product_quantities[product_name] = product_quantity

    product_names_quantity = list(actual_product_quantities.keys())
    actual_quantity_available = list(actual_product_quantities.values()) 

    actual_product_sold_quantities = {}

    #sold product quantities
    for product in products:
        product_name = product.name
        product_quantity = product.quantity
        
        # Check if the product name exists in product_details
        # If it does, add the quantities together
        sum=0
        if any(product_name == pd['product'].name for pd in product_details):
            for pd in product_details:
                if product_name == pd['product'].name:
                    sum += pd['count']
                    
        actual_product_sold_quantities[product_name] = sum

    actual_sold_quantity = list(actual_product_sold_quantities.values())     
         


    trace1 = go.Bar(
        x=product_names_quantity,
        y=actual_quantity_available,
        name='Actual Quantity Available',
        marker=dict(color='rgb(55, 83, 109)'),
    )

    trace2 = go.Bar(
        x=product_names_quantity,
        y=actual_sold_quantity,
        name='Quantity Sold',
        marker=dict(color='rgb(255, 127, 14)'),
    )

    layout = go.Layout(
        barmode='group',  # This stacks the bars
        title='Product Quantity Overview',
        xaxis=dict(title='Product Name'),
        yaxis=dict(title='Quantity'),
        showlegend=True
    )
    fig = go.Figure(data=[trace1, trace2], layout=layout)
    bar_chart_div = plot(fig, output_type='div', include_plotlyjs=False, show_link=False)



    #total_owe = products.annotate(total_amount=Sum(F('quantity') * F('price'))).values('total_amount')[0]['total_amount'] or 0
    return render(request, 'farmer_home.html', {'products': products, 'total_owe': total_owe, 'product_details': product_details, 'notifications': notifications, 'bar_chart_div': bar_chart_div, 'scatter_chart_div': chart_div})


@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.farmer = request.user
            product.save()
            return redirect('farmer_home')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.profile = profile
            review.save()
            return redirect('product_list')
    else:
        form = ReviewForm()
    return render(request, 'add_review.html', {'form': form, 'product': product})

@csrf_protect
def add_to_cart(request, product_id):
    product = Product.objects.get(pk=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product, is_ordered=False)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('product_list')  # Redirect to your product list page

def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user, is_ordered=False)
    total_price = sum(item.total_price() for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

def order_history(request):
    cart_items = CartItem.objects.filter(user=request.user, is_ordered=True)
    total_price = sum(item.total_price() for item in cart_items)
    return render(request, 'order_history.html', {'cart_items': cart_items, 'total_price': total_price})

@csrf_protect
@transaction.atomic
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def checkout(request):
    if request.method == 'POST':
        # Get the current user's cart items
        cart_items = CartItem.objects.filter(user=request.user, is_ordered=False)

        # Perform any payment processing or order processing logic here

        # Mark cart items as ordered
        for cart_item in cart_items:
            cart_item.is_ordered = True
            product = cart_item.product
            farmer = product.farmer
            if product.quantity > 1:
                product.quantity -= 1
                product.save()
            elif product.quantity == 1:
                product.quantity -= 1
                product.save()
                # Notify the farmer that the product is out of stock
                Notification.objects.create(user=farmer, product=product, message=f"Out of stock: {product.name} is no longer available. Please Add {product.name} Products")
            cart_item.save()

        # Redirect to a thank you page or order summary page
      # Assuming you have an 'order_confirmation' URL pattern

    return render(request, 'checkout.html')



def customer_report(request):
    # Retrieve products sold by the farmer where is_ordered is true
    products = Product.objects.filter(farmer=request.user)

    # Retrieve customer details associated with the sold products
    customers = []
    for product in products:
        cart_items = CartItem.objects.filter(product=product, is_ordered=True)
        for cart_item in cart_items:
            profile = Profile.objects.get(user=cart_item.user)
            customers.append({
                'product_name': product.name,
                'customer_name': profile.fullname,
                'customer_email': profile.mail,
                'customer_mobile_number': profile.phone_number,
                'product_image': product.image.url
            })

    context = {
        'customers': customers,
    }

    return render(request, 'customer_report.html', context)

@csrf_protect
def customer_individual_report(request, product_id):
    # Retrieve products sold by the farmer where is_ordered is true
    product = Product.objects.get(pk=product_id, farmer=request.user)
    cart_items = CartItem.objects.filter(product=product, is_ordered=True)
    customers = []
    for cart_item in cart_items:
            profile = Profile.objects.get(user=cart_item.user)
            customers.append({
                'customer_name': profile.fullname,
                'customer_email': profile.mail,
                'customer_mobile_number': profile.phone_number,
                'product_image': product.image.url
            })
    return render(request, 'customer_individual_report.html', {'customers': customers, 'product': product} )