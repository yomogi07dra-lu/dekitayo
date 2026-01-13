from typing import Optional
from django.shortcuts import get_object_or_404
from ..models import Child, Family_member 

SESSION_CHILD_KEY = "selected_child_id"

# 共通関数　子どものセッションの取得　子どもアカウント削除時のセッション
def get_target_child(request) -> Optional[Child]:
    family = request.user.family_member.family

    # 家族の子ども一覧（先頭の定義を固定）
    children = (
        Child.objects.filter(
            family_member__family=family,
            family_member__role=Family_member.CHILD,
        )
        .select_related("user")
        .order_by("id")
    )

    # 子どもが0人なら None（セッションも消す）
    if not children.exists():
        request.session.pop(SESSION_CHILD_KEY, None)
        return None

    # セッションの子IDが有効ならその子
    session_child_id = request.session.get(SESSION_CHILD_KEY)
    if session_child_id:
        child = children.filter(id=session_child_id).first()
        if child:
            return child

    # セッションが無効なら先頭の子（セッションも更新）
    first_child = children.first()
    request.session[SESSION_CHILD_KEY] = first_child.id
    return first_child

# 共通関数　ログイン中ユーザーに紐づくChildを返す。子どもでなければ404
def get_current_child(request) -> Child:
    family = request.user.family_member.family
    return get_object_or_404(
        Child,
        user=request.user,
        family_member__family=family,
        family_member__role=Family_member.CHILD,
    )