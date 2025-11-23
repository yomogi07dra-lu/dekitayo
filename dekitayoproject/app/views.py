from django.shortcuts import render
from . import forms

def signup(request):
    form = forms.UsersModelForm()
    return render(
        request, 
        'app/signup.html', 
        context={
            'signup': form
        }
    )