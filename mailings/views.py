from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import Recipient, Message, Mailing
from .forms import RecipientForm, MessageForm, MailingForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


def home(request):
    """Главная страница со статистикой"""
    now = timezone.now()

    total_mailings = Mailing.objects.count()

    active_mailings = Mailing.objects.filter(
        start_time__lte=now, end_time__gte=now, status="Запущена"
    ).count()

    unique_recipients = Recipient.objects.count()

    context = {
        "total_mailings": total_mailings,
        "active_mailings": active_mailings,
        "unique_recipients": unique_recipients,
    }
    return render(request, "mailings/home.html", context)


@method_decorator(cache_page(60 * 15), name="dispatch")
class RecipientListView(LoginRequiredMixin, ListView):
    model = Recipient
    template_name = "mailings/recipient_list.html"
    context_object_name = "recipients"
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.is_manager:
            # Менеджеры видят всех получателей
            return Recipient.objects.all().order_by("-id")
        else:
            # Пользователи видят только своих получателей
            return Recipient.objects.filter(owner=self.request.user).order_by("-id")


class RecipientDetailView(LoginRequiredMixin, DetailView):
    model = Recipient
    template_name = "mailings/recipient_detail.html"


class RecipientCreateView(LoginRequiredMixin, CreateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailings/recipient_form.html"
    success_url = reverse_lazy("recipient_list")

    def form_valid(self, form):

        form.instance.owner = self.request.user
        messages.success(self.request, "Получатель успешно создан")
        return super().form_valid(form)


class RecipientUpdateView(LoginRequiredMixin, UpdateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailings/recipient_form.html"
    success_url = reverse_lazy("recipient_list")

    def form_valid(self, form):
        messages.success(self.request, "Получатель успешно обновлен")
        return super().form_valid(form)


class RecipientDeleteView(LoginRequiredMixin, DeleteView):
    model = Recipient
    template_name = "mailings/recipient_confirm_delete.html"
    success_url = reverse_lazy("recipient_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Получатель успешно удален")
        return super().delete(request, *args, **kwargs)


@method_decorator(cache_page(60 * 5), name="dispatch")
class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = "mailings/message_list.html"
    context_object_name = "messages"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:

            queryset = cache.get("messages_queryset_all")
            if not queryset:
                queryset = Message.objects.all().order_by("-id")
                cache.set("messages_queryset_all", queryset, 60 * 5)
            return queryset
        else:

            cache_key = f"messages_queryset_{user.id}"
            queryset = cache.get(cache_key)
            if not queryset:
                queryset = Message.objects.filter(owner=user).order_by("-id")
                cache.set(cache_key, queryset, 60 * 5)
            return queryset


class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = "mailings/message_detail.html"


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailings/message_form.html"
    success_url = reverse_lazy("message_list")

    def form_valid(self, form):

        form.instance.owner = self.request.user
        messages.success(self.request, "Сообщение успешно создано")
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailings/message_form.html"
    success_url = reverse_lazy("message_list")

    def form_valid(self, form):
        messages.success(self.request, "Сообщение успешно обновлено")
        return super().form_valid(form)


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = "mailings/message_confirm_delete.html"
    success_url = reverse_lazy("message_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Сообщение успешно удалено")
        return super().delete(request, *args, **kwargs)


@method_decorator(cache_page(60 * 5), name="dispatch")
class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "mailings/mailing_list.html"
    context_object_name = "mailings"
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.is_manager:
            queryset = cache.get("mailings_queryset")
            if not queryset:
                queryset = Mailing.objects.all().order_by("-start_time")
                cache.set("mailings_queryset", queryset, 60 * 5)
            return queryset
        else:
            return Mailing.objects.filter(owner=self.request.user).order_by(
                "-start_time"
            )


class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    template_name = "mailings/mailing_detail.html"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailing_list")

    def form_valid(self, form):

        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs["instance"] = self.model(owner=self.request.user)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["messages_list"] = Message.objects.filter(owner=self.request.user)
        context["recipients_list"] = Recipient.objects.filter(owner=self.request.user)
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if not form.instance.id:

            now = timezone.now()
            tomorrow = now + timezone.timedelta(days=1)
            form.initial["start_time"] = tomorrow.replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            form.initial["end_time"] = tomorrow.replace(
                hour=18, minute=0, second=0, microsecond=0
            )
        return form


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailing_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs["instance"] = self.object
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["messages_list"] = Message.objects.all()
        context["recipients_list"] = Recipient.objects.all()

        if self.object:
            context["selected_recipients"] = list(
                self.object.recipients.values_list("id", flat=True)
            )

        return context

    def get_initial(self):
        initial = super().get_initial()
        if self.object:

            initial["start_time"] = self.object.start_time.strftime("%Y-%m-%dT%H:%M")
            initial["end_time"] = self.object.end_time.strftime("%Y-%m-%dT%H:%M")
        return initial


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    model = Mailing
    template_name = "mailings/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailing_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Рассылка успешно удалена")
        return super().delete(request, *args, **kwargs)


def send_mailing_now(request, pk):
    """Ручной запуск рассылки"""
    mailing = get_object_or_404(Mailing, pk=pk)

    mailing.update_status()

    now = timezone.now()
    if mailing.start_time <= now <= mailing.end_time:
        mailing.status = "Запущена"
        mailing.save(update_fields=["status"])

    if mailing.can_send_now():
        success, result_message = mailing.send_mailing()
        if success:
            messages.success(request, f"Рассылка успешно отправлена. {result_message}")
        else:
            messages.error(request, f"Ошибка при отправке рассылки: {result_message}")
    else:
        messages.error(
            request,
            f"Рассылка не может быть отправлена сейчас. "
            f"Статус: {mailing.status}. "
            f"Текущее время должно быть между {mailing.start_time} и {mailing.end_time}",
        )

    return redirect("mailing_detail", pk=pk)
