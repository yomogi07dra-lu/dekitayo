from django import forms
from .models import Users
from .models import Family_members

class UsersModelForm(forms.ModelForm):
    
    class Meta:
        model = Users
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

class Family_membersModelForm(forms.ModelForm):

    class Meta:
        model = Family_members
        fields = ('role',)
        widgets = { 'role': forms.RadioSelect }

