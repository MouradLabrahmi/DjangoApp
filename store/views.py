from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder
from django.views.generic import DetailView

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User, auth
from django.contrib import messages

from .forms import CreateUserForm


def store(request):
	data = cartData(request)
	cartItems = data['cartItems']
	
	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}

	return render(request, 'store/store.html', context)


def cart(request):
	data = cartData(request)
	items = data['items']
	order = data['order']
	cartItems = data['cartItems']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

def checkout(request):
	data = cartData(request)
	items = data['items']
	order = data['order']
	cartItems = data['cartItems']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/checkout.html', context)


def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)


# def product(request,id):
# 	product = Product.objects.get(id=id)
# 	print(product)
# 	context = {'product':product}

# 	return render(request, 'store/product.html', context)


def product(request,pk):
	product = Product.objects.get(id = pk)
	data = cartData(request)
	cartItems = data['cartItems']

	context = {'product':product, 'cartItems':cartItems}
	return render(request, "store/product.html",context)



def login(request):
	data = cartData(request)
	cartItems = data['cartItems']

	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')

		user = auth.authenticate(username=username, password = password)
		if user is not None:
			auth.login(request, user)
			return redirect("http://127.0.0.1:8000/")
		else :
			messages.info(request,'les informations sont erronees')
			return render(request,'store/login.html')
	else:
		return render(request,'store/login.html', {'cartItems':cartItems})

def register(request):
	data = cartData(request)
	cartItems = data['cartItems']

	form = CreateUserForm()
	if request.method == 'POST':
		form = CreateUserForm(request.POST)
		if form.is_valid():
			form.save()
			#auth_login(request,user)
			return redirect('/')
	context = {'form':form, 'cartItems':cartItems }
	return render(request,'store/register.html',context)