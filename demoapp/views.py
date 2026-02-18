from django.shortcuts import get_object_or_404, render,redirect
from django.http import HttpResponse,JsonResponse



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