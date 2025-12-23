from django import forms
from .models import User,Family_member,Item,Invitation,Daily_log, ParentComment
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

#新規登録
class UsersModelForm(forms.ModelForm):
    invitation_code = forms.CharField(
        label='招待コード',
        max_length=6,
        required=False
    )

    class Meta:
        model = User
        fields = ["email", "password","username"]
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
                'placeholder': '8文字以上、英字と数字を組み合わせてください'
            }),
            'username': forms.TextInput(attrs={
                'placeholder': 'はなこ'
            }),
        }

        help_texts = {
            "username": "",
        }

    def clean(self):
        clean_data =super().clean()
        password = clean_data.get('password')
        if password:
            try:
                validate_password(password, self.instance)
            except ValidationError as e:
                self.add_error('password', e)
        return clean_data
        
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
    password = forms.CharField(label="パスワード")

#パスワード再設定　メールアドレス入力
class RequestPasswordResetForm(forms.Form):
    email = forms.EmailField(
        label='メールアドレス',
        widget=forms.EmailInput()
    )

    def clean_email(self):
        email =self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise ValidationError('このメールアドレスのユーザーは存在しません')
        return email
    
#パスワード再設定　新しいパスワード
class SetNewPasswordForm(forms.Form):
    password1 = forms.CharField(
        label='新しいパスワード',
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '8文字以上、英字と数字を組み合わせてください',
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
    
    class Meta:
        model = Daily_log
        fields = ["child_comment", "photo1_url", "photo2_url"]
        labels = {
            'photo1_url': '',
            'photo2_url': '',
            'child_comment': '',
        }
        widgets = {
            "child_comment": forms.Textarea(attrs={
            "placeholder": "コメント：学習時間や感想、絵文字OK（最大100文字）",
            "maxlength": 100,
            "rows": 3,
            }),
        }
#保護者用コメント
class ParentCommentForm(forms.ModelForm):
    class Meta:
        model = ParentComment        
        fields = ["text"]
        labels = {
            'text': '',
        }        
        widgets = {
            "parent_comment": forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "コメント：最大100字",
            })
        }
