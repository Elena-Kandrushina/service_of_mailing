from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Кастомная модель пользователя"""

    ROLE_CHOICES = [
        ("user", "Пользователь"),
        ("manager", "Менеджер"),
    ]

    email = models.EmailField(_("email address"), unique=True)
    phone_number = models.CharField(
        max_length=15,
        verbose_name="Телефон",
        blank=True,
        null=True,
        help_text="Введите номер телефона",
    )
    country = models.CharField(
        max_length=35,
        verbose_name="Страна",
        blank=True,
        null=True,
        help_text="Введите страну",
    )
    avatar = models.ImageField(
        upload_to="users/avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар",
        help_text="Загрузите фото",
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default="user", verbose_name="Роль"
    )
    is_blocked = models.BooleanField(default=False, verbose_name="Заблокирован")

    mailings = models.ManyToManyField(
        "mailings.Mailing",
        related_name="users",
        blank=True,
        verbose_name="Рассылки пользователя",
    )

    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to.",
        related_name="custom_user_set",
        related_query_name="custom_user",
    )

    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="custom_user_set",
        related_query_name="custom_user",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_manager(self):
        return self.role == "manager"

    def can_edit_mailing(self, mailing):

        if self.is_manager:
            return False
        return mailing in self.mailings.all() or self.is_superuser
