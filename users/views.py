from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    UpdateView,
    TemplateView,
    CreateView,
    FormView,
    View,
)
from django.utils import timezone

from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from .models import User
from mailings.models import Mailing, MailingAttempt


class ManagerRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки, что пользователь - менеджер"""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_manager

    def handle_no_permission(self):
        messages.error(self.request, "Доступ только для менеджеров")
        return redirect("home")


class UserRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки, что пользователь - обычный пользователь"""

    def test_func(self):
        return self.request.user.is_authenticated and not self.request.user.is_manager

    def handle_no_permission(self):
        messages.error(self.request, "Доступ только для пользователей")
        return redirect("home")


class RegisterView(CreateView):
    template_name = "users/register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Регистрация успешна! Добро пожаловать!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Регистрация"
        return context


class LoginView(FormView):
    template_name = "users/login.html"
    form_class = CustomAuthenticationForm
    success_url = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()

        if user.is_blocked:
            messages.error(self.request, "Ваш аккаунт заблокирован")
            return redirect("users:login")

        login(self.request, user)
        messages.success(self.request, f"Добро пожаловать, {user.username}!")

        next_url = self.request.GET.get("next", self.success_url)
        return redirect(next_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Вход в систему"
        return context


class LogoutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "Вы вышли из системы")
        return redirect("home")


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "users/profile_edit.html"
    form_class = UserProfileForm
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Профиль обновлен")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Редактирование профиля"
        return context


class UserStatisticsView(LoginRequiredMixin, UserRequiredMixin, TemplateView):
    template_name = "users/statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        user_mailings = Mailing.objects.filter(owner=user)
        total_mailings = user_mailings.count()
        mailing_ids = user_mailings.values_list("id", flat=True)

        if mailing_ids:

            total_attempts = MailingAttempt.objects.filter(
                mailing_id__in=mailing_ids
            ).count()

            successful_attempts = MailingAttempt.objects.filter(
                mailing_id__in=mailing_ids, status="Успешно"
            ).count()
        else:
            total_attempts = 0
            successful_attempts = 0

        failed_attempts = total_attempts - successful_attempts

        active_mailings = user_mailings.filter(
            status="Запущена",
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now(),
        ).count()

        if total_attempts > 0:
            success_rate = (successful_attempts / total_attempts) * 100
        else:
            success_rate = 0

        context["stats"] = {
            "total_mailings": total_mailings,
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "failed_attempts": failed_attempts,
            "active_mailings": active_mailings,
            "success_rate": round(success_rate, 2),
        }

        return context


class UserListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    paginate_by = 20
    ordering = ["-date_joined"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Список пользователей"
        return context


class ToggleUserBlockView(LoginRequiredMixin, ManagerRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        if user == request.user:
            messages.error(request, "Нельзя заблокировать себя")
        else:
            user.is_blocked = not user.is_blocked
            user.save()

            action = "заблокирован" if user.is_blocked else "разблокирован"
            messages.success(request, f"Пользователь {user.username} {action}")

        return redirect("users:user_list")


class DisableMailingView(LoginRequiredMixin, ManagerRequiredMixin, View):
    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)

        if mailing.status != "Завершена":
            mailing.status = "Завершена"
            mailing.save(update_fields=["status"])
            messages.success(request, f"Рассылка #{mailing.id} отключена")
        else:
            messages.info(request, "Рассылка уже завершена")

        return redirect("mailing_list")


class CustomPasswordResetView(PasswordResetView):
    template_name = "users/password_reset.html"
    email_template_name = "users/password_reset_email.html"
    success_url = reverse_lazy("users:password_reset_done")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Восстановление пароля"
        return context


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "users/password_reset_done.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Письмо отправлено"
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("users:password_reset_complete")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Новый пароль"
        return context


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "users/password_reset_complete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Пароль изменен"
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    """Дашборд пользователя/менеджера"""

    template_name = "users/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_manager:

            context["total_users"] = User.objects.count()
            context["active_users"] = User.objects.filter(is_blocked=False).count()
            context["blocked_users"] = User.objects.filter(is_blocked=True).count()

            context["total_mailings"] = Mailing.objects.count()
            context["active_mailings"] = Mailing.objects.filter(
                status="Запущена",
                start_time__lte=timezone.now(),
                end_time__gte=timezone.now(),
            ).count()

            context["total_attempts"] = MailingAttempt.objects.count()
            context["successful_attempts"] = MailingAttempt.objects.filter(
                status="Успешно"
            ).count()

        else:

            user_mailings = Mailing.objects.filter(owner=user)

            context["user_mailings_count"] = user_mailings.count()
            context["active_user_mailings"] = user_mailings.filter(
                status="Запущена",
                start_time__lte=timezone.now(),
                end_time__gte=timezone.now(),
            ).count()

            mailing_ids = user_mailings.values_list("id", flat=True)

            if mailing_ids:
                context["user_total_attempts"] = MailingAttempt.objects.filter(
                    mailing_id__in=mailing_ids
                ).count()

                context["user_successful_attempts"] = MailingAttempt.objects.filter(
                    mailing_id__in=mailing_ids, status="Успешно"
                ).count()
            else:
                context["user_total_attempts"] = 0
                context["user_successful_attempts"] = 0

        return context


class HomeView(TemplateView):
    template_name = "mailings/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        context["total_mailings"] = Mailing.objects.count()
        context["unique_recipients"] = User.objects.count()

        if self.request.user.is_authenticated:
            if self.request.user.is_manager:

                context["active_mailings"] = Mailing.objects.filter(
                    start_time__lte=now, end_time__gte=now, status="Запущена"
                ).count()
            else:

                context["active_mailings"] = Mailing.objects.filter(
                    owner=self.request.user,
                    start_time__lte=now,
                    end_time__gte=now,
                    status="Запущена",
                ).count()
        else:

            context["active_mailings"] = 0

        return context
