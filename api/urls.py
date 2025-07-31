from django.urls import path
from .views import EssayThemeListAPIView
from .views import EssaySubmissionCreateAPIView
from .views import HistoryListAPIView, HistoryDetailAPIView
from .views import N8nCorrectionWebhookAPIView
from .views import UserCreateAPIView
from .views import ChangePasswordView


urlpatterns = [
    path('themes/', EssayThemeListAPIView.as_view(), name='theme-list'),
    path('submissions/', EssaySubmissionCreateAPIView.as_view(), name='submission-create'),
    path('history/', HistoryListAPIView.as_view(), name='history-list'),
    path('history/<int:pk>/', HistoryDetailAPIView.as_view(), name='history-detail'),
    path('webhooks/n8n/correction-complete/', N8nCorrectionWebhookAPIView.as_view(), name='webhook-n8n-correction'),
    path('register/', UserCreateAPIView.as_view(), name='register'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]