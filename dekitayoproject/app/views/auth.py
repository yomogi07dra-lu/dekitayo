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
        
        # ロールが入力されている（正しく取れない（または意図しない）を防ぐ）
        if role_ok:
            role = family_member_form.cleaned_data.get("role")
            invite = getattr(user_form, "invite", None)  # 招待コードがあれば取得なければNone
            # ロールが1（子ども）＋招待コードがない場合　エラーを発生させる
            if str(role) == "1" and not request.POST.get("invitation_code"):
                user_form.add_error("invitation_code", "子どもは招待コードが必要です")
        
        # すべて（ユーザー・ロール・招待コードエラー）OKのときだけDB反映
        forms_ok = user_ok and role_ok and (not user_form.errors.get("invitation_code"))
        if forms_ok:
            with transaction.atomic():  # すべて成功したらDB反映　エラーが起きたらなかったことに（中途半端を防ぐ）

                # ロール
                if role == 1:  #子ども　（inviteに紐づくFamilyに追加）
                    family = invite.family
                
                else: #保護者
                    if invite:#招待コード有　既存家族（inviteに紐づくFamilyに追加）
                        family = invite.family
                    else:#招待コード無　新規家族作成
                        family = Family.objects.create()

                # Family_member オブジェクトを作る(DBにはまだ保存しない)
                family_member = family_member_form.save(commit=False)
                # 決めたFamilyを代入
                family_member.family = family
                # 保護者か子どもか代入
                family_member.role = role
                #保護者・招待コードなし＝保護者代表
                family_member.is_admin = (role == 0 and not invite)
                #　family_memberをDB保存
                family_member.save()

                #　Userオブジェクトを作成（DBにはまだ保存しない）
                user = user_form.save(commit=False)
                # Userに紐づくFamily_memberに保存したfamily_memberをDB代入
                user.family_member = family_member

                # ロールによるアイコン設定
                if role == 1:
                    default_path = "icons/cat_1.png"
                else:
                    default_path = "icons/parent_default.png"

                # user.icon は ForeignKeyなので画像パスの文字列でなく
                # Iconレコードが必要(image_url が default_path と一致するレコード無ければNone）
                # FOREIGN KEY constraint failed（存在しない場合でのエラー）を防ぐ
                default_icon = Icon.objects.filter(image_url=default_path).first()

                # なければ未設定
                if default_icon:
                    user.icon = default_icon

                user.save()

                # 子どもの場合　ユーザーに対するChildレコードを作成　UserとFamily_memberを紐づけ
                if role == 1:
                    Child.objects.create(
                        user=user,
                        family_member=family_member,
                    )                

                if invite:#招待コード使い捨て
                    invite.is_active = False # この招待コードは無効化する
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
        # authenticate:Django の認証機能 ユーザーの存在　パスワードの一致　有効アカウントをチェック
        user = authenticate(request,email=email, password=password)

        if user is None:
            login_form.add_error(None, "メールアドレスまたはパスワードが違います")
            return render(request,"app/auth/login.html", {"login_form": login_form})
        
        login(request, user)

    # 保護者と子ども　画面遷移分け
        member = user.family_member
        # role は Family_member のフィールドにあるためfamily_memberを取得
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
        # 入力されたメールアドレス取得
        email = request_password_resetForm.cleaned_data['email']
        #　ユーザーを探す（filterはユーザーが無ければNone いなくても404にしない）
        user = User.objects.filter(email=email).first()
        # ユーザーが存在すれば　トークン取得or作成、新規作成かすでに作成していたものか（true/False） 
        if user:
            password_reset_token, created = PasswordResetToken.objects.get_or_create(user_PasswordReset=user)
            # 2回目以降 トークンを更新する
            if not created:
                #　新しいトークン発行（古いトークンは無効）
                password_reset_token.token = uuid.uuid4()
                # 使用していない状態に（パスワード再設定時リンク成功時使用済み（Ture）にしているため）
                password_reset_token.used = False
                # DBに保存
                password_reset_token.save()

            token = password_reset_token.token
            # URL組み立て
            # request.scheme→ http か https, request.get_host()→ 今アクセスしているドメイン ,/app/password_reset_confirm/{token}/→ トークン付きの再設定ページURL
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

# パスワード変更URL　メール送信完了画面
def request_password_reset_done(request):
    return render(request, "app/auth/request_password_reset_done.html")

#パスワード再設定変更
def password_reset_confirm(request, token):
    # トークンが一致、使用っされていないものを取得　見つからなければエラー（正しいリンクは有効、使い終わったリンクは無効）
    password_reset_token = get_object_or_404(
        PasswordResetToken,
        token=token,
        used=False,
    )

    form = SetNewPasswordForm(request.POST or None)
    if form.is_valid():
        # トークンに紐づいているユーザー取得
        user = password_reset_token.user_PasswordReset
        # 入力されたパスワード取得
        password = form.cleaned_data['password1']
        try:
            # Django標準のパスワードバリデーション
            validate_password(password, user=user)
        except ValidationError as e:
            form.add_error("password1", e.messages)
            return render(request, "app/auth/password_reset_confirm.html", {
                "confirm_form": form,
            })

        # パスワードはハッシュ化して保存
        user.set_password(password)
        user.save()
        # 使用したトークン無効化
        password_reset_token.used = True
        password_reset_token.save()
        return redirect('login')
        
    return render(request,
        'app/auth/password_reset_confirm.html',context={
        'confirm_form': form,
    })
