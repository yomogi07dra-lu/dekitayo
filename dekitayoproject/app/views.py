from django.shortcuts import render,redirect
from . import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

def signup(request):
    User_form = forms.UsersModelForm()
    Family_members_form = forms.Family_membersModelForm()

    if request.method == 'POST':
        User_form = forms.UsersModelForm(request.POST)
        Family_members_form = forms.Family_membersModelForm(request.POST)
        
        if User_form.is_valid() and Family_members_form.is_valid():
            
            User_form.save(commit=True)
            Family_members_form.save()
            return redirect('home')
    else:
        User_form = forms.UsersModelForm()
        Family_members_form = forms.Family_membersModelForm()

    return render(
        request, 
        'app/signup.html', 
        context={
            'signup': User_form,
            'role': Family_members_form,
        }
    )