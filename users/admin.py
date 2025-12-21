from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
    )
    list_filter = ("is_active", "is_staff", "role", "country")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Персональная информация",
            {
                "fields": (
                    "username",
                    "first_name",
                    "last_name",
                    "phone_number",
                    "country",
                    "avatar",
                )
            },
        ),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_blocked",
                    "role",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )

    def get_fieldsets(self, request, obj=None):

        fieldsets = super().get_fieldsets(request, obj)

        if obj and obj.is_superuser:

            custom_fieldsets = []
            for name, field_options in fieldsets:
                fields = field_options["fields"]

                if name == "Права доступа":
                    fields = tuple(f for f in fields if f != "role")

                    field_options = {
                        "fields": fields,
                        "description": 'Суперпользователь имеет все права. Поле "Роль" не применяется.',
                    }

                custom_fieldsets.append((name, field_options))

            return custom_fieldsets

        return fieldsets

    def get_readonly_fields(self, request, obj=None):

        readonly_fields = super().get_readonly_fields(request, obj)

        if obj and obj.is_superuser:

            if "role" not in readonly_fields:
                readonly_fields = list(readonly_fields) + ["role"]

        return readonly_fields
