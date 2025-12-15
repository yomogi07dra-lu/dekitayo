from django.shortcuts import render,redirect, get_object_or_404
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from . models import Users,Families,Family_members,PasswordResetToken,Items,Invitations
from .import forms
from .forms import UsersModelForm,Family_membersModelForm,LoginForm,RequestPasswordResetForm, SetNewPasswordForm,ItemForm
import uuid
from .utils import generate_invite_code

#新規登録
def signup(request):
    User_form = UsersModelForm()
    Family_members_form = Family_membersModelForm()

    if request.method == 'POST':
        User_form = UsersModelForm(request.POST)
        Family_members_form = Family_membersModelForm(request.POST)
        
        if User_form.is_valid() and Family_members_form.is_valid():
            with transaction.atomic():#すべて成功したらDB反映
                
                invite = getattr(User_form, 'invite', None)#招待コードがあれば使用
                if invite:
                    family = invite.family
                else:
                    family = Families.objects.create()

                family_member = Family_members_form.save(commit=False)
                family_member.family = family

                if invite:#代表は保護者
                    family_member.role = 1 
                    family_member.is_admin = False
                else:
                    family_member.role = 0
                    family_member.is_admin = True
                family_member.save()

                user = User_form.save(commit=False)
                user.family_member = family_member
                user.save()

                if invite:
                    invite.is_active = False
                    invite.save()
            # default_icon = Icons.objects.get(id=1)
            # user.icon = default_icon

            return redirect('login')

    return render(
        request, 
        'app/signup.html', 
        context={
            'signup': User_form,
            'role': Family_members_form,
        }
    )

#招待コード#
@login_required
def invitation(request):
    member = request.user.family_member

    if member is None or member.role != 0 or not member.is_admin:
        messages.error(request, '権限がありません')
        return redirect('parent_mypage')

    family = member.family
    invite = Invitations.objects.filter(family=family).first()

    if invite is None:
        invite = Invitations.objects.create(
            family=family,
            code=generate_invite_code(),
            is_active=True
        )
    else:
        invite.code = generate_invite_code()
        invite.is_active = True
        invite.save()

    return render(request, 'app/parent_invitation.html', {
        'invite': invite
    })



#ログイン
def user_login(request):
    login_form = LoginForm(request.POST or None)

    if request.method== "POST" and login_form.is_valid():
        email = login_form.cleaned_data['email']
        password = login_form.cleaned_data['password']

        try:
            user_email = Users.objects.get(email=email)
        except Users.DoesNotExist:
            login_form.add_error(None, "メールアドレスまたはパスワードが違います")
            return render(request,"app/login.html", {"login_form": login_form})
        
        user = authenticate(request,username=user_email.username, password=password)

        if user is None:
            login_form.add_error(None, "メールアドレスまたはパスワードが違います")
            return render(request,"app/login.html", {"login_form": login_form})
        
        login(request, user)

#保護者と子ども　画面遷移分け
        member = Family_members.objects.filter(users=user).first()
        if member and member.role == 0:
            return redirect('parent_home')
        else:
            return redirect('child_home')

    return render(
        request, 'app/login.html',context={
        'login_form': login_form,
        }
    )

#ログアウト
@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

#パスワード再設定送信
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

#パスワード再設定変更
def reset_password(request, token):
    password_reset_token = get_object_or_404(
        PasswordResetToken,
        token=token,
        used=False,
    )

    form = SetNewPasswordForm(request.POST or None)
    if form.is_valid():
        user = password_reset_token.user_PasswordReset
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

#保護者用学習項目登録
@login_required 
def parent_item_manage(request):
    colors = [
        "#ff0000",
        "#ff9900",
        "#ffff00",
        "#00ff00",
        "#00ffff",
        "#0000ff",
        "#9900ff",
    ]
    items = Items.objects.filter(user=request.user).order_by('id')
    form = ItemForm(request.POST or None)

    if request.method =='POST':
        action = request.POST.get('action')

        if action == 'create':
            if items.count() >= 7:
                form.add_error(None, "登録項目は最大7つまでです")
            elif form.is_valid():
                item = form.save(commit=False)
                item.user = request.user
                item.save()
                form = ItemForm()

        if action == 'delete':
            ids = request.POST.getlist('item_ids')
            Items.objects.filter(id__in=ids, user=request.user).delete()
            form = ItemForm()
    

    return render(request, 'app/parent_item_manage.html',{
        'item_form': form,
        'items': items,
        'colors': colors, 
    })
# 子ども用　学習記録　項目登録 #
@login_required
def child_record(request):
    family = request.user.family_member.family
    parent_user = Users.objects.filter(
        family_member__family=family,
        family_member__role=0
    ).first()

    if parent_user is None:
        items = Items.objects.none()
    else:
        items = Items.objects.filter(user=parent_user).order_by("id")

    return render(request, "app/child_record.html", {
        "items": items,
    })

        

        



def child_home(request):

    return render (request, 'app/child_home.html')

def parent_home(request):

    return render (request, 'app/parent_home.html')

def parent_mypage(request):

    return render (request, 'app/parent_mypage.html')
        