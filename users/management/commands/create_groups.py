from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = "Создает группы Менеджеры и Пользователи с соответствующими правами"

    def handle(self, *args, **options):
        self.stdout.write(" Создание групп и назначение прав")

        MANAGER_PERMISSIONS = [
            ("view_user", "users", "user"),
            ("view_mailing", "mailings", "mailing"),
            ("view_recipient", "mailings", "recipient"),
            ("view_message", "mailings", "message"),
            ("view_mailingattempt", "mailings", "mailingattempt"),
            ("change_user", "users", "user"),
            ("change_mailing", "mailings", "mailing"),
        ]

        USER_PERMISSIONS = [
            # Рассылки
            ("add_mailing", "mailings", "mailing"),
            ("change_mailing", "mailings", "mailing"),
            ("delete_mailing", "mailings", "mailing"),
            ("view_mailing", "mailings", "mailing"),
            # Получатели
            ("add_recipient", "mailings", "recipient"),
            ("change_recipient", "mailings", "recipient"),
            ("delete_recipient", "mailings", "recipient"),
            ("view_recipient", "mailings", "recipient"),
            # Сообщения
            ("add_message", "mailings", "message"),
            ("change_message", "mailings", "message"),
            ("delete_message", "mailings", "message"),
            ("view_message", "mailings", "message"),
        ]

        manager_group, created = Group.objects.get_or_create(name="Менеджеры")
        if created:
            self.stdout.write(self.style.SUCCESS('Группа "Менеджеры" создана'))
        else:
            self.stdout.write('Группа "Менеджеры" уже существует')

        manager_perms_count = 0
        for codename, app_label, model in MANAGER_PERMISSIONS:
            try:
                content_type = ContentType.objects.get(app_label=app_label, model=model)
                permission = Permission.objects.get(
                    content_type=content_type, codename=codename
                )
                manager_group.permissions.add(permission)
                manager_perms_count += 1
            except ContentType.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Не найден ContentType: {app_label}.{model}")
                )
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Не найдено право: {codename}"))

        self.stdout.write(
            self.style.SUCCESS(f"Менеджерам назначено {manager_perms_count} прав")
        )

        user_group, created = Group.objects.get_or_create(name="Пользователи")
        if created:
            self.stdout.write(self.style.SUCCESS('Группа "Пользователи" создана'))
        else:
            self.stdout.write('Группа "Пользователи" уже существует')

        user_perms_count = 0
        for codename, app_label, model in USER_PERMISSIONS:
            try:
                content_type = ContentType.objects.get(app_label=app_label, model=model)
                permission = Permission.objects.get(
                    content_type=content_type, codename=codename
                )
                user_group.permissions.add(permission)
                user_perms_count += 1
            except ContentType.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Не найден ContentType: {app_label}.{model}")
                )
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f" Не найдено право: {codename}"))

        self.stdout.write(
            self.style.SUCCESS(f"Пользователям назначено {user_perms_count} прав")
        )

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS(" ГРУППЫ СОЗДАНЫ И НАСТРОЕНЫ"))
        self.stdout.write("=" * 50)

        self.stdout.write("\n Группа 'Менеджеры' имеет права:")
        for perm in manager_group.permissions.all().order_by(
            "content_type__model", "codename"
        ):
            self.stdout.write(f"  • {perm.name}")

        self.stdout.write("\n Группа 'Пользователи' имеет права:")
        for perm in user_group.permissions.all().order_by(
            "content_type__model", "codename"
        ):
            self.stdout.write(f"  • {perm.name}")

        self.stdout.write(
            self.style.SUCCESS(
                "\n Все готово! Теперь можно назначать пользователей в группы."
            )
        )
