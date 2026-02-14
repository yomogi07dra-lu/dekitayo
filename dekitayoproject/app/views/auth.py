from django.shortcuts import render,redirect, get_object_or_404
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.conf import settings  
from .. models import User,Icon,Child,Family,Family_member,PasswordResetToken
from .. forms import UsersModelForm,Family_membersModelForm,LoginForm,RequestPasswordResetForm, SetNewPasswordForm
import uuid


# 新規登録
def signup(request):
    # GETの時　空フォーム表示　
    user_form = UsersModelForm()
    family_member_form = Family_membersModelForm()
    
    # POST（送信）の時
    if request.method == 'POST':
        # request（ブラウザからサーバーに送られきた全ての情報が入ったもの）からPOST（POST送信で入力された値） を使ってUsersModelForm（定義）に渡してuser_form（入力済みフォーム・インスタンス）を作る
        user_form = UsersModelForm(request.POST)
        family_member_form = Family_membersModelForm(request.POST)

        # 個別にバリデーション（OKならcleaned_dataが使用できる）
        user_ok = user_form.is_valid()
        role_ok = family_member_form.is_valid()

        # 定義
        role = None
        invite = None

        if role_ok:
            role = family_member_form.cleaned_data.get("role")
            invite = getattr(user_form, "invite", None)  

            if str(role) == "1" and not request.POST.get("invitation_code"):
                user_form.add_error("invitation_code", "子どもは招待コードが必要です")
        
        forms_ok = user_ok and role_ok and (not user_form.errors.get("invitation_code"))

        # すべてOKのときだけDB反映
        if forms_ok:
            with transaction.atomic():  # すべて成功したらDB反映　エラーが起きたらなかったことに（中途半端を防ぐ）

                # ロール
                if role == 1:  #子ども

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

                if role == 1:
                    default_path = "icons/cat_1.png"
                else:
                    default_path = "icons/parent_default.png"

                # Iconレコードを探す（無ければNone）FOREIGN KEY constraint failedを防ぐ
                default_icon = Icon.objects.filter(image_url=default_path).first()

                # なければ未設定
                if default_icon:
                    user.icon = default_icon

                user.save()


                if role == 1:
                    Child.objects.create(
                        user=user,
                        family_member=family_member,
                    )                

                if invite:#招待コード使い捨て
                    invite.is_active = False
                    invite.save()

            # 新規登録後の遷移先をロールで分岐
            login(request, user)
            if role == 0:  # 保護者
                return redirect("parent_home")
            else:          # 子ども
                return redirect("child_home")
        
    return render(
        request, 
        'app/auth/signup.html', 
        context={
            'signup': user_form,
            'role': family_member_form,
        }
    )

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
            return render(request,"app/auth/login.html", {"login_form": login_form})
        
        user = authenticate(request,email=email, password=password)

        if user is None:
            login_form.add_error(None, "メールアドレスまたはパスワードが違います")
            return render(request,"app/auth/login.html", {"login_form": login_form})
        
        login(request, user)

    # 保護者と子ども　画面遷移分け
        member = user.family_member
        if member and member.role == Family_member.PARENT:
            return redirect('parent_home')
        else:
            return redirect('child_home')

    return render(
        request, 'app/auth/login.html',context={
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
        #　404にしない
        user = User.objects.filter(email=email).first()
        if user:
            password_reset_token, created = PasswordResetToken.objects.get_or_create(user_PasswordReset=user)
            if not created:
                password_reset_token.token = uuid.uuid4()
                password_reset_token.used = False
                password_reset_token.save()

            token = password_reset_token.token
            reset_url = (f"{request.scheme}://{request.get_host()}/app/password_reset_confirm/{token}/")

            send_mail(
                subject="【パスワード再設定】",
                message=f"""
                    以下のURLからパスワードを再設定してください。

                    {reset_url}

                    ※このリンクは一度のみ有効です。
                """,
                
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            # 送信成功したら完了画面へ
        return redirect("request_password_reset_done")


    return render (request, 'app/auth/request_password_reset.html',context={
        'reset_form': request_password_resetForm,
    })
# パスワード変更URL　メール送信完了
def request_password_reset_done(request):
    return render(request, "app/auth/request_password_reset_done.html")

#パスワード再設定変更
def password_reset_confirm(request, token):
    password_reset_token = get_object_or_404(
        PasswordResetToken,
        token=token,
        used=False,
    )

    form = SetNewPasswordForm(request.POST or None)
    if form.is_valid():
        user = password_reset_token.user_PasswordReset
        password = form.cleaned_data['password1']
        try:
            validate_password(password, user=user)
        except ValidationError as e:
            form.add_error("password1", e.messages)
            return render(request, "app/auth/password_reset_confirm.html", {
                "confirm_form": form,
            })

        
        user.set_password(password)
        user.save()

        password_reset_token.used = True
        password_reset_token.save()
        return redirect('login')
        
    return render(request,
        'app/auth/password_reset_confirm.html',context={
        'confirm_form': form,
    })
