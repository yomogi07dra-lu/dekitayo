from django.shortcuts import render,redirect
from . import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from . models import Families
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

def signup(request):
    User_form = forms.UsersModelForm()
    Family_members_form = forms.Family_membersModelForm()

    if request.method == 'POST':
        User_form = forms.UsersModelForm(request.POST)
        Family_members_form = forms.Family_membersModelForm(request.POST)
        
        if User_form.is_valid() and Family_members_form.is_valid():

            family = Families.objects.create()
            family_member = Family_members_form.save(commit=False)
            family_member.family = family
            family_member.save()
            user = User_form.save(commit=False)
            user.family_member = family_member
            # default_icon = Icons.objects.get(id=1)
            # user.icon = default_icon
            user.save()
            return redirect('login')

    return render(
        request, 
        'app/signup.html', 
        context={
            'signup': User_form,
            'role': Family_members_form,
        }
    )


def user_login(request):
    login_form = forms.LoginForm(request.POST or None)
    if login_form.is_valid():
        email = login_form['email']
        password = login_form['password']
        user = authenticate(email=email, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            return redirect('login')
    return render(
        request, 'app/login.html',context={
        'login_form': login_form,
        }
    )


@login_required
def user_logout(request):
    logout(request)
    return redirect('login')