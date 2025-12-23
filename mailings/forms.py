from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Recipient, Message, Mailing


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ["email", "full_name", "comment"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["subject", "body"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ["start_time", "end_time", "message", "recipients"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields["start_time"].widget = forms.DateTimeInput(
            attrs={
                "class": "form-control",
                "type": "datetime-local",
            }
        )
        self.fields["end_time"].widget = forms.DateTimeInput(
            attrs={
                "class": "form-control",
                "type": "datetime-local",
            }
        )
        self.fields["message"].widget = forms.Select(
            attrs={"class": "form-control", "placeholder": "Выберите сообщение..."}
        )
        self.fields["recipients"].widget = forms.SelectMultiple(
            attrs={"class": "form-control", "size": "8", "style": "height: 150px;"}
        )
        if user and user.is_manager:
            self.fields["message"].queryset = Message.objects.filter(owner=user)
            self.fields["recipients"].queryset = Recipient.objects.filter(owner=user)
        else:
            self.fields["message"].queryset = Message.objects.all()
            self.fields["recipients"].queryset = Recipient.objects.all()

        self.fields["message"].empty_label = "Выберите сообщение..."

        self.fields["start_time"].help_text = "Дата и время начала рассылки"
        self.fields["end_time"].help_text = "Дата и время окончания рассылки"
        self.fields["recipients"].help_text = (
            "Выберите получателей (для множественного выбора удерживайте Ctrl)"
        )

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time:
            if start_time < timezone.now():
                raise ValidationError(
                    {"start_time": "Дата начала не может быть в прошлом"}
                )
            if start_time >= end_time:
                raise ValidationError(
                    {"end_time": "Дата окончания должна быть позже даты начала"}
                )

        message = cleaned_data.get("message")
        if not message:
            raise ValidationError({"message": "Выберите сообщение для рассылки"})

        recipients = cleaned_data.get("recipients")
        if not recipients:
            raise ValidationError({"recipients": "Выберите хотя бы одного получателя"})

        return cleaned_data
