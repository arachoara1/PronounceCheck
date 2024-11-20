from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label="이메일")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("이미 등록된 이메일입니다.")
        return email


class LoginForm(forms.Form):
    username = forms.CharField(label="아이디", max_length=150)
    password = forms.CharField(label="비밀번호", widget=forms.PasswordInput)
