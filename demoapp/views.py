from datetime import date

from django.shortcuts import get_object_or_404, render,redirect
from django.http import HttpResponse,JsonResponse
from django.db import transaction
from django.contrib import messages
from .models import CustomerProfile, Delivery, DeliveryAgent, Order, OrderItem, Product
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from .forms import CategoryForm, ContactForm, DeliveryAgentForm, LoginForm, OrderForm,DeliveryForm
from django.contrib.auth.decorators import login_required
from .mpesa import send_b2c, stk_push, stk_query
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import logging
from django.db.models import Q, Count, DecimalField, ExpressionWrapper
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from .forms import ProductForm
from .forms import RegisterForm
from django.db.models import Sum
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings
from .models import Favorite, Product
from django.db.models.functions import TruncDay
from django.db.models import F, Sum


logger = logging.getLogger("mpesa")



from demoapp.models import Category, Product

# Create your views here.
def myfunc(request):
    products = Product.objects.all().order_by('-id')

    category = request.GET.get("category")

    if category:
        products = products.filter(category_id=category)
    mydict={
         "allCategory":Category.objects.filter(products__isnull=False).distinct(),
         "products": products,
    }
    return render(request,'index.html',context=mydict)
def shop(request):
    cart = request.session.get('cart', {})
    subtotal = 0
    for item in cart.values():
        subtotal += int(item['quantity']) * float(item['price'])       

    product_list = Product.objects.all().order_by('-id')

    product = request.GET.get("product")
    category = request.GET.get("category")

    if product:
        product_list = product_list.filter(name__icontains=product)

    if category:
        product_list = product_list.filter(category_id=category)

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
    
    profile = None
    
    
    if request.user.is_authenticated:
        profile = CustomerProfile.objects.filter(user=request.user).first()
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            # Use cleaned_data instead of request.POST
            data = form.cleaned_data
            email = data["email"]
            password = data.get("password")
            phone = data["phone"]
            print("FINAL PHONE:", phone)
            user = None

            # Returning user logic
            user = User.objects.filter(email=email).first()
            if user and user.is_staff:
                # Clear cart
                request.session.pop('cart', None)
                request.session.modified = True
                messages.error(request, "Staff are not allowed to checkout. Use POS instead.")
                return redirect("checkout")
            if user:
                
                if password:
                    user = authenticate(request, username=user.username, password=password)
                    if user is None:
                        messages.error(request, "Incorrect password. Please login.")
                        return redirect("checkout")
                    login(request, user)
                #else:
                    #messages.error(request, "Password has an issue.")
                    #return redirect("checkout")
            else:
                # Create account if password provided
                if password:
                    user = User.objects.create_user(
                        username=email, email=email, password=password, is_staff=False
                    )
                    login(request, user)
                
                
            if request.user.is_authenticated:
                profile, created = CustomerProfile.objects.get_or_create(user=request.user)
                profile.first_name = request.POST.get("first_name")
                profile.last_name = request.POST.get("last_name")
                profile.email = request.POST.get("email")
                profile.phone = request.POST.get("phone")
                profile.country = request.POST.get("country")
                profile.address = request.POST.get("address")
                profile.city = request.POST.get("city")
                profile.state = request.POST.get("state")
                profile.zip_code = request.POST.get("zip_code")

                profile.save()        
            # Calculate subtotal
           # ✅ STEP 1: Calculate subtotal (product total)
            subtotal = sum(
                Decimal(str(item['price'])) * item['quantity']
                for item in cart.values()
            )

            # ✅ STEP 2: VAT
            vat_rate = Decimal('0.16')
            vat = subtotal * vat_rate

            # ✅ STEP 3: Delivery fee
            delivery = Delivery.objects.filter(county__iexact=data.get("city")).first()
            delivery_fee = Decimal(delivery.delivery_fee) if delivery else Decimal('5')

            # ✅ STEP 4: FINAL TOTAL
            total = subtotal + vat + delivery_fee
            

            # Create order
            order = Order.objects.create(
                user=user,
                subtotal=subtotal,
                vat=vat,
                delivery_fee=delivery_fee,
                total=total,
                is_paid=False,
                **{field: data[field] for field in form.Meta.fields}
            )
            
            
            
            if order.total <= 0:
                messages.error(request, "Order total must be greater than 0")
                return redirect("cart") 
            # Create OrderItems & update stock
            for key, item in cart.items():
                product = Product.objects.get(id=key)
                if product.stock < item['quantity']:
                    messages.error(request, f"Not enough stock for {product.name} reduce quantity in cart")
                    return redirect("checkout")
                product.stock -= item['quantity']
                product.save()
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item['price'],
                    cost_price=item['cost_price'],
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
                phone = form.cleaned_data["phone"]
                print("Mpesa Order Total") 
                print(order.total)
                response = stk_push(request,phone, int(order.total), order.id)
                if response.get('ResponseCode') == '0':
                    order.checkout_request_id = response.get("CheckoutRequestID")
                    order.save()
                    messages.success(request, "STK push initiated")
                else:
                    messages.error(request, f"Payment failed. Try again. Response: {response}")
                    return redirect("checkout")

            # Clear cart
            request.session.pop('cart', None)
            request.session.modified = True
            try:
                #send_mail(
                #    "Order Confirmation",
                #   f"Hello {order.first_name}, your order has been received. Total: Ksh {order.total}",
                #    settings.EMAIL_HOST_USER,
                #    [order.email],
                #    fail_silently=True,
                #)
                print("sent successfully")
            except Exception as e:
                print("Email error:", e)
            
            return redirect('clientorder')

        else:
            profile=None
            subtotal = sum(float(item['total']) for item in cart.values())
            if request.user.is_authenticated:
                profile = CustomerProfile.objects.filter(user=request.user).first()
            # Form errors automatically available in template
            vat = subtotal * 0.16  # 16% VAT
            grand_total = subtotal + vat

            mydict={
                    "allCategory":Category.objects.all(),
                    "Delivery_list" :Delivery.objects.all(),
                    "profile": profile,
                    "subtotal":subtotal,
                    "vat":vat,
                    "grand_total":grand_total,
                    "form": form    
                }
            return render(request, "checkout.html", context=mydict)

    else:
        form = OrderForm()
    subtotal = 0
    for item in cart.values():
        subtotal += int(item['quantity']) * float(item['price']) 
    vat = subtotal * 0.16  # 16% VAT
    grand_total = subtotal + vat        
    mydict={
         "allCategory":Category.objects.all(),
         "Delivery_list" :Delivery.objects.all(),
         "profile": profile,
         "vat":vat,
         "grand_total":grand_total,
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
def contact_view(request):
    form = ContactForm()

    if request.method == "POST":
        form = ContactForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            message = form.cleaned_data["message"]

            send_mail(
                subject=f"Message from {name}",
                message=message,
                from_email=email,
                recipient_list=["mbuguam443@gmail.com"],  # your email
            )

            return render(request, "contact.html", {
                "form": ContactForm(),
                "success": True
            })

    return render(request, "contact.html", {"form": form})

@staff_member_required(login_url='login')  # redirect non-staff users    
def postproduct(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Posted successfully")
            return redirect('postproduct')
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
            'cost_price':float(product.cost_price),
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
    return redirect('cart')
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



def logoutUser(request):
    logout(request)  # Clears session
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')  # Redirect wherever you want



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

    status = request.GET.get('status')
    query = request.GET.get('query')

    if status:
        orders = orders.filter(payment_status=status)

    if query:
        orders = orders.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(created_at__icontains=query) |
            Q(id__icontains=query)
        )

    for order in orders:
        order.num_items = order.items.count()

    for order in orders:
        print("Order:", order.id, "Delivery:", order.delivery_fee)

        for item in order.items.all():
            print(item.price, item.cost_price, item.quantity)    

    paginator = Paginator(orders, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    
    valid_orders = Order.objects.filter(
        payment_status='paid',
        delivery_status='delivered'
    )

    total_sales = valid_orders.aggregate(
        total_sales=Sum('total')
    )['total_sales'] or 0

    profit = OrderItem.objects.filter(order__in=valid_orders).aggregate(
                    profit=Sum((F('price') - F('cost_price')) * F('quantity'))
                )['profit'] or 0

    total_cost = OrderItem.objects.filter(
                            order__in=valid_orders
                                    ).aggregate(
                                        total_cost=Sum(F('cost_price') * F('quantity'))
                                    )['total_cost'] or 0    
    delivery_total = valid_orders.aggregate(
                            total_delivery=Sum('delivery_fee')
                        )['total_delivery'] or 0 
        


    product_total = OrderItem.objects.filter(
            order__in=valid_orders
        ).aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or 0  
     
    total_vat = valid_orders.aggregate(
                    total_vat=Sum('vat')
                )['total_vat'] or 0

    context = {
        "orders": page_obj,
        "total_sales": total_sales,
        "profit":profit,
        "total_cost":total_cost,
        "delivery_total":delivery_total,
        "total_vat":total_vat,
        "product_total":product_total
    }

    return render(request, "Allorders.html", context)

def Adminorderdetail(request,order_id):
    order = get_object_or_404(Order, id=order_id,)
    items = order.items.all()  # Related name from OrderItem
    total = 0
    for item in items:
        item.total_price = item.price * item.quantity  # per item total
        total += item.total_price  # accumulate order total
    agents = DeliveryAgent.objects.all()    
    mydict={
        'order': order,
        'items': items,
        'total':total,
        'agents':agents
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
        agent_id = request.POST.get('delivery_agent')
        if agent_id:
            agent = DeliveryAgent.objects.get(id=agent_id)
            order.delivery_agent=agent
            order.delivery_status = "delivered"
            order.save()
            messages.success(request, "Assigned agent successfully!")
        else:
            messages.success(request, "Could not find an Agent!")    

    return redirect('Adminorderdetail', order_id=order.id)   


def loginUser(request):
    if request.user.is_authenticated:
        return redirect("index")
    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():

        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
           
        user_obj = User.objects.filter(email=email).first()
        if user_obj is not None:
            user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                login(request, user)
                if user.is_staff :
                    return redirect("Allorders")
                else:
                    return redirect("clientorder")
            else:
                messages.success(request, "User Login Failed")
                return redirect('login')
        else:
                messages.success(request, "User Login Failed")
                return redirect('login')           
            
            
    mydict={
        "form": form
        }
    return render(request,'login.html',context=mydict)    

#staff_member_required(login_url='login')  # redirect non-staff users
def createUser(request):
    form = RegisterForm(request.POST)
    if request.method == "POST":
        
        if form.is_valid():
            user = form.save(commit=False)   # don't save yet
            user.is_staff = True             # make user staff
            if User.objects.filter(email=user.email).exists():
                messages.error(request, "Email already exists")
                return redirect("createUser")
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

@login_required
def toggle_favorite(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    fav = Favorite.objects.filter(user=request.user, product=product)

    if fav.exists():
        fav.delete()
    else:
        Favorite.objects.create(user=request.user, product=product)

    return redirect(request.META.get('HTTP_REFERER'))     

@staff_member_required(login_url='login')  # redirect non-staff users
def pos(request):
    cart = request.session.get('poscart', {})
    subtotal = 0
    for item in cart.values():
        subtotal += int(item['quantity']) * float(item['price']) 

    orders = Order.objects.all().order_by('-created_at')

    
    query = date.today()


    orders = orders.filter(created_at__date=query)

    orders = orders.annotate(num_items=Count('items'))

    paginator = Paginator(orders, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    for order in orders:
        print("Order:", order.id, "Delivery:", order.delivery_fee)

        for item in order.items.all():
            print(item.price, item.cost_price, item.quantity)
 
    total_sales = orders.aggregate(
                total_sales=Sum('total')
                    )['total_sales'] or 0

    stats = OrderItem.objects.filter(order__in=orders).aggregate(
                        total_cost=Sum(F('cost_price') * F('quantity')),
                        profit=Sum((F('price') - F('cost_price')) * F('quantity'))
                    )

    delivery_total = orders.aggregate(
                            total_delivery=Sum('delivery_fee')
                        )['total_delivery'] or 0 

    total_cost = stats['total_cost'] or 0
    profit = stats['profit'] or 0 
    vat = subtotal * 0.16
    grand_total = subtotal + vat
    mydict = {
        "orders": page_obj,
        "total_sales": total_sales,
        "profit":profit,
        "total_cost":total_cost,
        "subtotal":subtotal,
        "vat":vat,
        "grand_total":grand_total,
        "delivery_total":delivery_total
    }
    return render(request,'pos.html',context=mydict)
@staff_member_required(login_url='login')  # redirect non-staff users
def AddPosCart(request):
    

    productname=request.POST['searchProduct']
    
    try:
        product = Product.objects.get(name=productname)
        cart = request.session.get('poscart', {})

        if str(product.id) in cart:
            cart[str(product.id)]['quantity'] += 1
        else:
        
            cart[str(product.id)] = {
                    'name': product.name,
                    'price': float(product.price),
                    'cost_price':float(product.cost_price),
                    'quantity': 1,
                    "image": product.image.url if product.image else "",
                    "total":float(product.price)*1
            }
        cart[str(product.id)]['total'] = cart[str(product.id)]['quantity'] * cart[str(product.id)]['price']
        request.session['poscart'] = cart
        request.session.modified = True

    except Product.DoesNotExist:
        product = None
        messages.success(request, "Product Not Found")
    

    
   
    return redirect('pos')
    #return redirect(request.META.get('HTTP_REFERER', '/'))
@staff_member_required(login_url='login')  # redirect non-staff users
def removePosProductCart(request,i):
    cart = request.session.get('poscart', {})
    product_id = str(i)
    if product_id in cart:
        del cart[product_id]
    request.session['poscart'] = cart
    request.session.modified = True  # important

    return redirect('pos')  # redirect to cart page    

def update_poscart(request):
    cart = request.session.get('poscart', {})
    if request.method == "POST":
        
        
         
        for key,item in cart.items():
            quantity = request.POST.get(f'quantity_{key}')

            if quantity:
                quantity = int(quantity)
                cart[key]['quantity'] = quantity
                cart[key]['total'] = quantity * float(cart[key]['price'])
            
        request.session['poscart'] = cart
        request.session.modified = True  

    return redirect('pos')    
        
@staff_member_required(login_url='login')  # redirect non-staff users
def pos_checkout(request):
    cart = request.session.get('poscart', {})
    if not cart:
        messages.error(request, "Your cart is empty")
        return redirect("pos")
    
    if request.method == "POST":
               
            # Calculate subtotal
            # ✅ STEP 1: Subtotal (product only)
            subtotal = sum(
                Decimal(str(item['price'])) * item['quantity']
                for item in cart.values()
            )

            # ✅ STEP 2: VAT
            vat_rate = Decimal('0.16')
            vat = subtotal * vat_rate

            # ✅ STEP 3: Delivery (POS = usually 0)
            delivery_fee = Decimal('0')

            # ✅ STEP 4: Final total
            total = subtotal + vat + delivery_fee
            # Create order
            if request.POST.get("payment_method") == "mpesa" and not request.POST.get("phone").startswith("254"):
                   messages.error(request, "Phone has to start with 254")
                   return redirect("pos")
            order = Order.objects.create(
                subtotal=subtotal,
                vat=vat,
                delivery_fee=delivery_fee,
                total=total,
                payment_method=request.POST.get("payment_method"),
                payment_status="pending",
                delivery_status="pending",
                is_paid=False,
                is_pos=True
            )
            
            # Create OrderItems & update stock
            for key, item in cart.items():
                product = Product.objects.get(id=key)
                if product.stock < item['quantity']:
                    messages.error(request, f"Not enough stock for {product.name} reduce quantity in cart")
                    return redirect("pos")
                product.stock -= item['quantity']
                product.save()
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item['price'],
                    cost_price=item['cost_price'],
                    quantity=item['quantity']
                )

            if order.payment_method == "cash":
                order.payment_status = "paid"
                order.delivery_status = "delivered"
                order.is_paid = True
                order.save()
                messages.success(request, "Posted Successfully")
                request.session.pop('poscart', None)
                request.session.modified = True
                return redirect('receipt')
            elif order.payment_method == "mpesa":
                order.phone=request.POST.get("phone")
                if not order.phone.startswith("254"):
                    messages.success(request, "Phone must start with 254 to use mpesa")
                    return redirect('pos')
                response = stk_push(request,order.phone, int(order.total), order.id)
                if response.get('ResponseCode') == '0':
                    order.checkout_request_id = response.get("CheckoutRequestID")
                    order.delivery_status = "delivered"
                    order.save()
                    messages.success(request, "STK push initiated please enter pin to pay")
                    request.session.pop('poscart', None)
                    request.session.modified = True
                    return redirect('receipt')
                else:
                    messages.error(request, f"Payment failed. Try again. Response: {response}")
                    return redirect("pos")

            # Clear cart
            request.session.pop('poscart', None)
            request.session.modified = True
            try:
                #send_mail(
                #    "Order Confirmation",
                #   f"Hello {order.first_name}, your order has been received. Total: Ksh {order.total}",
                #    settings.EMAIL_HOST_USER,
                #    [order.email],
                #    fail_silently=True,
                #)
                print("sent successfully")
            except Exception as e:
                print("Email error:", e)
            
            return redirect('pos')
    subtotal = 0
    for item in cart.values():
        subtotal += int(item['quantity']) * float(item['price'])     
     
    return redirect('pos')    

def receipt(request):
    order = Order.objects.order_by("-created_at").first()  

    context = {
        "order": order
    }
    return render(request,'receipt.html',context)    

def sales_data(request):

    sales = (
        Order.objects
        .filter(payment_status='paid', delivery_status='delivered')  # ✅ FILTER HERE
        .annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(total=Sum('total'))
        .order_by('day')
    )

    labels = []
    data = []

    for s in sales:
        labels.append(s["day"].strftime("%d %b"))
        data.append(float(s["total"]))

    return JsonResponse({
        "labels": labels,
        "data": data
    })    

def dashboard(request):
    return render(request,'dashboard.html')    



def confirmPayment(request,checkid):
    result = stk_query(checkid)
    code = result.get("ResultCode")
    order = Order.objects.get(checkout_request_id=checkid)
    
    if code == "0":
        order.payment_status = "paid"

    elif code == "1032":
        order.payment_status = "failed"

    elif code == "1037":
        order.payment_status = "pending"

    else:
        order.payment_status = "pending"

    order.save()
    messages.success(request, result)
    return redirect('Adminorderdetail',order.id)

def refund_order(request, order_id):

    order = Order.objects.get(id=order_id)

    phone = order.phone
    amount = int(order.total)

    response = send_b2c(phone, amount)

    order.refund_status = True
    order.save()

    return JsonResponse(response)

@csrf_exempt
def b2c_result(request):

    data = json.loads(request.body)

    print("B2C RESULT")
    print(data)

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})


@csrf_exempt
def b2c_timeout(request):

    data = json.loads(request.body)

    print("B2C TIMEOUT")
    print(data)

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Timeout received"})   

def addBlog(request):
    return render(request,'addBlog.html')    
 
def addVAT(request):
    return render(request,'addVAT.html')
def signup(request):
    form = RegisterForm(request.POST)
    if request.method == "POST":
        
        if form.is_valid():
            user = form.save(commit=False)   # don't save yet
            user.is_staff = False             # make user staff
            if User.objects.filter(email=user.email).exists():
                messages.error(request, "Email already exists")
                return redirect("signup")
            user.save()                      # now save
            messages.success(request, "User Created successfully")
            return redirect('signup')
        else:
            form = RegisterForm()
            messages.success(request, "User creation failed")
    mydict={
        "form": form,
        "Allusers":User.objects.all()
        }
    return render(request, "register.html",context=mydict)

def retrypaying(request, order_id):
    order = Order.objects.get(id=order_id)

    response = stk_push(request,order.phone, int(order.total), order.id)
    if response.get('ResponseCode') == '0':
        order.checkout_request_id = response.get("CheckoutRequestID")
        order.save()
        messages.success(request, "STK push initiated")
    else:
        messages.error(request, f"Payment failed. Try again. Response: {response}")

    return redirect("order_detail", order_id=order.id)
 
    
def addAgent(request):
    if request.method == "POST":
        form = DeliveryAgentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Saved successfully")
            return redirect('addAgent')  # change to your URL
        else:
            messages.success(request, "Failed successfully")
            return redirect('addAgent')  # change to your URL
    else:
        
        form = DeliveryAgentForm()
    agents = DeliveryAgent.objects.all()

    return render(request,'addAgent.html', {'form': form,'agents': agents})

def delete_Agent(request, id):
    agent = get_object_or_404(DeliveryAgent, id=id)
    agent.delete()
    messages.success(request, "Deleted successfully")
    return redirect('addAgent')
def edit_Agent(request, id):
    agent = get_object_or_404(DeliveryAgent, id=id)

    if request.method == "POST":
        form = DeliveryAgentForm(request.POST, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, "updated successfully")
            return redirect('addAgent')  # change if needed
        else:
            messages.success(request, "failed to save")
    else:
        form = DeliveryAgentForm(instance=agent)
    agents = DeliveryAgent.objects.all()
    return render(request, 'addAgent.html', {'form': form,'agent':agent,'agents': agents})

def cancel_order_logic(order, cancelled_by=None):
    # Prevent cancelling twice
    if order.delivery_status == 'cancelled':
        return False

    # Only allow cancellation before delivery
    if order.delivery_status in ['shipped', 'delivered']:
        return False
    # ❌ CUSTOMER cannot cancel paid orders
    if cancelled_by == 'customer' and order.payment_status == 'paid':
        return False
    
    # Mark as cancelled
    order.delivery_status = 'cancelled'

    # Handle payment
    #if order.payment_status == 'paid':
        #order.payment_status = 'refunded'
        # ✅ ADMIN REFUND ONLY
    if cancelled_by == 'admin' and order.payment_status == 'paid':
        order.payment_status = 'refunded'
        print("Refund triggered ✅")
    # Restore stock ONLY ONCE
    if not order.stock_restored:
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

        order.stock_restored = True

    order.save()
    return True
@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    success = cancel_order_logic(order, cancelled_by='customer')

    if success:
        messages.success(request, "Order cancelled")
    else:
        messages.error(request, "Cannot cancel this order")

    return redirect('clientorder')
@staff_member_required
def admin_cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    success = cancel_order_logic(order, cancelled_by='admin')

    if success:
        messages.success(request, "Order cancelled by admin")
    else:
        messages.error(request, "Cannot cancel")

    return redirect('Allorders')

