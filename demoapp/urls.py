from django.urls import path
from . import views

urlpatterns=[
    path('',views.myfunc,name="index"),
    path('shop',views.shop,name="shop"),
    path('detail',views.detail,name="detail"),
    path('cart',views.cart,name="cart"),
    path('checkout',views.checkout,name="checkout"),
    path('blog',views.blog,name="blog"),
    path('contact',views.contact,name="contact"),
    path('blogdetail',views.blogdetail,name="blogdetail"),
    path('postproduct',views.postproduct,name="postproduct"),
    path('addCategory',views.addCategory,name="addCategory"),
    path('submitCategory',views.submitCategory,name="submitCategory"),
    path('deleteCategory/<int:i>',views.deleteCategory,name="deleteCategory"),
    path('editCategory/<int:i>',views.editCategory,name="editCategory"),
    path('updateCategory/<int:i>',views.updateCategory,name="updateCategory"),
    path('searchCategory',views.searchCategory,name="searchCategory"),
    #posting product
    path('submitProduct',views.submitProduct,name="submitProduct"),
    path('deleteProduct/<int:i>',views.deleteProduct,name="deleteProduct"),
]