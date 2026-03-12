from django.urls import path
from . import views

urlpatterns=[
    path('',views.myfunc,name="index"),
    path('shop',views.shop,name="shop"),
    path('detail/<int:i>',views.detail,name="detail"),
    path('cart',views.cart,name="cart"),
    path('checkout',views.checkout,name="checkout"),
    path('blog',views.blog,name="blog"),
    path('contact',views.contact,name="contact"),
    path('blogdetail',views.blogdetail,name="blogdetail"),
    path('postproduct',views.postproduct,name="postproduct"),
    path('addCategory',views.addCategory,name="addCategory"),
    path('deleteCategory/<int:i>',views.deleteCategory,name="deleteCategory"),
    path('editCategory/<int:i>',views.editCategory,name="editCategory"),
    path('searchCategory',views.searchCategory,name="searchCategory"),
    #posting product
    
    path('deleteProduct/<int:i>',views.deleteProduct,name="deleteProduct"),
    path('editProduct/<int:i>',views.editProduct,name="editProduct"),
   
    path('searchProduct',views.searchProduct,name="searchProduct"),
    #add to cart
    path('AddCart',views.AddCart,name="AddCart"),
    path('removeProductCart/<int:i>',views.removeProductCart,name="removeProductCart"),
    path('update-cart', views.update_cart, name='update_cart'),
    #Test Mpesa
    path('mpesaapi', views.mpesaapi, name='mpesaapi'),
    #submit checkout
    path('submitOrder',views.submitOrder,name="submitOrder"),
    #Order Submitted successfully
    path('logout',views.logoutUser,name="logout"),
    path('testForm',views.testForm,name="testForm"),
    path('clientorder',views.clientorder,name="clientorder"),
    path('my-orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('ordersuccess',views.ordersuccess,name="ordersuccess"),
    path("callback", views.mpesa_callback, name="mpesa_callback"),
    #AdminOrders
    path("Allorders",views.Allorders,name="Allorders"),
    path("Adminorderdetail/<int:order_id>/",views.Adminorderdetail,name="Adminorderdetail"),
    path("searchOrder",views.searchOrder,name="searchOrder"),
    path("updatePayment/<int:id>/",views.updatePayment,name="updatePayment"),
    path("updateOrderStatus/<int:id>/",views.updateOrderStatus,name="updateOrderStatus"),
    path("login",views.loginUser,name="login"),
    path("createUser",views.createUser,name="createUser"),
    path("delivery",views.DeliveryCrud,name="delivery"),
    path('deleteDelivery/<int:i>',views.deleteDelivery,name="deleteDelivery"),
    path('searchDelivery',views.searchDelivery,name="searchDelivery"),
    path('editDelivery/<int:i>',views.editDelivery,name="editDelivery"),
    path("favorite/<int:product_id>/", views.toggle_favorite, name="favorite"),
    #pos implementation
    path("pos",views.pos,name="pos"),
    path("AddPosCart",views.AddPosCart,name="AddPosCart"),
    #removePosProductCart
    path('removePosProductCart/<int:i>',views.removePosProductCart,name="removePosProductCart"),
    #update_poscart
    path('update_poscart', views.update_poscart, name='update_poscart'),
    #pos_checkout
    path('pos_checkout',views.pos_checkout,name="pos_checkout"),

    
    
]
