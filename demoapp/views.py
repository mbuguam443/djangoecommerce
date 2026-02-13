from django.shortcuts import render,redirect
from django.http import HttpResponse,JsonResponse



from demoapp.models import Category, Product

# Create your views here.
def myfunc(request):
    mydict={
         "allCategory":Category.objects.all()
    }
    return render(request,'index.html',context=mydict)
def shop(request):
    data = {
    "products": [
        {"id": 1, "name": "Crab Pool Security", "price": 30.00,"image":"img/product/product-1.jpg"},
        {"id": 2, "name": "Crab Pool Security", "price": 40.00,"image":"img/product/product-2.jpg"},
        {"id": 3, "name": "Crab Pool Security", "price": 50.00,"image":"img/product/product-3.jpg"}
               ],
    "allCategory":Category.objects.all()           
          }
         

    return render(request,'shop-grid.html',context=data)
def cart(request):
    mydict={
         "allCategory":Category.objects.all()
    }
    return render(request,'shoping-cart.html',context=mydict)
def detail(request):
    mydict={
         "allCategory":Category.objects.all()
    }
    return render(request,'shop-details.html',context=mydict)
def checkout(request):
    mydict={
         "allCategory":Category.objects.all()
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
         "allCategory":Product.objects.all()
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
