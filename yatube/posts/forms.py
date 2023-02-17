from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {'text': 'Текст поста', 'group': 'Тематическая группа'}
        help_texts = {
            'text': 'это поле не может быть пустым',
            'group': 'выберете подходящую группу или оставьте пустым'
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Текст комментария'}
        help_texts = {
            'text': 'оставьте свой комментарий',
        }
