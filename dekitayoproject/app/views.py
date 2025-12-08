from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from . models import Users,Families,PasswordResetToken
from .import forms
from .forms import UsersModelForm,Family_membersModelForm,LoginForm,RequestPasswordResetForm, SetNewPasswordForm
import uuid

def signup(request):
    User_form = UsersModelForm()
    Family_members_form = Family_membersModelForm()

    if request.method == 'POST':
        User_form = UsersModelForm(request.POST)
        Family_members_form = Family_membersModelForm(request.POST)
        
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
    login_form = LoginForm(request.POST or None)
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

def request_password_reset(request):
    request_password_resetForm = RequestPasswordResetForm(request.POST or None)
    if request_password_resetForm.is_valid():
        email = request_password_resetForm.cleaned_data['email']
        user = get_object_or_404(Users, email=email)

        password_reset_token, created = PasswordResetToken.objects.get_or_create(user_PasswordReset=user)
        if not created:
            password_reset_token.token = uuid.uuid4()
            password_reset_token.used = False
            password_reset_token.save()
        user.is_avtive = False
        user.save

        token = password_reset_token.token
        print(f"{request.scheme}://{request.get_host()}/app/reset_password/{token}/")

    return render (request, 'app/request_password_reset.html',context={
        'reset_form': request_password_resetForm,
    })

def reset_password(request, token):
    password_reset_token = get_object_or_404(
        PasswordResetToken,
        token=token,
        used=False,
    )

    form = SetNewPasswordForm(request.POST or None)
    if form.is_valid():
        user = password_reset_token.user
        password = form.cleaned_data['password1']
        validate_password(password)
        user.set_password(password)
        user.is_active = True
        user.save()

        password_reset_token.used = True
        password_reset_token.save()
        return redirect('login')
        
    return render(request,
        'app/password_reset_confirm.html',context={
        'confirm_form': form,
    })


def child_home(request):

    return render (request, 'app/child_home.html')
        