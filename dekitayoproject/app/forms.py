from django import forms
from .models import Users
from .models import Family_members
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

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

    def clean(self):
        clean_data =super().clean()
        password = clean_data.get('password')
        try:
            validate_password(password, self.instance)
        except ValidationError as e:
            self.add_error('password', e)
        return clean_data
        
    def save(self,commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class Family_membersModelForm(forms.ModelForm):

    class Meta:
        model = Family_members
        fields = ('role',)
        labels = {
            'role': '',
        }
        widgets = { 'role': forms.RadioSelect }


class LoginForm(forms.Form):
    email = forms.EmailField(label="メールアドレス")
    password = forms.CharField(label="パスワード")


class RequestPasswordResetForm(forms.Form):
    email = forms.EmailField(
        label='メールアドレス',
        widget=forms.EmailInput()
    )

    def clean_email(self):
        email =self.cleaned_data['email']
        if not Users.objects.filter(email=email).exists():
            raise ValidationError('このメールアドレスのユーザーは存在しません')
        return email
    

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