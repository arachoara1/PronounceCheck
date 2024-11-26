from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        label="아이디",
        widget=forms.TextInput(attrs={'placeholder': '아이디를 입력하세요'}),
    )
    email = forms.EmailField(
        required=True,
        label="이메일",
        widget=forms.EmailInput(attrs={'placeholder': '이메일을 입력하세요'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']  # `username` 필드로 변경

    def clean_username(self):  # `id` 대신 `username`으로 변경
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("이미 사용 중인 아이디입니다.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(  # `id`를 `username`으로 변경
        label="아이디",
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': '아이디를 입력하세요'}),
    )
    password = forms.CharField(
        label="비밀번호",
        widget=forms.PasswordInput(attrs={'placeholder': '비밀번호를 입력하세요'}),
    )
