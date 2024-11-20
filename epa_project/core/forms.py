from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    id = forms.CharField(
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
        fields = ['id', 'email', 'password1', 'password2']  # 필드 순서 수정

    def clean_id(self):
        id = self.cleaned_data.get('id')
        if User.objects.filter(username=id).exists():  # `username` 필드에 매핑
            raise forms.ValidationError("이미 사용 중인 아이디입니다.")
        return id

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['id']  # `id`를 `username`으로 저장
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    id = forms.CharField(
        label="아이디",
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': '아이디를 입력하세요'}),
    )
    password = forms.CharField(
        label="비밀번호",
        widget=forms.PasswordInput(attrs={'placeholder': '비밀번호를 입력하세요'}),
    )
