from django.shortcuts import render,redirect, get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from . models import User,Family,Family_member,PasswordResetToken,Item,Invitation,DailyLogItem,Daily_log
from .import forms
from .forms import UsersModelForm,Family_membersModelForm,LoginForm,RequestPasswordResetForm, SetNewPasswordForm,ItemForm,DailyLogForm
import uuid
from .utils import generate_invite_code

#新規登録
def signup(request):
    user_form = UsersModelForm()
    family_member_form = Family_membersModelForm()

    if request.method == 'POST':
        user_form = UsersModelForm(request.POST)
        family_member_form = Family_membersModelForm(request.POST)
        
        if user_form.is_valid() and family_member_form.is_valid():
            with transaction.atomic():#すべて成功したらDB反映
                
                role = family_member_form.cleaned_data.get("role")
                invite = getattr(user_form, "invite", None)

                if role == 1:  #子ども
                    if not invite:#招待コード無
                        user_form.add_error(
                            "invitation_code",
                            "子どもは招待コードが必要です"
                        )
                        return render(request,'app/signup.html', {
                            'signup': user_form,
                            'role': family_member_form
                        })
                    family = invite.family
                
                else: #保護者
                    if invite:#招待コード有　既存家族
                        family = invite.family
                    else:#招待コード無　新規家族作成
                        family = Family.objects.create()


                family_member = family_member_form.save(commit=False)
                family_member.family = family
                family_member.role = role

                #保護者・招待コードなし＝保護者代表
                family_member.is_admin = (role == 0 and not invite)
                family_member.save()

                user = user_form.save(commit=False)
                user.family_member = family_member
                user.save()

                if invite:#招待コード使い捨て
                    invite.is_active = False
                    invite.save()
            # default_icon = Icons.objects.get(id=1)
            # user.icon = default_icon

            return redirect('login')

    return render(
        request, 
        'app/signup.html', 
        context={
            'signup': user_form,
            'role': family_member_form,
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
    invite = Invitation.objects.filter(family=family).first()

    if invite is None:
        invite = Invitation.objects.create(
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
            user_email = User.objects.get(email=email)
        except User.DoesNotExist:
            login_form.add_error(None, "メールアドレスまたはパスワードが違います")
            return render(request,"app/login.html", {"login_form": login_form})
        
        user = authenticate(request,username=user_email.username, password=password)

        if user is None:
            login_form.add_error(None, "メールアドレスまたはパスワードが違います")
            return render(request,"app/login.html", {"login_form": login_form})
        
        login(request, user)

#保護者と子ども　画面遷移分け
        member = Family_member.objects.filter(user=user).first()
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
        user = get_object_or_404(User, email=email)

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
    items = Item.objects.filter(user=request.user).order_by('id')#DBの一覧　QuerySet
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
                return redirect("parent_item_manage")

        if action == 'delete':
            ids = request.POST.getlist('item_ids')
            Item.objects.filter(id__in=ids, user=request.user).delete()
            return redirect("parent_item_manage")
    #表示用データ　List 色とペア
    rows = []#行
    item_count = items.count()#項目数

    for i, color in enumerate(colors):
        item = None

        if i < item_count:
            item = items[i]

        rows.append({
            "color": color,
            "item": item,
        })
    

    return render(request, 'app/parent_item_manage.html',{
        'item_form': form,
        'rows': rows,
    })
# 子ども用　学習記録　項目登録 #
@login_required
def child_record(request):
    today = timezone.localdate()
    family = request.user.family_member.family #子ども所属家族取得
    
    parent_user = User.objects.filter( #家族の代表取得
        family_member__family=family,
        family_member__role=0,
        family_member__is_admin=True,
    ).first()

    if parent_user:#家族代表が登録した項目取得
        items = list(Item.objects.filter(user=parent_user).order_by("id"))
    else:
        items = []    
    
    colors = [
        "#ff0000",
        "#ff9900",
        "#ffff00",
        "#00ff00",
        "#00ffff",
        "#0000ff",
        "#9900ff",
    ]

    rows = [] #7行の項目作成
    for i, color in enumerate(colors):
        item = None

        if i < len(items):
            item = items[i]

        rows.append({
            "color": color,
            "item": item,
        })
    
    if request.method == "POST":
        form = DailyLogForm(request.POST, request.FILES)

        if form.is_valid():
            checked_item_ids = request.POST.getlist("item_ids")#チェックされた項目

            with transaction.atomic():#同じ日なら更新、なければ新規作成
                daily_log, created = Daily_log.objects.update_or_create(
                    user=request.user,
                    date=today,
                    defaults={
                        "comment": form.cleaned_data["comment"],
                        "photo1_url": form.cleaned_data.get("photo1_url"),
                        "photo2_url": form.cleaned_data.get("photo2_url"),
                    }
                )
                #更新は全部消して作成しなおす
                DailyLogItem.objects.filter(daily_log=daily_log).delete()
                if checked_item_ids:
                    DailyLogItem.objects.bulk_create([
                        DailyLogItem(daily_log=daily_log, item_id=item_id)
                        for item_id in checked_item_ids
                    ])
        return redirect("child_home")
    
    else:
        form = DailyLogForm()
    
    
    return render(request, "app/child_record.html",{
        "today": today,        
        "form": form,
        "rows": rows,
    })


def child_home(request):

    return render (request, 'app/child_home.html')

def parent_home(request):

    return render (request, 'app/parent_home.html')

def parent_mypage(request):

    return render (request, 'app/parent_mypage.html')
        