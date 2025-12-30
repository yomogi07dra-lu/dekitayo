from django.shortcuts import render,redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .. models import Child,Family_member,Item,Invitation,DailyLogItem,Daily_log
from datetime import date, timedelta
from .. forms import ItemForm, ParentCommentForm
import uuid, calendar
from .. utils import generate_invite_code

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
        return render(request, "app/parent/home.html", {
            "today": today,
            "child": None,
        })

    # 今日の学習記録　取得
    daily_log = Daily_log.objects.filter(
        child=child,
        date=today,
    ).first() #最新取得

    # 今日の学習項目　取得
    items = list(
        Item.objects
        .filter(family=family, child=child)
        .order_by("color_index")
    )
    # 空の箱　今日の記録がなかった場合エラーにならないように
    checked_item_ids = []

    # 今日のチェックされた学習項目　取得
    if daily_log is not None:
        checked_item_ids = list(
            DailyLogItem.objects
            .filter(daily_log=daily_log)
            .values_list("item_id", flat=True) # idリストとして取得
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

    return render(request, "app/parent/home.html", {
        "today": today,
        "child": child,
        "daily_log": daily_log,
        "rows": rows,
        "checked_item_ids": checked_item_ids,
        "comment_form": form,
    })

#保護者用学習項目登録
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
        "app/parent/item_manage.html",
        {
            "child": child,
            "item_form": form,
            "rows": rows,
        },
    )

# 保護者用　過去記録
def parent_daily_detail(request,child_id=None):
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

        

    return render (request, 'app/parent/daily_detail.html')

# 保護者用月間学習記録カレンダー
def parent_monthly_calendar(request):

    return render (request, 'app/parent/monthly_calendar.html')


# 保護者用マイページ
def parent_mypage(request):

    return render (request, 'app/parent/mypage.html')

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

    return render(request, 'app/parent/invitation.html', {
        'invite': invite
    })

# 保護者用 兄弟姉妹切替
def parent_child_switch(request):

    return render (request, 'app/parent/child_switch.html')


# 保護者用月間学習記録グラフ
def parent_monthly_graph(request):

    return render (request, 'app/parent/monthly_graph.html')

# 保護者用週間学習記録グラフ
def parent_weekly_graph(request):

    return render (request, 'app/parent/weekly_graph.html')
