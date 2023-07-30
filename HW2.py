from django.apps import AppConfig
from django.contrib import admin
from .models import AbstractUser, ShopUser, ShopUserProfile
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from django.forms import forms, HiddenInput, ModelForm
import random
import hashlib
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver



class AuthappConfig(AppConfig):
    name = 'authapp'

class AbstractUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_active')
    list_display_links = ('username', 'first_name', 'last_name', 'email')
    search_fields = ('username', 'first_name', 'last_name', 'email')


admin.site.register(ShopUser, AbstractUserAdmin)


class ShopUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'tagline', 'aboutMe', 'gender')
    list_display_links = ('user', 'tagline', 'aboutMe', 'gender')
    search_fields = ('user', 'tagline', 'aboutMe', 'gender')


admin.site.register(ShopUserProfile, ShopUserProfileAdmin)

class ShopUserLoginForm(AuthenticationForm):
    class Meta:
        model = ShopUser
        fields = ('username', 'password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'footer_subscribe_input'
            if (field_name == 'username'):
                field.widget.attrs['placeholder'] = 'Введите логин'
            if (field_name == 'password'):
                field.widget.attrs['placeholder'] = 'и пароль'
            field.label = ''  

class ShopUserRegisterForm(UserCreationForm):
    class Meta:
        model = ShopUser
        fields = ('username', 'first_name', 'password1', 'password2', 'email', 'age', 'avatar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'footer_subscribe_input'
            field.help_text = '' 
            if (field_name == 'username'):
                field.widget.attrs['placeholder'] = 'Придумайте логин'
            if (field_name == 'first_name'):
                field.widget.attrs['placeholder'] = 'Введите ваше имя'
            if (field_name == 'password1'):
                field.widget.attrs['placeholder'] = 'Придумайте пароль'
            if (field_name == 'password2'):
                field.widget.attrs['placeholder'] = 'повторите пароль'
            if (field_name == 'email'):
                field.widget.attrs['placeholder'] = 'Введите e-mail'
            if (field_name == 'age'):
                field.widget.attrs['placeholder'] = 'Ваш возраст'
            if (field_name != 'avatar'):
                field.label = ''  

    def clean_age(self):  
        data = self.cleaned_data['age']
        if data < 18:
            raise forms.ValidationError("Вы слишком молоды!")
        return data  

    def save(self):
        user = super(ShopUserRegisterForm, self).save()  
        user.is_active = False
        salt = hashlib.sha1(str(random.random()).encode('utf8')).hexdigest()[:6]  
        user.activation_key = hashlib.sha1((user.email + salt).encode('utf8')).hexdigest()
        user.save()  
        return user  


class ShopUserUpdateForm(UserChangeForm):
    class Meta:
        model = ShopUser
        fields = ('username', 'first_name', 'email', 'age', 'avatar',
                  'password')  # без поля password невозможно сохранить изменения

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'footer_subscribe_input'
            if (field_name == 'username'):
                field.label = 'Логин'
            field.widget.attrs['placeholder'] = ('Введите ' + str(field.label)).capitalize()
            field.label = ''  
            field.help_text = ''  
            if field_name == 'password':
                field.widget = HiddenInput()  

    def clean_age(self):  
        data = self.cleaned_data['age']
        if data < 18:
            raise forms.ValidationError("Вы слишком молоды!")
        return data


class ShopUserProfileEditForm(ModelForm):
    class Meta:
        model = ShopUserProfile
        fields = ('tagline', 'aboutMe', 'gender')

    def __init__(self, *args, **kwargs):
        super(ShopUserProfileEditForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'footer_subscribe_input'
            field.widget.attrs['placeholder'] = ('Введите ' + str(field.label)).capitalize()
            field.label = '' 

class ShopUser(AbstractUser):
    avatar = models.ImageField(upload_to='users_avatars', blank=True)  # ImageField не будет работать без pillow
    age = models.PositiveIntegerField(verbose_name='Возраст пользователя', default=18)
    activation_key = models.CharField(max_length=128, blank=True)
    activation_key_expires = models.DateTimeField(default=(now() + timedelta(hours=48)))

    def is_activation_key_expired(self):
        if now() <= self.activation_key_expires:
            return False
        else:
            return True


class ShopUserProfile(models.Model):
    MALE = 'M'
    FEMALE = 'W'
    GENDER_CHOICES = (
        (None, 'Выберите пол'),
        (MALE, 'мужчина'),
        (FEMALE, 'женщина'),
    )
    # создание связи «один-к-одному» и создается индекс
    user = models.OneToOneField(ShopUser, unique=True, null=False, db_index=True, on_delete=models.CASCADE)
    tagline = models.CharField(verbose_name='Теги', max_length=128, blank=True)
    aboutMe = models.TextField(verbose_name='О себе', max_length=512, blank=True)
    # получаем фиксированный набор значений, которые прописаны в кортеже GENDER_CHOICES
    gender = models.CharField(verbose_name='Пол', max_length=1, choices=GENDER_CHOICES, blank=True)

    class Meta:
        verbose_name_plural = 'Профили пользователей в соцсетях'
        verbose_name = 'Профиль пользователя'
        ordering = ['user']

    @receiver(post_save, sender=ShopUser)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            ShopUserProfile.objects.create(user=instance)

    @receiver(post_save, sender=ShopUser)  # при получении определенных сигналов вызывает задекорированный метод
    def save_user_profile(sender, instance, **kwargs):
        # из модели ShopUser можно получить доступ к связанной модели по ее имени как к атрибуту
        instance.shopuserprofile.save()

class ShopUser(AbstractUser):
    avatar = models.ImageField(upload_to='users_avatars', blank=True)  # ImageField не будет работать без pillow
    age = models.PositiveIntegerField(verbose_name='Возраст пользователя', default=18)
    activation_key = models.CharField(max_length=128, blank=True)
    activation_key_expires = models.DateTimeField(default=(now() + timedelta(hours=48)))

    def is_activation_key_expired(self):
        if now() <= self.activation_key_expires:
            return False
        else:
            return True


class ShopUserProfile(models.Model):
    MALE = 'M'
    FEMALE = 'W'
    GENDER_CHOICES = (
        (None, 'Выберите пол'),
        (MALE, 'мужчина'),
        (FEMALE, 'женщина'),
    )
    # создание связи «один-к-одному» и создается индекс
    user = models.OneToOneField(ShopUser, unique=True, null=False, db_index=True, on_delete=models.CASCADE)
    tagline = models.CharField(verbose_name='Теги', max_length=128, blank=True)
    aboutMe = models.TextField(verbose_name='О себе', max_length=512, blank=True)
    # получаем фиксированный набор значений, которые прописаны в кортеже GENDER_CHOICES
    gender = models.CharField(verbose_name='Пол', max_length=1, choices=GENDER_CHOICES, blank=True)

    class Meta:
        verbose_name_plural = 'Профили пользователей в соцсетях'
        verbose_name = 'Профиль пользователя'
        ordering = ['user']

    @receiver(post_save, sender=ShopUser)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            ShopUserProfile.objects.create(user=instance)

    @receiver(post_save, sender=ShopUser)  # при получении определенных сигналов вызывает задекорированный метод
    def save_user_profile(sender, instance, **kwargs):
        # из модели ShopUser можно получить доступ к связанной модели по ее имени как к атрибуту
        instance.shopuserprofile.save()