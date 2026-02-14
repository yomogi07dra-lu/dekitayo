from django import forms
from .models import User,Family_member,Item,Invitation,Daily_log, ParentComment
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

#新規登録
class UsersModelForm(forms.ModelForm):
    invitation_code = forms.CharField(
        label='招待コード',
        max_length=6,
        required=False
    )
    # 追加：確認用パスワード（DBには保存しない）
    confirm_password_input = forms.CharField(
        label='パスワード（確認）',
        required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'もう一度同じパスワードを入力してください'
        })
    )

    class Meta:
        model = User
        fields = ["email", "password", "username"]
        labels = {
            'email': 'メールアドレス',
            'password': 'パスワード',
            'username': 'ユーザー名',
        }
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'test@test.com'
            }),
            'password': forms.PasswordInput(attrs={
                'placeholder': '8文字以上、英字と数字、記号が使用できます'
            }),
            'username': forms.TextInput(attrs={
                'placeholder': 'ママ'
            }),
        }

        help_texts = {
            "username": "",
        }

    def clean(self):
        cleaned_data =super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password_input')

        # 一致チェック
        if password and confirm and password != confirm:
            self.add_error('confirm_password_input', 'パスワードが一致しません')

        if password:
            try:
                validate_password(password, self.instance)
            except ValidationError as e:
                self.add_error('password', e)
        return cleaned_data
        
    def clean_invitation_code(self):
        code = self.cleaned_data.get('invitation_code')

        if not code:
            return code
        
        invite = Invitation.objects.filter(
            code=code,
            is_active=True
        ).first()

        if not invite:
            raise forms.ValidationError('無効な招待コードです')

        self.invite = invite
        return code
    
    def save(self,commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
    

#新規登録　子ども・保護者分け
class Family_membersModelForm(forms.ModelForm):

    class Meta:
        model = Family_member
        fields = ('role',)
        labels = {
            'role': '',
        }
        widgets = { 'role': forms.RadioSelect }

#ログイン
class LoginForm(forms.Form):
    email = forms.EmailField(label="メールアドレス")
    password = forms.CharField(
        label="パスワード",
        widget=forms.PasswordInput()
    )

#パスワード再設定　メールアドレス入力
class RequestPasswordResetForm(forms.Form):
    email = forms.EmailField(
        label='メールアドレス',
        widget=forms.EmailInput()
    )

    def clean_email(self):
        email =self.cleaned_data['email']
        return email
    
#パスワード再設定　新しいパスワード
class SetNewPasswordForm(forms.Form):
    password1 = forms.CharField(
        label='新しいパスワード',
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '8文字以上、英字と数字、記号を使用できます',
            }
        ),
    )
    password2 = forms.CharField(
        label='新しいパスワード再入力',
        widget=forms.PasswordInput(),
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 =cleaned_data.get('password1')
        password2 =cleaned_data.get('password2')

        if password1 and password2:
            if password1 != password2:
                raise ValidationError('パスワードを再設定できませんでした')
            
        return cleaned_data

#保護者用　学習項目登録
class ItemForm(forms.ModelForm):

    class Meta:
        model = Item
        fields = ['item_name']
        labels = {
            'item_name': '',}
        widgets = {
            "item_name": forms.TextInput(attrs={
                "class": "item-input",
            })
        }

# 子ども用　学習記録　項目登録 #
class DailyLogForm(forms.ModelForm):
    child_comment = forms.CharField(
    required=False,
    widget=forms.Textarea(attrs={
        "placeholder": "コメント：学習時間や感想、絵文字OK（最大100文字）",
        "maxlength": 100,  # フロント側補助
        "rows": 3,
    }),
    label="",
    )
    
    class Meta:
        model = Daily_log
        fields = ["child_comment", "photo1_url", "photo2_url"]
        labels = {
            'photo1_url': '',
            'photo2_url': '',
        }
    
     # 改行コードを統一して「見た目」と同じ数え方にする
    def clean_child_comment(self):
        comment = self.cleaned_data.get("child_comment", "")
        # Windowsの \r\n を \n に統一（改行を1文字扱いに）
        comment = comment.replace("\r\n", "\n").replace("\r", "\n")
        if len(comment) > 100:
            raise forms.ValidationError(
                "改行もふくめて100文字までです\n少しだけみじかくしてみよう!" #　もしもの時用
            )
        return comment

#保護者用コメント
class ParentCommentForm(forms.ModelForm):
    text = forms.CharField(
        required=True,
        max_length=100,  # サーバ側で必ず制限
        error_messages={
            "max_length": "コメントは改行を含め100文字以内で入力してください",
        },
        widget=forms.Textarea(attrs={
            "rows": 3,
            "maxlength": 100,  # フロント側補助
            "placeholder": "最大100字",
        }),
        label="",
    )

    class Meta:
        model = ParentComment        
        fields = ["text"]

# パスワード変更
class PasswordChangeForm(PasswordChangeForm):

    old_password = forms.CharField(
        label="現在のパスワード",
        widget=forms.PasswordInput()
    )
    new_password1 = forms.CharField(
        label="新しいパスワード",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "8文字以上・英字と数字、記号を使用できます"
            }
        ),
    )
    new_password2 = forms.CharField(
        label="新しいパスワード（再入力）",
        widget=forms.PasswordInput()
    )

# メールアドレス変更
User = get_user_model()

class EmailChangeForm(forms.Form):
    new_email = forms.EmailField(label="新しいメールアドレス")

    # ログイン中ユーザーを受け取る
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    # 新メールが他人と重複していないかチェック
    def clean_new_email(self):
        new = self.cleaned_data["new_email"]
        if User.objects.filter(email=new).exclude(id=self.user.id).exists():
            raise forms.ValidationError("このメールアドレスは既に使用されています")
        return new

    # 保存
    def save(self):
        self.user.email = self.cleaned_data["new_email"]
        self.user.save(update_fields=["email"])
        return self.user



