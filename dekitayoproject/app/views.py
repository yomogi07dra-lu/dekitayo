from django.shortcuts import render,redirect, get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from . models import User,Child,Family,Family_member,PasswordResetToken,Item,Invitation,DailyLogItem,Daily_log,ParentComment
from .import forms
from .forms import UsersModelForm,Family_membersModelForm,LoginForm,RequestPasswordResetForm, SetNewPasswordForm,ItemForm,DailyLogForm, ParentCommentForm
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

                if role == 1:
                    Child.objects.create(
                        user=user,
                        family_member=family_member,
                    )                

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
        member = user.family_member
        if member and member.role == Family_member.PARENT:
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
COLOR_SLOTS = [
    {"index":0, "class": "red"},
    {"index":1, "class": "orange"},
    {"index":2, "class": "yellow"},
    {"index":3, "class": "green"},
    {"index":4, "class": "cyan"},
    {"index":5, "class": "blue"},
    {"index":6, "class": "purple"},
]
SLOT_INDEXES = [slot["index"] for slot in COLOR_SLOTS] 

@login_required
def parent_item_manage(request, child_id=None):

    # ログインユーザーのfamily取得
    family = request.user.family_member.family


    if child_id is None: #child_idが指定されていない場合
        # 最初に登録された子ども
        child = (
            Child.objects
            .filter(
                family_member__family=family,
                family_member__role=Family_member.CHILD,
            )
            .select_related("user", "family_member")
            .order_by("id")     # 最初に登録した子ども
            .first()
        )
        #　子どもが登録されていない場合
        if child is None:
            return redirect("invitation")

    # child_id が指定されている場合　兄弟切替
    else:
        child = get_object_or_404(
            Child,
            id=child_id,
            family_member__family=family,
            family_member__role=Family_member.CHILD,
        )
    #学習項目取得
    items = Item.objects.filter(
            family=family,
            child=child
        )

    # {0: Item, 1: Item, ...} の辞書に変換
    items_by_index = {item.color_index: item for item in items}


    form = ItemForm()
    
    if request.method == "POST":
        action = request.POST.get("action")
        #登録
        if action == "create":
            form = ItemForm(request.POST)
            if form.is_valid():
                item_name = form.cleaned_data["item_name"]

            used = set(items_by_index.keys())                     # 既に埋まっているスロット
            empty = [i for i in SLOT_INDEXES if i not in used]    # 空きスロット　上から

            if not empty:
                form.add_error(None, "学習項目は最大7つまでです")

            else: #スロットにItemがない（一番上から）
                Item.objects.create(
                    family=family,
                    child=child,
                    item_name=item_name,
                    color_index=empty[0],
                    )

                return redirect("parent_item_manage_with_child", child_id=child.id)

        # 削除
        elif action == "delete":
            ids = request.POST.getlist("item_ids")
            Item.objects.filter(
                id__in=ids,
                family=family,
                child=child,
            ).delete()

            return redirect("parent_item_manage_with_child", child_id=child.id)

    # 表示
    rows = [
        {
            "index": slot["index"],
            "class": slot["class"],
            "item": items_by_index.get(slot["index"]),  # 無ければ 未登録
        }
        for slot in COLOR_SLOTS
    ]
    return render(
        request,
        "app/parent_item_manage.html",
        {
            "child": child,
            "item_form": form,
            "rows": rows,
        },
    )

# 子ども用　学習記録　項目登録 #
@login_required
def child_record(request):
    today = timezone.localdate()
    family = request.user.family_member.family #子ども所属家族取得
    family_member = request.user.family_member
    
    child = Child.objects.filter(
        family_member=family_member,
        family_member__family=family,
        family_member__role=Family_member.CHILD,
    ).select_related("family_member").first()
        
    if child is None:
        return redirect("invitation")  
    
    items = list(Item.objects.filter(family=family, child=child).order_by("color_index"))


    # 今日の学習項目
    daily_log = Daily_log.objects.filter(
        user=request.user,
        child=child,
        date=today
    ).first()
    
    # 一度登録していた時の学習項目ID一覧
    checked_item_ids = []
    
    if daily_log is not None:
        checked_item_ids_queryset = (
            DailyLogItem.objects
            .filter(daily_log=daily_log)
            .values_list("item_id", flat=True)
        )
        checked_item_ids = list(checked_item_ids_queryset)

    # 画面表示用の7行データを作成
    rows = []

    for slot in COLOR_SLOTS:
        index = slot["index"]
        css_class = slot["class"]
        item = None

    # 登録されている学習項目を1つずつ確認する
        for one_item in items:
    # 学習項目の表示位置が、このスロット番号と同じか？
            if one_item.color_index == index:
                item = one_item
                break

        rows.append({
            "class": css_class,
            "item": item,
        })

    if request.method == "POST":
        form = DailyLogForm(request.POST, request.FILES)

        if form.is_valid():
            checked_item_ids = request.POST.getlist("item_ids")#チェックされた項目

            with transaction.atomic():#同じ日なら更新、なければ新規作成
                daily_log, created = Daily_log.objects.update_or_create(
                    user=request.user,
                    child=child,
                    date=today,
                )

                # コメント・写真を保存
                daily_log.child_comment = form.cleaned_data["child_comment"]
                daily_log.photo1_url = form.cleaned_data["photo1_url"]
                daily_log.photo2_url = form.cleaned_data["photo2_url"]
                daily_log.save()
                
                # 更新項目　前データ削除
                DailyLogItem.objects.filter(
                    daily_log=daily_log
                ).delete()

                # 更新項目　保存
                for item_id in checked_item_ids:
                    DailyLogItem.objects.create(
                        daily_log=daily_log,
                        item_id=item_id
                    )
        return redirect("child_home")
    
    else:
        if daily_log is not None:
            form = DailyLogForm(instance=daily_log)
        else:
            form = DailyLogForm()
    
    
    return render(request, "app/child_record.html",{
        "today": today,        
        "form": form,
        "rows": rows,
        "checked_item_ids": checked_item_ids,
    })

@login_required
#保護者用ホーム画面
def parent_home(request,child_id=None):
    today = timezone.localdate()
    family = request.user.family_member.family

    #保護者かどうか
    if request.user.family_member.role != Family_member.PARENT:
        messages.error(request, "保護者のみアクセスできます")
        return redirect("child_home")
    
    #child_idがあるならその子（兄弟切替から）ない場合は家族一覧最初の子ども
    
    if child_id is not None:
        child = get_object_or_404(
            Child,
            id=child_id,
            family_member__family=family,
            family_member__role=Family_member.CHILD,
        )
    else:
        child=(
            Child.objects
            .filter(
                family_member__family=family,
                family_member__role=Family_member.CHILD,
            )
            .select_related("user")
            .order_by("id")
            .first()
        )

    if child is None:
        # 子どもが未登録なら何も表示していないホーム画面を表示　テンプレートにて子ども登録のコメント
        return render(request, "app/parent_home.html", {
            "today": today,
            "child": None,
        })

    # 今日の学習記録
    daily_log = Daily_log.objects.filter(
        user=child.user,
        child=child,
        date=today,
    ).first()

    #今日の学習項目
    checked_items = []
    if daily_log is not None:
        checked_items = (
            DailyLogItem.objects
            .filter(daily_log=daily_log)
            .select_related("item")
            .order_by("id")
        )
    # 保護者コメント
    if request.method == "POST":
        if daily_log is None:
            messages.error(request, "今日の学習記録はまだありません")
            return redirect("parent_home_with_child", child_id=child.id)

        form = ParentCommentForm(request.POST)
        if form.is_valid():
            parent_comment = form.save(commit=False)
            parent_comment.user = request.user
            parent_comment.daily_log = daily_log
            parent_comment.save()
            return redirect("parent_home_with_child", child_id=child.id)
    else:
        form = ParentCommentForm()    

    return render(request, "app/parent_home.html", {
        "today": today,
        "child": child,
        "daily_log": daily_log,
        "checked_items": checked_items,
        "comment_form": form,
    })





def child_home(request):

    return render (request, 'app/child_home.html')

def parent_mypage(request):

    return render (request, 'app/parent_mypage.html')
        