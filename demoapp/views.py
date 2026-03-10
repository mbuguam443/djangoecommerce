from django.shortcuts import get_object_or_404, render,redirect
from django.http import HttpResponse,JsonResponse
from django.db import transaction
from django.contrib import messages
from .models import Delivery, Order, OrderItem, Product
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from .forms import CategoryForm, CheckoutForm, LoginForm, OrderForm,DeliveryForm
from django.contrib.auth.decorators import login_required
from .mpesa import stk_push
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import logging
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from .forms import ProductForm
from .forms import RegisterForm
from django.db.models import Sum
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings


logger = logging.getLogger("mpesa")



from demoapp.models import Category, Product

# Create your views here.
def myfunc(request):
    mydict={
         "allCategory":Category.objects.filter(products__isnull=False).distinct(),
         "products": Product.objects.all(),
    }
    return render(request,'index.html',context=mydict)
def shop(request):
    cart = request.session.get('cart', {})
    subtotal = 0
    for item in cart.values():
        subtotal += int(item['quantity']) * float(item['price'])    
    
    product_list = Product.objects.all().order_by('-id')

    paginator = Paginator(product_list, 8)  # 8 products per page
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    data = {
    "products": products,
    "allCategory":Category.objects.all(),
    "subtotal":subtotal           
          }
         

    return render(request,'shop-grid.html',context=data)
def cart(request):
    cart = request.session.get('cart', {})
    subtotal = 0
    for item in cart.values():
        subtotal += int(item['quantity']) * float(item['price']) 
    mydict={
         "allCategory":Category.objects.all(),
         "subtotal":subtotal    
    }
    return render(request,'shoping-cart.html',context=mydict)
def detail(request,i):
    obj=Product.objects.get(id=i)
    mydict={
         "allCategory":Category.objects.all(),
         "Product":obj,
         "products": Product.objects.all(),
    }
    return render(request,'shop-details.html',context=mydict)

   
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty")
        return redirect("cart")

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            # Use cleaned_data instead of request.POST
            data = form.cleaned_data
            email = data["email"]
            password = data.get("password")
            user = None

            # Returning user logic
            user = User.objects.filter(email=email).first()
            if user:
                
                if password:
                    user = authenticate(request, username=user.username, password=password)
                    if user is None:
                        messages.error(request, "Incorrect password. Please login.")
                        return redirect("checkout")
                    login(request, user)
                else:
                    messages.error(request, "Password has an issue.")
                    return redirect("checkout")
            else:
                # Create account if password provided
                if password:
                    user = User.objects.create_user(
                        username=email, email=email, password=password, is_staff=False
                    )
                    login(request, user)
                else:
                    messages.error(request, "Enter password to login or create an account")
                    return redirect("checkout")
            # Calculate subtotal
            subtotal = sum(float(item['total']) for item in cart.values())
            
            

            # Create order
            order = Order.objects.create(
                user=user,
                subtotal=subtotal,
                total=subtotal,
                is_paid=False,
                **{field: data[field] for field in form.Meta.fields}
            )
            delivery = Delivery.objects.filter(county__iexact=order.city).first()

            if delivery:
                order.delivery_fee = delivery.delivery_fee
            else:
                order.delivery_fee = 5
            print("City for delivery:")    
            print(order.city.lower())
            order.total = Decimal(order.subtotal) + Decimal(order.delivery_fee)

            # Create OrderItems & update stock
            for key, item in cart.items():
                product = Product.objects.get(id=key)
                if product.stock < item['quantity']:
                    messages.error(request, f"Not enough stock for {product.name}")
                    return redirect("cart")
                product.stock -= item['quantity']
                product.save()
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item['price'],
                    quantity=item['quantity']
                )

            # Payment handling (cash / mpesa)
            if order.payment_method =="pay_on_delivery":
                order.is_paid = False
                order.save()
            elif order.payment_method == "cash":
                order.is_paid = False
                order.save()
            elif order.payment_method == "mpesa":
                if not order.phone.startswith("254"):
                    messages.success(request, "Phone must start with 254 to use mpesa")
                    return redirect('checkout')
                response = stk_push(order.phone, int(order.total), order.id)
                if response.get('ResponseCode') == '0':
                    order.checkout_request_id = response.get("CheckoutRequestID")
                    order.save()
                    messages.success(request, "STK push initiated")
                else:
                    messages.error(request, f"Payment failed. Try again. Response: {response}")
                    return redirect("checkout")

            # Clear cart
            del request.session['cart']
            request.session.modified = True
            send_mail(
            "Order Confirmation",
            f"Hello {order.first_name}, your order has been received. Total: Ksh {order.total}",
            "mystore@gmail.com",
            [order.email],
            fail_silently=False,
            )
            try:
                send_mail(
                    "Order Confirmation",
                   f"Hello {order.first_name}, your order has been received. Total: Ksh {order.total}",
                    settings.EMAIL_HOST_USER,
                    [order.email],
                    fail_silently=True,
                )
                
            except:
                print("Failed to email")
                pass
            return redirect('ordersuccess')

        else:
            # Form errors automatically available in template
            return render(request, "checkout.html", {"form": form})

    else:
        form = OrderForm()
    subtotal = 0
    for item in cart.values():
        subtotal += int(item['quantity']) * float(item['price'])     
    mydict={
         "allCategory":Category.objects.all(),
         "Delivery_list" :Delivery.objects.all(),
         "subtotal":subtotal    
    }    
    return render(request, "checkout.html", context=mydict)
    #cart = request.session.get('cart', {})
    #subtotal = 0
    #for item in cart.values():
    #    subtotal += int(item['quantity']) * float(item['price']) 
    #mydict={
    #     "allCategory":Category.objects.all(),
    #     "subtotal":subtotal    
    #}
    
    #return render(request,'checkout.html',context=mydict)
def blog(request):
    mydict={
         "allCategory":Category.objects.all()
    }
    return render(request,'blog.html',context=mydict)
def blogdetail(request):
    mydict={
         "allCategory":Category.objects.all()
    }
    return render(request,'blog-details.html',context=mydict)
def contact(request):
    mydict={
         "allCategory":Category.objects.all()
    }
    return render(request,'contact.html',context=mydict)

@staff_member_required(login_url='login')  # redirect non-staff users    
def postproduct(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = ProductForm()
    product_list = Product.objects.all()
    paginator = Paginator(product_list, 5)  # 5 items per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)    
    mydict={
         "allCategory":Category.objects.all(),
         "allProduct":page_obj,
         'form': form
    }
    return render(request,'postProduct.html',context=mydict)

@staff_member_required(login_url='login')  # redirect non-staff users
def addCategory(request):
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Posted successfully")
            return redirect('addCategory')
        else:
           messages.success(request, "Posted Failed")

    else:
        form = CategoryForm()
    category_list = Category.objects.all()
    paginator = Paginator(category_list, 4)  # 5 items per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)     
    mydict = {
        'form': form,
        'allCategory': page_obj
    }
    
    return render(request, 'addCategory.html', context=mydict)


    
        
@staff_member_required(login_url='login')  # redirect non-staff users    
def deleteCategory(request,i):
    obj=Category.objects.get(id=i)
    obj.delete()
    messages.success(request, "Deleted successfully")
    return redirect('addCategory')

@staff_member_required(login_url='login')  # redirect non-staff users
def editCategory(request, i):
    obj = Category.objects.get(id=i)

    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Updated successfully")
            return redirect("addCategory")
    else:
        form = CategoryForm(instance=obj)

    category_list = Category.objects.all()
    paginator = Paginator(category_list, 4)  # 5 items per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)     
    mydict = {
        "Category":obj,
        "form": form,
        "allCategory": page_obj
    }

    return render(request, "addCategory.html", context=mydict)

@staff_member_required(login_url='login')  # redirect non-staff users
def searchCategory(request):
    query=request.GET['Categoryname']
    mydict={
              "allCategory":Category.objects.filter(name__contains=query)
           }    
    return render(request,'addCategory.html',context=mydict)

@staff_member_required(login_url='login')  # redirect non-staff users
def deleteProduct(request,i):
    obj=Product.objects.get(id=i)
    obj.image.delete(save=False)  # delete file
    obj.delete()
    mydict={
         "success":True,
         "successmessage":"Deleted succefully",
         "allProduct":Product.objects.all()
    }
    return  redirect('postproduct')

@staff_member_required(login_url='login')  # redirect non-staff users
def editProduct(request,i):
    obj=Product.objects.get(id=i)
    form = ProductForm(request.POST, request.FILES, instance=obj)
    if form.is_valid():
        form.save()  # Updates the existing object
        return redirect('postproduct')
    else:
        print(form.errors)  # Logs validation errors
    mydict={
         "Product":obj,
         "allCategory":Category.objects.all(),
         "allProduct":Product.objects.all()
    }
    return render(request,'postProduct.html',context=mydict)

@staff_member_required(login_url='login')  # redirect non-staff users
def searchProduct(request):
    query=request.GET['searchProduct']
    mydict={
              "allProduct":Product.objects.filter(name__contains=query)
           }    
    return render(request,'postProduct.html',context=mydict)

def AddCart(request):
    #request.session['cart'] = {}
    #request.session.modified = True

    productid=request.POST['productid']
    quantity=request.POST['quantity']
    product=Product.objects.get(id=productid)
    quantity = int(quantity)

    cart = request.session.get('cart', {})

    if str(productid) in cart:
        cart[str(productid)]['quantity'] += quantity
    else:
        cart[str(productid)] = {
            'name': product.name,
            'price': float(product.price),
            'quantity': quantity,
            "image": product.image.url if product.image else "",
            "total":float(product.price)*1
        }
    cart[str(productid)]['total'] = cart[str(productid)]['quantity'] * cart[str(productid)]['price']
    request.session['cart'] = cart
    request.session.modified = True
    mydict={
         "Product":product
    }
    return render(request,'shop-details.html',context=mydict)
    #return redirect(request.META.get('HTTP_REFERER', '/'))

def removeProductCart(request,i):
    cart = request.session.get('cart', {})
    product_id = str(i)
    if product_id in cart:
        del cart[product_id]
    request.session['cart'] = cart
    request.session.modified = True  # important

    return redirect('cart')  # redirect to cart page    
    

def update_cart(request):
    cart = request.session.get('cart', {})
    if request.method == "POST":
        
        
         
        for key,item in cart.items():
            quantity = request.POST.get(f'quantity_{key}')

            if quantity:
                quantity = int(quantity)
                cart[key]['quantity'] = quantity
                cart[key]['total'] = quantity * float(cart[key]['price'])
            
        request.session['cart'] = cart
        request.session.modified = True


    subtotal = 0
    for item in cart.values():
        subtotal += int(item['quantity']) * float(item['price'])    
    mydict={
            "subtotal":subtotal
        }
    

    return render(request, 'shoping-cart.html', context=mydict)
def mpesaapi(request):
    return HttpResponse("Am Mpesa Api guy")

@transaction.atomic
def submitOrder(request):
    if request.method == "POST":
        cart = request.session.get('cart', {})
        if not cart:
            messages.error(request, "Your cart is empty")
            return redirect("cart")

        email = request.POST.get("email")
        password = request.POST.get("password")
        user = None

        # Returning user logic
        if User.objects.filter(email=email).exists():
            if password:
                user = authenticate(request, username=email, password=password)
                if user is None:
                    messages.error(request, "Incorrect password. Please login.")
                    return redirect("checkout")
                login(request, user)
            else:
                messages.error(request, "This email is already registered. Please enter your password.")
                return redirect("checkout")
        else:
            # Create account if password provided
            if password:
                user = User.objects.create_user(username=email, email=email, password=password,is_staff=False)
                
                login(request, user)

        # Calculate subtotal
        subtotal = sum(float(item['total']) for item in cart.values())
        payment_method = request.POST.get("payment_method")
        print("Payment Method")
        print(payment_method)
        if not payment_method:
           messages.error(request, "Select payment method.")
           return redirect("checkout") 

        # Create Order
        order = Order.objects.create(
            user=user,
            first_name=request.POST.get("first_name"),
            last_name=request.POST.get("last_name"),
            email=email,
            phone=request.POST.get("phone"),
            country=request.POST.get("country"),
            address=request.POST.get("address"),
            city=request.POST.get("city"),
            state=request.POST.get("state"),
            zip_code=request.POST.get("zip_code"),
            subtotal=subtotal,
            total=subtotal,
            payment_method=payment_method,
            is_paid=False,  # will update if payment confirmed
        )

        # Create OrderItems
        for key, item in cart.items():
            product = Product.objects.get(id=key)
             # Deduct stock
            quantity = item['quantity']
            print(f"Before: {product.name} stock={product.stock}")
            if product.stock < quantity:
                messages.error(request, f"Not enough stock for {product.name}")
                return redirect("cart")
            product.stock -= quantity
            product.save()
            print(f"After: {product.name} stock={product.stock}")
            OrderItem.objects.create(
                order=order,
                product=product,
                price=item['price'],
                quantity=item['quantity']
            )

        # Handle payment
        if payment_method == "cash":
            order.is_paid = False  # cash payment pending
            order.save()
            # Optionally send email to admin/user
        elif payment_method == "mpesa":
            # Call Mpesa API here
            
            # Redirect to pending/payment page
            phone = order.phone
            amount = int(order.total)
            response = stk_push(phone, amount, order.id)
            if response.get('ResponseCode') == '0':
                checkout_id = response.get("CheckoutRequestID")
                order.checkout_request_id = checkout_id
                order.save()
                messages.success(request, response)
            else:
                messages.error(request, f"STK push failed. Try again. Response: {response}")
                return render(request,'checkout.html')
            
            
        # Clear cart
        del request.session['cart']
        request.session.modified = True

        return redirect('ordersuccess')  # you can create a success page

    return render(request,'checkout.html')

def logoutUser(request):
    logout(request)  # Clears session
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')  # Redirect wherever you want

def testForm(request):
    if request.method == "POST":
        form = CheckoutForm(request.POST)

        if form.is_valid():
            # process order
            messages.success(request, "Order placed successfully!")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CheckoutForm()
    mydict={
        "form": form
         }
    return render(request, "testform.html", context=mydict)

def ordersuccess(request):
    
    return render(request,'OrderSuccess.html')

@login_required(login_url='login')  # Redirects to homepage if not logged in    
def clientorder(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    for order in orders:
        order.num_items = order.items.count()  # count related OrderItems
    
    total_sales = total_sales = orders.filter(
                                    user=request.user,
                                    payment_status="paid"
                                ).aggregate(total_sales=Sum('total'))['total_sales'] or 0
    mydict={
        'orders':orders,
        'total_sales':total_sales
    }
    return render(request,'clientvieworder.html',context=mydict)  
  
@login_required(login_url='login')
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all()  # Related name from OrderItem
    total = 0
    for item in items:
        item.total_price = item.price * item.quantity  # per item total
        total += item.total_price  # accumulate order total
    mydict={
        'order': order,
        'items': items,
        'total':total
        }
    return render(request, 'orderdetails.html',context=mydict)

@csrf_exempt
def mpesa_callback(request):
    if request.method == "POST":
        try:
            raw_body = request.body.decode('utf-8')
            logger.info("MPESA RAW CALLBACK: %s", raw_body)
            print("MPESA RAW CALLBACK:", raw_body)
            data = json.loads(request.body)

            stk_callback = data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc')
            merchant_request_id = stk_callback.get('MerchantRequestID')
            checkout_request_id = stk_callback.get('CheckoutRequestID')

            # If payment was successful
            if result_code == 0:

                callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])

                metadata = {}
                for item in callback_metadata:
                    metadata[item['Name']] = item.get('Value')

                amount = metadata.get('Amount')
                mpesa_receipt = metadata.get('MpesaReceiptNumber')
                phone = metadata.get('PhoneNumber')
                account_reference = metadata.get('AccountReference')

                # Extract order id from AccountReference
                # Example: AccountReference = "Order5"
                checkout_id = stk_callback.get("CheckoutRequestID")

                order = Order.objects.get(checkout_request_id=checkout_id)
    
                order.is_paid = True
                order.payment_status="paid"
                order.payment_reference = metadata.get("MpesaReceiptNumber")
                order.payment_date = timezone.now()
                order.save()

                print("Payment successful for Order:")

            else:
                print("Payment failed:", result_desc)

        except Exception as e:
            print("Callback error:", str(e))

        return JsonResponse({"status": "received"})

    return JsonResponse({"error": "Invalid request"}, status=400)    

@staff_member_required(login_url='login')  # redirect non-staff users
def Allorders(request):
    orders = Order.objects.all().order_by('-created_at')
    for order in orders:
        order.num_items = order.items.count()  # count related OrderItems
    paginator = Paginator(orders, 6)  # Show 10 orders per page

    page_number = request.GET.get('page')  # Get the page number from query params
    page_obj = paginator.get_page(page_number)  # Returns the page object

    total_sales = Order.objects.filter(payment_status="paid").aggregate(total_sales=Sum('total'))['total_sales'] or 0

    mydict={
        'orders':page_obj,
        "total_sales": total_sales
    }
    return render(request,'Allorders.html',context=mydict)  

def Adminorderdetail(request,order_id):
    order = get_object_or_404(Order, id=order_id,)
    items = order.items.all()  # Related name from OrderItem
    total = 0
    for item in items:
        item.total_price = item.price * item.quantity  # per item total
        total += item.total_price  # accumulate order total
    mydict={
        'order': order,
        'items': items,
        'total':total
        }
    return render(request, 'Adminorderdetail.html',context=mydict)

def searchOrder(request):
    query = request.GET.get('query')
    orders = Order.objects.all().order_by('-created_at')
    
    for order in orders:
        order.num_items = order.items.count()  # count related OrderItems

    if query:
        orders = orders.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(created_at__date=query)
        )

    return render(request, 'Allorders.html', {"orders": orders}) 

@staff_member_required(login_url='login')  # redirect non-staff users
def updatePayment(request,id):
    order = Order.objects.get(id=id)

    if request.method == "POST":
        status = request.POST.get("payment_status")
        order.payment_status = status
        if status == "paid":
            order.is_paid=True
        order.save()

    return redirect('Adminorderdetail', order_id=order.id)
    
@staff_member_required(login_url='login')  # redirect non-staff users    
def updateOrderStatus(request,id):
    order = Order.objects.get(id=id)

    if request.method == "POST":
        status = request.POST.get("delivery_status")
        order.delivery_status = status
        order.save()

    return redirect('Adminorderdetail', order_id=order.id)   


def loginUser(request):
    if request.user.is_authenticated:
        return redirect("index")
    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():

        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            if user.is_staff :
                return redirect("Allorders")
            else:
                return redirect("clientorder")
        else:
            messages.success(request, "User Login Failed")
            return redirect('login')       
            
            
    mydict={
        "form": form
        }
    return render(request,'login.html',context=mydict)    

@staff_member_required(login_url='login')  # redirect non-staff users
def createUser(request):
    form = RegisterForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            user = form.save(commit=False)   # don't save yet
            user.is_staff = True             # make user staff
            user.save()                      # now save
            messages.success(request, "User Created successfully")
            return redirect('createUser')
        else:
            form = RegisterForm()
            messages.success(request, "User creation failed")
    mydict={
        "form": form,
        "Allusers":User.objects.all()
        }
    return render(request, "CreateUser.html",context=mydict)

@staff_member_required(login_url='login')  # redirect non-staff users    
def DeliveryCrud(request):
    if request.method == "POST":
        form = DeliveryForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("delivery")

    else:
        form = DeliveryForm()
    deliveries = Delivery.objects.all()
    mydict={"form": form,"deliveries": deliveries}
    return render(request, "delivery.html",context=mydict)

@staff_member_required(login_url='login')  # redirect non-staff users    
def deleteDelivery(request,i):
    obj=Delivery.objects.get(id=i)
    obj.delete()
    messages.success(request, "Deleted successfully")
    return redirect('delivery')    

@staff_member_required(login_url='login')  # redirect non-staff users
def editDelivery(request, i):
    obj = Delivery.objects.get(id=i)
    print(obj)
    if request.method == "POST":
        form = DeliveryForm(request.POST,instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Updated successfully")
            return redirect("delivery")
    else:
        form = DeliveryForm(instance=obj)

    Delivery_list = Delivery.objects.all()
    paginator = Paginator(Delivery_list, 4)  # 5 items per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)   
      
    mydict = {
        "Delivery":obj,
        "form": form,
        "deliveries": page_obj
    }

    return render(request, "delivery.html", context=mydict)
        
@staff_member_required(login_url='login')  # redirect non-staff users
def searchDelivery(request):
    query=request.GET['Deliveryname']
    mydict={
              "deliveries":Delivery.objects.filter(county__contains=query)
           }    
    return render(request,'delivery.html',context=mydict)    