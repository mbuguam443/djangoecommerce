from django import forms
from .models import Product
from .models import Category
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CheckoutForm(forms.Form):
    first_name = forms.CharField(max_length=50,label="First Name",
    error_messages={
        'required': 'Please enter your First Name.'
    })
    last_name = forms.CharField(max_length=50)
    country = forms.CharField(max_length=100)
    address = forms.CharField(max_length=255)
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)
    zip_code = forms.CharField(max_length=20)
    phone = forms.CharField(max_length=15)
    email = forms.EmailField()
    password = forms.CharField(min_length=6, widget=forms.PasswordInput)

    PAYMENT_CHOICES = [
        ('Cash', 'Cash'),
        ('Paypal', 'Paypal'),
        ('Mpesa', 'Mpesa'),
    ]

    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect
    )

class LoginForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        required=True,
        error_messages={
            'required': 'Email is required!',
            'invalid': 'Enter a valid email address.'
        }
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        error_messages={
            'required': 'Password cannot be empty!'
        }
    )    

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'weight', 'stock', 'available', 'image']
        # No widgets → default HTML elements will be rendered, your theme will style them    

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name','image']  # include only fields you want in the form

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "is_staff", "password1", "password2"]        