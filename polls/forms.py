from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory

from .models import UserProfile, Question, Choice


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    avatar = forms.ImageField(required=True, help_text="Аватар обязателен")

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'avatar')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = UserProfile.objects.create(user=user, avatar=self.cleaned_data['avatar'])
        return user


class ProfileUpdateForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(), max_length=250, required=True)
    email = forms.EmailField(widget=forms.EmailInput(), required=True)

    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio', 'birth_date']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        user = self.user
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            super().save(commit=commit)
        return self.instance

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'image', 'question_user']
        widgets = {
            'question_user': forms.HiddenInput(),
        }

ChoiceFormSet = inlineformset_factory(Question, Choice, fields=('choice_text',))