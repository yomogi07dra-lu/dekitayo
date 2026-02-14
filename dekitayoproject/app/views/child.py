from django.shortcuts import render,redirect, get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .. models import Item,DailyLogItem,Daily_log, Icon
from datetime import date, timedelta
from .. forms import DailyLogForm, EmailChangeForm, PasswordChangeForm
from .utils import get_current_child
import calendar


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
#子ども用ホーム・過去学習記録
def child_home(request, year=None, month=None, day=None):
    if year and month and day:
        today = date(year, month, day)                    
    else:
        today = timezone.localdate() #　指定なければ今日
    
    family = request.user.family_member.family

    # 共通関数：ログイン中のユーザーに紐づくchild取得
    child = get_current_child(request)

    # 今日の学習記録
    daily_log = Daily_log.objects.filter(
        child=child,
        date=today,
    ).first() # 最新取得

    # 今日の学習項目　取得 （表示対象（active）のみ）
    items = list(
        Item.objects
        .filter(family=family, child=child, is_active=True)
        .order_by("color_index")
    )

    # 空の箱　今日の記録がなかった場合エラーにならないように　対象：学習項目
    checked_item_ids = []

    # 空の箱　今日の記録がなかった場合エラーにならないように　対象：保護者コメント
    parent_comments = []

    # 今日のチェックされた学習項目　取得
    if daily_log is not None:
        checked_item_ids = list(
            DailyLogItem.objects
            .filter(daily_log=daily_log)
            .values_list("item_id", flat=True) # idリストとして取得
        )
        parent_comments = (
        daily_log.parent_comments
        .select_related("user", "user__icon")   # コメントした保護者のアイコン
        .order_by("-created_at")           # コメント新しい順
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

    return render(request, "app/child/home.html", {
        "today": today,
        "day": today.day,
        "year": year,
        "month": month,
        "daily_log": daily_log,
        "parent_comments": parent_comments,
        "rows": rows,
        "checked_item_ids": checked_item_ids,
        "is_past": today != timezone.localdate(),  #過去学習記録用のテンプレートで使用
    })

    # 子ども・保護者のコメントは表示なのでテンプレート


# 子ども用　学習記録　登録 
@login_required
def child_record(request, year=None, month=None, day=None):

    # 対象日（指定がなければ今日）
    if year and month and day:
        target_date = date(int(year), int(month), int(day))
    else:
        target_date = timezone.localdate()

    # 子ども所属家族取得
    family = request.user.family_member.family 
    
    
    # 共通関数：ログイン中のユーザーに紐づくchild取得
    child = get_current_child(request)

    # 学習項目　取得 （表示対象（active）のみ）
    items = list(Item.objects.filter(family=family, child=child, is_active=True).order_by("color_index"))

    # 指定日の学習記録
    daily_log = Daily_log.objects.filter(
        child=child,
        date=target_date
    ).first() #最新取得
    
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

    item_rows = [row for row in rows if row.get("item")]

    if request.method == "POST":
        form = DailyLogForm(request.POST, request.FILES, instance=daily_log)

        if form.is_valid():
            checked_item_ids = request.POST.getlist("item_ids")#チェックされた項目

            # 保存してよい学習項目（is_active=True）のID一覧をDBから取得する
            # inactive の item_id が混ざる可能性が残っているため
            active_items_queryset = Item.objects.filter(
                family=family,
                child=child,
                is_active=True
            )
            active_item_id_list = list(
                active_items_queryset.values_list("id", flat=True)
            )
            # 比較しやすいように、許可IDを set にする（検索が速い）
            allowed_item_id_set = set(active_item_id_list)

            # 送られてきたIDの中から、許可されているものだけ残す
            filtered_checked_item_ids = []
            for item_id in checked_item_ids:
                if int(item_id) in allowed_item_id_set:
                    filtered_checked_item_ids.append(item_id)

            # 以降の保存処理では、絞り込んだIDだけを使う
            checked_item_ids = filtered_checked_item_ids


            with transaction.atomic():#同じ日なら更新、なければ新規作成
                daily_log, created = Daily_log.objects.update_or_create(
                    child=child,
                    date=target_date,
                    defaults={"user": request.user},  
                )

                # コメント・写真を保存
                daily_log.child_comment = form.cleaned_data["child_comment"]

                # 　写真：削除チェックがあれば None を優先（ソフト削除）
                delete_photo1 = request.POST.get("delete_photo1") == "1"
                delete_photo2 = request.POST.get("delete_photo2") == "1"

                if delete_photo1:
                    daily_log.photo1_url = None
                elif form.cleaned_data.get("photo1_url"):
                    daily_log.photo1_url = form.cleaned_data["photo1_url"]

                if delete_photo2:
                    daily_log.photo2_url = None
                elif form.cleaned_data.get("photo2_url"):
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
            return redirect("child_home_by_date", year=target_date.year, month=target_date.month, day=target_date.day)
    
    else:
        if daily_log is not None:
            form = DailyLogForm(instance=daily_log)
        else:
            form = DailyLogForm()
    
    return render(request, "app/child/record.html",{
        "today": target_date,        
        "form": form,
        "rows": rows,
        "checked_item_ids": checked_item_ids,
        "is_past": target_date != timezone.localdate(),
        "item_rows": item_rows,
        "daily_log": daily_log,
    })
    


# 子ども用　月間学習記録カレンダー
@login_required
def child_monthly_calendar(request, year=None, month=None):
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

    # 共通関数：ログイン中のユーザーに紐づくchild取得
    child = get_current_child(request)

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
    # 過去の記録遷移
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
        "year": year,
        "month": month,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "calendar_days": calendar_days, 
        "learned_days": learned_days,
    }

    return render (request, 'app/child/monthly_calendar.html',context)


# 子ども用月間学習記録グラフ
@login_required
def child_monthly_graph(request, year=None, month=None):

    # 共通関数：ログイン中のユーザーに紐づくchild取得
    child = get_current_child(request)

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
        "child_id": child.id,
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

    return render (request, 'app/child/monthly_graph.html', context)

# 子ども用週間学習記録グラフ
@login_required
def child_weekly_graph(request, year=None, month=None, day=None):

    # 共通関数：ログイン中のユーザーに紐づくchild取得
    child = get_current_child(request)

    #日付
    today = timezone.localdate()
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
        "child_id": child.id,
        "labels": labels,
        "counts": counts,
        "start_date": start_date,
        "end_date": end_date,
        "prev_year": prev_base.year, "prev_month": prev_base.month, "prev_day": prev_base.day,
        "next_year": next_base.year, "next_month": next_base.month, "next_day": next_base.day,
    }

    return render (request, 'app/child/weekly_graph.html', context)





# 子ども用マイページ
@login_required
def child_mypage(request):
    # 共通関数：ログイン中のユーザーに紐づくchild取得
    child = get_current_child(request)

    return render (request, 'app/child/mypage.html')

# 子ども用 アイコン変更
@login_required
def child_icon_change(request):
    
    # 共通関数：ログイン中のユーザーに紐づくchild取得
    child = get_current_child(request)

    # 表示したいアイコン一覧
    target_paths = [
        "icons/cat_1.png",
        "icons/wolf_2.png",
        "icons/deer_3.png",
        "icons/squirrel_4.png",
        "icons/tiger_5.png",
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
                "app/child/icon_change.html",
                {"icons": icons, "current_icon": current_icon, "error": "アイコンを選択してください"}
            )

        icon = get_object_or_404(Icon, id=int(icon_id))
        request.user.icon = icon
        request.user.save(update_fields=["icon"])
        return redirect("child_mypage")
        
    return render (request, 'app/child/icon_change.html',
        {"icons": icons, "current_icon": current_icon})


# 子ども用 パスワード変更
@login_required
def child_password_change(request): 
    
    # 共通関数：ログイン中のユーザーに紐づくchild取得
    child = get_current_child(request)

    child_password_change_form = PasswordChangeForm(
        user=request.user,
        data=request.POST or None
    )
    if request.method == "POST":
        if child_password_change_form.is_valid():
            child_password_change_form .save()
            update_session_auth_hash(request, request.user)
        # 成功メッセージ（モーダルで表示する）
            messages.success(request, "パスワードを変更しました")
            return redirect("child_password_change")
        
        else:
        # 失敗メッセージ・フォームのエラー文だけフィールド名は表示しない（モーダルで表示する）
            error_messages = "\n".join(
                error_message
                for error_list in child_password_change_form.errors.values()
                for error_message in error_list
            )

            messages.error(request, error_messages)
        
    
    return render (request, 'app/child/password_change.html', context={
        'child_password_change_form': child_password_change_form,
    })

# 子ども用 メールアドレス変更
@login_required
def child_email_change(request): 
    
    # 共通関数：ログイン中のユーザーに紐づくchild取得
    child = get_current_child(request)

    form = EmailChangeForm(request.POST or None, user=request.user)
        
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "メールアドレスを変更しました")
        return redirect("child_mypage")

    return render(request, "app/child/email_change.html", {
        "email_change_form": form,
        "current_email": request.user.email,  # 現在のメールアドレス表示用
    })


        