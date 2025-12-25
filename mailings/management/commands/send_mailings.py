from django.core.management.base import BaseCommand
from django.utils import timezone
from mailings.models import Mailing


class Command(BaseCommand):
    help = "Отправляет запланированные рассылки"

    def handle(self, *args, **options):
        now = timezone.now()

        mailings_to_send = Mailing.objects.filter(
            start_time__lte=now, end_time__gte=now, status="Запущена"
        )

        self.stdout.write(f"Найдено {mailings_to_send.count()} рассылок для отправки")

        for mailing in mailings_to_send:
            self.stdout.write(f"Отправка рассылки #{mailing.id}...")
            success, message = mailing.send_mailing()

            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"Рассылка #{mailing.id} отправлена: {message}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Ошибка при отправке рассылки #{mailing.id}: {message}"
                    )
                )
