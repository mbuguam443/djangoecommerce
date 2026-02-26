from django import forms

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