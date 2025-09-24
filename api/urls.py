from django.urls import path
from .views import (
    EssayThemeListAPIView,
    EssaySubmissionCreateAPIView,
    HistoryListAPIView, 
    HistoryDetailAPIView,
    N8nCorrectionWebhookAPIView,
    UserCreateAPIView,
    ChangePasswordView,
    PasswordResetRequestView, 
    PasswordResetConfirmView,
    UserProfileDetailView 
)

urlpatterns = [
    path('profile/me/', UserProfileDetailView.as_view(), name='user-profile-detail'),
    path('themes/', EssayThemeListAPIView.as_view(), name='theme-list'),
    path('submissions/', EssaySubmissionCreateAPIView.as_view(), name='submission-create'),
    path('history/', HistoryListAPIView.as_view(), name='history-list'),
    path('history/<int:pk>/', HistoryDetailAPIView.as_view(), name='history-detail'),
    path('webhooks/n8n/correction-complete/', N8nCorrectionWebhookAPIView.as_view(), name='webhook-n8n-correction'),
    path('register/', UserCreateAPIView.as_view(), name='register'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]