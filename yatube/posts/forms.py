from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Текст поста', 'group': 'Сообщество',
                  'image': 'Фото поста'}

    def clean_text(self):
        data = self.cleaned_data['text']

        if not data:
            raise forms.ValidationError('Поле не должно быть пустым!')

        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Текст комментария'}
        help_text = 'Напишиште ваше мнение о посте'

    def clean_text(self):
        data = self.cleaned_data['text']

        if not data:
            raise forms.ValidationError('Поле не должно быть пустым!')
        return data
