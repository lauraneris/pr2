from django.conf import settings
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
from .serializers import ChangePasswordSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser 
from django.contrib.auth.models import User
from .serializers import UserSerializer
from rest_framework.permissions import AllowAny
from .models import EssaySubmission, EssayTheme, Correction, CorrectionCriterion
from .serializers import (EssaySubmissionSerializer, EssayThemeSerializer,
                          SubmissionHistorySerializer)

# --- Views para Temas ---
class EssayThemeListAPIView(generics.ListAPIView):
    queryset = EssayTheme.objects.all().order_by('-created_at')
    serializer_class = EssayThemeSerializer

class EssaySubmissionCreateAPIView(generics.CreateAPIView):
    queryset = EssaySubmission.objects.all()
    serializer_class = EssaySubmissionSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    parser_classes = [MultiPartParser, FormParser, JSONParser] 

    def perform_create(self, serializer):
        submission = serializer.save(user=self.request.user)
        
        # URL do Webhook ATUALIZADA para a versão final
        n8n_webhook_url = "https://funpar.app.n8n.cloud/webhook/corrigir-redacao"

        payload = {
            "submission_id": submission.id,
            "submitted_text": submission.submitted_text,
            "file_url": self.request.build_absolute_uri(submission.submitted_file.url) if submission.submitted_file else None,
        }

        try:
            response = requests.post(n8n_webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            submission.status = 'processing'
            submission.save()
            print(f"Redação ID {submission.id} enviada e CONFIRMADA pelo n8n.")
        except requests.RequestException as e:
            submission.status = 'error'
            submission.save()
            print(f"ERRO DE REDE/CONEXÃO ao enviar para o n8n: {e}")

# --- Views para o Histórico do Usuário ---
class HistoryListAPIView(generics.ListAPIView):
    serializer_class = SubmissionHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EssaySubmission.objects.filter(user=self.request.user).order_by('-submission_date')

class HistoryDetailAPIView(generics.RetrieveAPIView):
    serializer_class = SubmissionHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EssaySubmission.objects.filter(user=self.request.user)

# --- View para o Webhook do n8n ---
class N8nCorrectionWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        # ... (código do webhook que finalizaremos depois) ...
        return Response(status=status.HTTP_200_OK)
    
class UserCreateAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = [IsAuthenticated]

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response({"message": "Senha alterada com sucesso!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

