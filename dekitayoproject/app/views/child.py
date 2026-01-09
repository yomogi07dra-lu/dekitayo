from django.shortcuts import render,redirect, get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .. models import Child,Family_member,Item,DailyLogItem,Daily_log, Icon, ParentComment
from datetime import date, timedelta
from .. forms import DailyLogForm, EmailChangeForm, PasswordChangeForm
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

    #ログイン中のユーザーに紐づくchild取得
    child = get_object_or_404(
        Child,
        user=request.user,
        family_member__family=family,
        family_member__role=Family_member.CHILD,
    )

    # 今日の学習記録
    daily_log = Daily_log.objects.filter(
        child=child,
        date=today,
    ).first() # 最新取得

    # 今日の学習項目　取得
    items = list(
        Item.objects
        .filter(family=family, child=child)
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
        .order_by("-id")           # コメント新しい順
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
        "daily_log": daily_log,
        "parent_comments": parent_comments,
        "rows": rows,
        "checked_item_ids": checked_item_ids,
        "is_past": today != timezone.localdate(),  #過去学習記録用のテンプレートで使用
    })

    # 子ども・保護者のコメントは表示なのでテンプレート


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

    # ログインしているユーザーに紐づくChildレコードが存在しない場合(なくても動く)  
    if child is None:
        logout(request)
        return redirect("login")  
    
    items = list(Item.objects.filter(family=family, child=child).order_by("color_index"))


    # 今日の学習項目
    daily_log = Daily_log.objects.filter(
        child=child,
        date=today
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

    if request.method == "POST":
        form = DailyLogForm(request.POST, request.FILES)

        if form.is_valid():
            checked_item_ids = request.POST.getlist("item_ids")#チェックされた項目

            with transaction.atomic():#同じ日なら更新、なければ新規作成
                daily_log, created = Daily_log.objects.update_or_create(
                    child=child,
                    date=today,
                    defaults={"user": request.user},  
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
    
    
    return render(request, "app/child/record.html",{
        "today": today,        
        "form": form,
        "rows": rows,
        "checked_item_ids": checked_item_ids,
    })


# 子ども用　月間学習記録カレンダー
def child_monthly_calendar(request, year=None, month=None):
    today = date.today()
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

    #ログイン中のユーザーに紐づくchild取得
    family = request.user.family_member.family
    child = get_object_or_404(
        Child,
        user=request.user,
        family_member__family=family,
        family_member__role=Family_member.CHILD,
    )
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
    
    context = {
        "year": year,
        "month": month,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "month_days": month_days,
        "learned_days": learned_days,
    }

    return render (request, 'app/child/monthly_calendar.html',context)


# 子ども用月間学習記録グラフ
def child_monthly_graph(request, year=None, month=None):

    #ログイン中のユーザーに紐づくchild取得
    family = request.user.family_member.family
    child = get_object_or_404(
        Child,
        user=request.user,
        family_member__family=family,
        family_member__role=Family_member.CHILD,
    )
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
def child_weekly_graph(request, year=None, month=None, day=None):

    #ログイン中のユーザーに紐づくchild取得
    family = request.user.family_member.family
    child = get_object_or_404(
        Child,
        user=request.user,
        family_member__family=family,
        family_member__role=Family_member.CHILD,
    )

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
def child_mypage(request):
    family = request.user.family_member.family
    child = get_object_or_404(
        Child,
        user=request.user,
        family_member__family=family,
        family_member__role=Family_member.CHILD,
    )    

    return render (request, 'app/child/mypage.html')

# 子ども用 アイコン変更
@login_required
def child_icon_change(request):
    family = request.user.family_member.family
    child = get_object_or_404(
        Child,
        user=request.user,
        family_member__family=family,
        family_member__role=Family_member.CHILD,
    )
    # 表示したいアイコン一覧
    target_paths = [
        "icons\\cat_1.png",
        "icons\\wolf_2.png",
        "icons\\deer_3.png",
        "icons\\squirrel_4.png",
        "icons\\tiger_5.png",
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
    
    #　子どもかどうか
    family = request.user.family_member.family
    get_object_or_404(
        Child,
        user=request.user,
        family_member__family=family,
        family_member__role=Family_member.CHILD,
    )

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
        
        else:
        # 失敗メッセージ（モーダルで表示する）
            messages.error(request, "パスワードを変更できませんでした")
        
    
    return render (request, 'app/child/password_change.html', context={
        'child_password_change_form': child_password_change_form,
    })

# 子ども用 メールアドレス変更
@login_required
def child_email_change(request): 
    
    #　子どもかどうか
    family = request.user.family_member.family
    child = get_object_or_404(
        Child,
        user=request.user,
        family_member__family=family,
        family_member__role=Family_member.CHILD,
    )

    form = EmailChangeForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            current_email = form.cleaned_data["current_email"]
            new_email = form.cleaned_data["new_email"]

            if current_email != request.user.email:
                form.add_error(
                "current_email",
                "現在のメールアドレスが正しくありません"
            )
            else:
                request.user.email = new_email
                request.user.save()
                return redirect("child_mypage")

    return render (request, 'app/child/email_change.html', context={
        'email_change_form': form}
    )


        