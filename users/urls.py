from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    # Регистрация и аутентификация
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    # Профиль и статистика
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),
    path("statistics/", views.UserStatisticsView.as_view(), name="user_statistics"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    # Для менеджеров
    path("users/", views.UserListView.as_view(), name="user_list"),
    path(
        "users/<int:pk>/toggle-block/",
        views.ToggleUserBlockView.as_view(),
        name="toggle_user_block",
    ),
    path(
        "mailings/<int:pk>/disable/",
        views.DisableMailingView.as_view(),
        name="disable_mailing",
    ),
    # Сброс пароля
    path(
        "password-reset/",
        views.CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        views.CustomPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        views.CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
