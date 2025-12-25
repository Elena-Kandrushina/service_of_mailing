from django.contrib.auth import get_user_model
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


class Recipient(models.Model):
    """Модель получателя рассылки"""

    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_recipients",
        verbose_name="Владелец",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"

    def __str__(self):
        return f"{self.full_name} ({self.email})"


User = get_user_model()


class Message(models.Model):
    """Модель сообщения"""

    subject = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Владелец",
        related_name="messages",
        null=True,
        blank=True,
    )

    def get_total_recipients(self):
        """Получить общее количество уникальных получателей"""
        from django.db.models import Count

        recipients = Recipient.objects.filter(mailings__message=self).distinct().count()
        return recipients

    def get_total_attempts(self):
        """Получить общее количество попыток отправки"""
        total = 0
        for mailing in self.mailings.all():
            total += mailing.attempts.count()
        return total

    def get_last_sent_date(self):
        """Получить дату последней отправки"""
        last_attempt = (
            MailingAttempt.objects.filter(mailing__message=self)
            .order_by("-attempt_time")
            .first()
        )
        return last_attempt.attempt_time if last_attempt else None

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"

    def __str__(self):
        return self.subject


class Mailing(models.Model):
    """Модель рассылки"""

    STATUS_CHOICES = [
        ("Создана", "Создана"),
        ("Запущена", "Запущена"),
        ("Завершена", "Завершена"),
    ]

    start_time = models.DateTimeField(verbose_name="Дата и время начала отправки")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания отправки")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Создана", verbose_name="Статус"
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Сообщение",
    )
    recipients = models.ManyToManyField(
        Recipient, related_name="mailings", verbose_name="Получатели"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_mailings",
        verbose_name="Владелец",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-start_time"]

    def clean(self):
        """Валидация дат"""
        if self.start_time and self.end_time:
            if self.start_time < timezone.now():
                raise ValidationError(
                    {"start_time": "Дата начала не может быть в прошлом"}
                )
            if self.start_time >= self.end_time:
                raise ValidationError(
                    {"end_time": "Дата окончания должна быть позже даты начала"}
                )

    def update_status(self):
        """Обновление статуса рассылки"""
        now = timezone.now()

        if self.start_time > now:
            new_status = "Создана"
        elif self.start_time <= now <= self.end_time:
            new_status = "Запущена"
        else:
            new_status = "Завершена"

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=["status"])

        return new_status

    def can_send_now(self):
        """Проверка возможности отправки рассылки"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    def send_mailing(self):
        """Отправка рассылки"""
        if not self.can_send_now():
            return False, "Рассылка не может быть отправлена в текущее время"

        success_count = 0
        error_count = 0

        for recipient in self.recipients.all():
            try:
                send_mail(
                    subject=self.message.subject,
                    message=self.message.body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )
                status = "Успешно"
                server_response = "Письмо успешно отправлено"
                success_count += 1
            except Exception as e:
                status = "Не успешно"
                server_response = str(e)
                error_count += 1

            MailingAttempt.objects.create(
                mailing=self,
                attempt_time=timezone.now(),
                status=status,
                server_response=server_response,
            )

        return True, f"Отправлено успешно: {success_count}, с ошибкой: {error_count}"

    def save(self, *args, **kwargs):
        if not self.owner and hasattr(self, "_current_user"):
            self.owner = self._current_user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Рассылка #{self.id} - {self.message.subject}"


class MailingAttempt(models.Model):
    """Модель попытки отправки рассылки"""

    STATUS_CHOICES = [
        ("Успешно", "Успешно"),
        ("Не успешно", "Не успешно"),
    ]

    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Рассылка",
    )
    attempt_time = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата и время попытки"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, verbose_name="Статус"
    )
    server_response = models.TextField(verbose_name="Ответ почтового сервера")

    class Meta:
        verbose_name = "Попытка отправки"
        verbose_name_plural = "Попытки отправки"
        ordering = ["-attempt_time"]

    def __str__(self):
        return f"Попытка #{self.id} - {self.status}"
