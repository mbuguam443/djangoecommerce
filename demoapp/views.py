from django.shortcuts import get_object_or_404, render,redirect
from django.http import HttpResponse,JsonResponse
from django.db import transaction
from django.contrib import messages
from .models import Order, OrderItem, Product
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from .forms import CheckoutForm
from django.contrib.auth.decorators import login_required
from .mpesa import stk_push
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import logging

logger = logging.getLogger("mpesa")



from demoapp.models import Category, Product

# Create your views here.
def myfunc(request):
    mydict={
         "allCategory":Category.objects.all()
    }
    return render(request,'index.html',context=mydict)
def shop(request):
    cart = request.session.get('cart', {})
    subtotal = 0
    for item in cart.values():
        subtotal += int(item['quantity']) * float(item['price'])    
    
    data = {
    "products": Product.objects.all(),
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
         "Product":obj
    }
    return render(request,'shop-details.html',context=mydict)
def checkout(request):
    cart = request.session.get('cart', {})
    subtotal = 0
    for item in cart.values():
        subtotal += int(item['quantity']) * float(item['price']) 
    mydict={
         "allCategory":Category.objects.all(),
         "subtotal":subtotal    
    }
    
    return render(request,'checkout.html',context=mydict)
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
def postproduct(request):
    mydict={
         "allCategory":Category.objects.all(),
         "allProduct":Product.objects.all()
    }
    return render(request,'postProduct.html',context=mydict)
def addCategory(request):
    mydict={
         "allCategory":Category.objects.all()
    }
    return render(request,'addCategory.html',context=mydict)
def submitCategory(request):
    category=request.POST['category']
    error=False
    errormessage=""
    success=False
    successmessage=""
    if not category:
        error=True
        errormessage="Category is empty"
    else:
        obj=Category()
        obj.name=category
        obj.save()
        success=True
        successmessage="Category Added successfully"
    
    mydict={
              "error":error,
              "errormessage":errormessage,
              "success":success,
              "successmessage":successmessage,
              "allCategory":Category.objects.all()
           }    
    return render(request,'addCategory.html',context=mydict)
def deleteCategory(request,i):
    obj=Category.objects.get(id=i)
    obj.delete()
    mydict={
         "success":True,
         "successmessage":"Deleted succefully",
         "allCategory":Category.objects.all()
    }
    return render(request,'addCategory.html',context=mydict)
def editCategory(request,i):
    obj=Category.objects.get(id=i)
   
    mydict={
         "Category":obj,
         "allCategory":Category.objects.all()
    }
    return render(request,'addCategory.html',context=mydict)
def updateCategory(request,i):
    category=request.POST['category']
    error=False
    errormessage=""
    success=False
    successmessage=""
    if not category:
        error=True
        errormessage="Category is empty"
    else:
        obj=Category.objects.get(id=i)
        obj.name=category
        obj.save()
        success=True
        successmessage="Category Updated successfully"
    
    mydict={
              "error":error,
              "errormessage":errormessage,
              "success":success,
              "successmessage":successmessage,
              "allCategory":Category.objects.all()
           }    
    return render(request,'addCategory.html',context=mydict)

def searchCategory(request):
    query=request.GET['Categoryname']
    mydict={
              "allCategory":Category.objects.filter(name__contains=query)
           }    
    return render(request,'addCategory.html',context=mydict)
def submitProduct(request):
    obj=Product()
    if request.method=="POST":
        category_id = request.POST['category']
        category = Category.objects.get(id=category_id)
        obj.category=category
        obj.name=request.POST["name"]
        obj.description=request.POST["description"]
        obj.price=request.POST["price"]
        obj.weight=request.POST["weight"]
        obj.stock=request.POST["stock"]
        obj.available=request.POST["available"]
        obj.image=request.FILES["image"]
        obj.save()
    mydict={
         "success":True,
         "successmessage":"Added succefully",
         "allProduct":Product.objects.all()
    }
    return  redirect('postproduct')

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

def editProduct(request,i):
    obj=Product.objects.get(id=i)
   
    mydict={
         "Product":obj,
         "allCategory":Category.objects.all(),
         "allProduct":Product.objects.all()
    }
    return render(request,'postProduct.html',context=mydict)
def updateProduct(request,i):
    obj=Product.objects.get(id=i)
    if request.method=="POST":
        category_id = request.POST['category']
        category = Category.objects.get(id=category_id)
        obj.category=category
        obj.name=request.POST["name"]
        obj.description=request.POST["description"]
        obj.price=request.POST["price"]
        obj.weight=request.POST["weight"]
        obj.stock=request.POST["stock"]
        obj.available=request.POST["available"]
        if 'image' in request.FILES:
            obj.image.delete(save=False)
            obj.image = request.FILES["image"]
        obj.save()
    mydict={
         "success":True,
         "successmessage":"updated succefully",
         "allCategory":Product.objects.all(),
         "allProduct":Product.objects.all()
    }
    return  redirect('postproduct')

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
                user = User.objects.create_user(username=email, email=email, password=password)
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
    return redirect('index')  # Redirect wherever you want

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

@login_required(login_url='index')  # Redirects to homepage if not logged in    
def clientorder(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    for order in orders:
        order.num_items = order.items.count()  # count related OrderItems
    
    mydict={
        'orders':orders
    }
    return render(request,'clientvieworder.html',context=mydict)    

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


