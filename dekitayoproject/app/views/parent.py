from django.shortcuts import render,redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .. models import ParentComment, User,Child,Family_member,Item,Invitation,DailyLogItem,Daily_log, Icon
from django.contrib.auth import update_session_auth_hash
from datetime import date, timedelta
from .. forms import ItemForm, ParentCommentForm, EmailChangeForm, PasswordChangeForm
import calendar
from .. utils import generate_invite_code
from .utils import get_target_child



# 保護者学習項目登録・子ども学習記録・子どもホーム画面・保護者ホーム画面共通
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
#保護者用ホーム画面・過去記録画面
def parent_home(request, year=None, month=None, day=None):
    # 基準の日付
    if year and month and day:
        target_date = date(int(year), int(month), int(day))
    else:
        target_date = timezone.localdate() #　指定なければ今日

    #保護者かどうか
    if request.user.family_member.role != Family_member.PARENT:
        messages.error(request, "保護者のみアクセスできます")
        return redirect("child_home")
    
    # 表示する子どもの選択（共通）
    child = get_target_child(request) 
   
    if child is None:
        # 子どもが未登録なら何も表示していないホーム画面を表示　テンプレートにて子ども登録のコメント
        return render(request, "app/parent/home.html", {
            "child": None,
            "today":target_date
        })

    # 今日の学習記録　取得
    daily_log = Daily_log.objects.filter(
        child=child,
        date=target_date,
    ).first() #最新取得

    # 今日の学習項目　取得（表示対象（active）のみ）
    family = request.user.family_member.family    

    checked_item_ids = []
    if daily_log is not None:
        checked_item_ids = list(
            DailyLogItem.objects
            .filter(daily_log=daily_log)
            .values_list("item_id", flat=True)
        )

    items = list(
        Item.objects
        .filter(family=family, child=child, id__in=checked_item_ids)
        .order_by("color_index")
    )

    # 表示 #
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

    
    # 子どものコメントは表示なのでテンプレートで

    # 保護者コメント（POST/GETで共通化してシンプルに）
    form = ParentCommentForm()
    if request.method == "POST":
        form = ParentCommentForm(request.POST)

        if daily_log is None:
            # POSTデータを保持せず戻す（入力は消える）
            return redirect(
                "parent_home_by_date",
                year=target_date.year, month=target_date.month, day=target_date.day
            )

        elif form.is_valid():
            parent_comment = form.save(commit=False)
            parent_comment.user = request.user
            parent_comment.daily_log = daily_log
            parent_comment.save()
            
            messages.success(request, "送信しました")

            return redirect(
                "parent_home_by_date",
                year=target_date.year, month=target_date.month, day=target_date.day
            )

        else:
            # モーダル用メッセージに渡す
            messages.error(request, "コメントは改行含め、100文字以内で入力してください")

    # 保護者コメント一覧
    parent_comments = []
    if daily_log is not None:
        parent_comments = (
            ParentComment.objects
            .filter(daily_log=daily_log)
            .order_by("-created_at")  # 最新が上
        )

    return render(request, "app/parent/home.html", {
        "today": target_date,
        "child": child,
        "daily_log": daily_log,
        "rows": rows,
        "checked_item_ids": checked_item_ids,
        "comment_form": form,
        "parent_comments": parent_comments,
    })

#保護者用学習項目登録
@login_required
def parent_item_manage(request):

    #保護者かどうか
    if request.user.family_member.role != Family_member.PARENT:
        messages.error(request, "保護者のみアクセスできます")
        return redirect("child_home")

    # 表示する子どもの選択（共通）
    child = get_target_child(request)
    
    if child is None:
        # 子どもが未登録なら何も表示していない学習項目登録画面を表示　テンプレートにて子ども登録のコメント
        return render(request, "app/parent/item_manage.html", {
            "child": None,
        })


    #学習項目取得 （表示対象（active）のみ）
    family = request.user.family_member.family
    items = Item.objects.filter(
            family=family,
            child=child,
            is_active=True
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
                    # 二重登録防止
                    already_exists = Item.objects.filter(
                        family=family,
                        child=child,
                        item_name=item_name,
                        is_active=True,
                    ).exists()

                    if already_exists:
                        form.add_error("item_name", "同じ学習項目がすでに登録されています")
                    else:
                        Item.objects.create(
                            family=family,
                            child=child,
                            item_name=item_name,
                            color_index=empty[0],
                        )
                        return redirect("parent_item_manage")

        # 削除
        elif action == "delete":
            ids = request.POST.getlist("item_ids")
            Item.objects.filter(
                id__in=ids,
                family=family,
                child=child,
            ).update(is_active=False, # ソフトデリート
                     deleted_at=timezone.now(), 
            ) 

            return redirect("parent_item_manage")

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
        "app/parent/item_manage.html",
        {
            "child": child,
            "item_form": form,
            "rows": rows,
        },
    )

    
# 保護者用月間学習記録カレンダー
@login_required
def parent_monthly_calendar(request, year=None, month=None):

    #保護者かどうか
    if request.user.family_member.role != Family_member.PARENT:
        messages.error(request, "保護者のみアクセスできます")
        return redirect("child_home")

    # 表示する子どもの選択（共通）
    child = get_target_child(request)

    #　基準の日付
    today = timezone.localdate()
    year = year or today.year
    month = month or today.month

    # 基準　今月の1日
    current = date(year, month, 1)

    # 前月
    prev_date = current - timedelta(days=1) # timedelta は「日・時間・秒」単位ずらす
    prev_year = prev_date.year
    prev_month = prev_date.month

    # 次月
    next_date = (current + timedelta(days=31)).replace(day=1)
    next_year = next_date.year
    next_month = next_date.month

    cal = calendar.Calendar(firstweekday=6) # 日曜(6)始まり
    month_days = cal.monthdayscalendar(year, month)
    
    # 子どもがいない場合  month_days から calendar_days を作る
    if child is None:
        calendar_days = []
        for week in month_days:
            row = []
            for day in week:
                if day == 0:
                    row.append({"day": 0})
                else:
                    target = date(year, month, day)
                    row.append({
                        "day": day,
                        "can_edit": False,     # 未来日
                        "has_log": False,    # ⭐用
                    })
            calendar_days.append(row)

        context = {
            "today": today,
            "child": None,
            "year": year,
            "month": month,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "month_days": month_days,
            "calendar_days": calendar_days,  
            "learned_days": set(),
        }
        return render(request, "app/parent/monthly_calendar.html", context)

    #記録の絞り込み
    daily_logs = Daily_log.objects.filter(
        child=child,
        date__year=year,
        date__month=month,
    )    
    # 学習した日付　
    learned_days = {
        daily_log.date.day
        for daily_log in daily_logs
    }
    # テンプレを簡単にするためのデータ
    calendar_days = []
    for week in month_days:
        row = []
        for day in week:
            if day == 0:
                row.append({"day": 0})
            else:
                target = date(year, month, day)
                row.append({
                    "day": day,
                    "can_edit": target <= today,     # 未来日はリンク無し
                    "has_log": day in learned_days,    # ⭐表示用
                })
        calendar_days.append(row)
    
    context = {
        "today": today,
        "child": child,
        "year": year,
        "month": month,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "calendar_days": calendar_days,
        "learned_days": learned_days,
    }

    return render (request, 'app/parent/monthly_calendar.html', context)



# 保護者用月間学習記録グラフ
@login_required
def parent_monthly_graph(request, year=None, month=None):
    #保護者かどうか
    if request.user.family_member.role != Family_member.PARENT:
        messages.error(request, "保護者のみアクセスできます")
        return redirect("child_home")
    
    # 表示する子どもの選択（共通）
    child = get_target_child(request)
    
    #日付
    today = timezone.localdate()
    year = year or today.year
    month = month or today.month

    start_date = date(year, month, 1) # 月初めの日（1日）
    last_day = calendar.monthrange(year, month)[1] # 1か月間　何日あるか
    end_date = date(year, month, last_day) # 月終わりの日付

    current = date(year, month, 1)

    prev_date = current - timedelta(days=1)
    prev_year = prev_date.year
    prev_month = prev_date.month

    next_date = (current + timedelta(days=31)).replace(day=1)
    next_year = next_date.year
    next_month = next_date.month   

    # 子ども未登録の場合　"labels""counts""colors"空データ
    if child is None:
        context = {
            "today": today,
            "child": None,
            "labels": [],      
            "counts": [],      
            "colors": [],      
            "year": year,
            "month": month,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "monthly_total": 0,
        }
        return render(request, "app/parent/monthly_graph.html", context)

   
    #データ
    family = request.user.family_member.family
    qs = (
    Item.objects      # 学習項目から（項目数が0でも表示できる）
    .filter(family=family, child=child)
    .annotate(
        total=Count(          # 各 Item に計算結果の列 total を追加
            "dailylogitem",   # Item に紐づく DailyLogItem を数える
            filter=Q(         #「この月の分だけ」を数える条件
                dailylogitem__daily_log__date__range=(start_date, end_date)
            ),
        )
    )
    .filter(total__gt=0)        
    .order_by("color_index") # 並び順
)
    
    # COLOR_SLOTSを利用 辞書に
    COLOR_CLASS_MAP = {slot["index"]: slot["class"] for slot in COLOR_SLOTS}

    # グラフ
    labels = [item.item_name for item in qs] # 縦軸
    counts = [item.total for item in qs] # 横軸
    colors = [COLOR_CLASS_MAP.get(item.color_index, "gray") for item in qs] # 色　（0～6以外はgray）

    context = {
        "today": today,
        "child": child,
        "labels": labels,
        "counts": counts,
        "colors": colors,
        "year": year,
        "month": month,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    }
    
    # 月間学習項目数
    monthly_total = sum(item.total for item in qs)
    context["monthly_total"] = monthly_total

    return render (request, 'app/parent/monthly_graph.html', context)

@login_required
# 保護者用週間学習記録グラフ
def parent_weekly_graph(request, year=None, month=None, day=None):
    
    #保護者かどうか
    if request.user.family_member.role != Family_member.PARENT:
        messages.error(request, "保護者のみアクセスできます")
        return redirect("child_home")

    #日付
    today = date.today()
    if year and month and day:
        base_date = date(int(year), int(month), int(day))
    else:
        base_date = today
    # 週の範囲
    offset = (base_date.weekday() + 1) % 7
    start_date = base_date - timedelta(days=offset)       # 日曜
    end_date = start_date + timedelta(days=6)             # 土曜

    # 前週・次週用
    prev_base = start_date - timedelta(days=7)
    next_base = start_date + timedelta(days=7)

    
    # 表示する子どもの選択（共通）
    child = get_target_child(request)


    # 子ども未登録の場合　"counts"は空データ
    if child is None:
        context = {
            "today": today,
            "child": None,
            "labels": ["日", "月", "火", "水", "木", "金", "土"],
            "counts": [0, 0, 0, 0, 0, 0, 0],
            "start_date": start_date,
            "end_date": end_date,
            "prev_year": prev_base.year,
            "prev_month": prev_base.month,
            "prev_day": prev_base.day,
            "next_year": next_base.year,
            "next_month": next_base.month,
            "next_day": next_base.day,
        }
        return render(request, "app/parent/weekly_graph.html", context)
    
    #データ
    day_totals = (
        Daily_log.objects
        .filter(child=child, date__range=(start_date, end_date))
        .annotate(total=Count("dailylogitem"))
        .values("date", "total")
    )    
    
    total_map = {row["date"]: row["total"] for row in day_totals}

    # グラフ
    labels = ["日", "月", "火", "水", "木", "金", "土"] # 縦軸
    counts = [total_map.get(start_date + timedelta(days=i), 0) for i in range(7)] # 横軸

    context = {
        "today": today,
        "child": child,
        "labels": labels,
        "counts": counts,
        "start_date": start_date,
        "end_date": end_date,
        "prev_year": prev_base.year, "prev_month": prev_base.month, "prev_day": prev_base.day,
        "next_year": next_base.year, "next_month": next_base.month, "next_day": next_base.day,
    }


    return render (request, 'app/parent/weekly_graph.html',context)


# 保護者用マイページ
@login_required
def parent_mypage(request):

    return render (request, 'app/parent/mypage.html')


# 保護者用 兄弟姉妹切替
@login_required
def parent_child_switch(request):

    #保護者かどうか
    if request.user.family_member.role != Family_member.PARENT:
        messages.error(request, "保護者のみアクセスできます")
        return redirect("child_home")
    
    # 子ども一覧
    family = request.user.family_member.family
    children = Child.objects.filter(
        family_member__family=family,
        family_member__role=Family_member.CHILD,
    ).select_related("user")

    # 子どもidを セッションで保存
    if request.method == "POST":
        selected_child_id = request.POST.get("child_id")

        if selected_child_id:
            request.session["selected_child_id"] = int(selected_child_id)
            return redirect("parent_home")
        
    return render (request, 'app/parent/child_switch.html',
        {"children": children}
    )


#招待コード#
@login_required
def invitation(request):
    member = request.user.family_member

    if member is None or member.role != 0 or not member.is_admin:
        messages.error(request, '権限がありません')
        return redirect('parent_mypage')

    family = member.family
    invite = None

    # 発行ボタンを押したときだけ発行
    if request.method == "POST":
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


    return render(request, 'app/parent/invitation.html', {
        'invite': invite
    })

# 保護者用 家族一覧
@login_required
def parent_family_list(request):
    #保護者かどうか
    if request.user.family_member.role != Family_member.PARENT:
        messages.error(request, "保護者のみアクセスできます")
        return redirect("child_home")
    
    # 家族取得
    family = request.user.family_member.family

    # 家族代表のみ
    member = request.user.family_member
    if member is None or member.role != 0 or not member.is_admin:
        messages.error(request, '権限がありません')
        return redirect('parent_mypage')

    # 削除
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        if not user_id:
            messages.error(request, "削除対象が選択されていません")
            return redirect("parent_family_list")
        
        target_user = get_object_or_404(
            User,
            id=user_id,
            family_member__family=family,
        )

        # 自分を消せないようにする
        if target_user.id == request.user.id:
            messages.error(request, "自分自身は削除できません")
            return redirect("parent_family_list")
        
        target_user.delete()  # Userごと消す
        return redirect("parent_family_list")
    
    # GET：一覧表示
    members = (
        User.objects
        .filter(family_member__family=family)
        .select_related("family_member", "icon")
        .order_by("id")
    )

    return render (request, 'app/parent/family_list.html', {
        "members": members,
    })

# 保護者用 パスワード変更
@login_required
def parent_password_change(request):
    #保護者かどうか
    if request.user.family_member.role != Family_member.PARENT:
        messages.error(request, "保護者のみアクセスできます")
        return redirect("child_home")

    parent_password_change_form = PasswordChangeForm(
        user=request.user,
        data=request.POST or None
    )
    if request.method == "POST":
        if parent_password_change_form.is_valid():
            parent_password_change_form .save()
            update_session_auth_hash(request, request.user)
        # 成功メッセージ（モーダルで表示する）
            messages.success(request, "パスワードを変更しました")
        
        else:
        # 失敗メッセージ・フォームのエラー文だけフィールド名は表示しない（モーダルで表示する）
            error_messages = "\n".join(
                error_message
                for error_list in parent_password_change_form.errors.values()
                for error_message in error_list
            )
            messages.error(request, error_messages)

    return render (request, 'app/parent/password_change.html', context={
        'parent_password_change_form': parent_password_change_form,})

# 保護者用 メールアドレス変更
@login_required
def parent_email_change(request):
    #保護者かどうか
    if request.user.family_member.role != Family_member.PARENT:
        messages.error(request, "保護者のみアクセスできます")
        return redirect("child_home")
    
    
    form = EmailChangeForm(request.POST or None, user=request.user)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "メールアドレスを変更しました")
        return redirect("parent_mypage")

    return render(request, "app/parent/email_change.html", {
        "email_change_form": form,
        "current_email": request.user.email,  # 現在のメールアドレス表示用
    })

# 保護者用 アイコン変更
@login_required
def parent_icon_change(request):

    #保護者かどうか
    if request.user.family_member.role != Family_member.PARENT:
        messages.error(request, "保護者のみアクセスできます")
        return redirect("child_home")

    # 表示したいアイコン一覧
    target_paths = [
        "icons/pengin_6.png",
        "icons/octopus_7.png",
        "icons/tortoise_8.png",
        "icons/whale_9.png",
        "icons/dolphin_10.png",
    ]
    icons = Icon.objects.filter(image_url__in=target_paths).order_by("id")
    current_icon = request.user.icon
    # 選択　保存
    if request.method == "POST":
        icon_id = request.POST.get("icon_id")
        if not icon_id:
        # 選択していない（事故防止）
            return render(
                request,
                "app/parent/icon_change.html",
                {"icons": icons, "current_icon": current_icon, "error": "アイコンを選択してください"}
            )

        icon = get_object_or_404(Icon, id=int(icon_id))
        request.user.icon = icon
        request.user.save(update_fields=["icon"])
        return redirect("parent_mypage")
        

    return render (request, 'app/parent/icon_change.html',
                   {"icons": icons, "current_icon": current_icon})