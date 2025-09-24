import requests
import threading  
from django.conf import settings
from django.db import transaction
from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from .models import EssaySubmission, EssayTheme, Correction, CorrectionCriterion
from .serializers import (
    EssaySubmissionSerializer, 
    EssayThemeSerializer,
    SubmissionHistorySerializer,
    UserSerializer,
    ChangePasswordSerializer
)


def send_submission_to_webhook(submission, request):
    n8n_webhook_url = "https://n8n-n8n-start.eswufe.easypanel.host/webhook-test/d3aadfb9-3482-428e-9b2f-6bab1d85c088"

    file_url = None
    if submission.submitted_file:
        file_url = request.build_absolute_uri(submission.submitted_file.url)

    payload = {
        "submission_id": submission.id,
        "submitted_text": submission.submitted_text,
        "file_url": file_url,
    }

    try:
        requests.post(n8n_webhook_url, json=payload, timeout=20)
        print(f"THREAD: Redação ID {submission.id} enviada com sucesso para o n8n.")
    except requests.RequestException as e:
        print(f"THREAD ERRO: Falha ao enviar Redação ID {submission.id} para o n8n: {e}")
        submission.status = 'error'
        submission.save()


# views para os temas de redação e subimissão de redações 
class EssayThemeListAPIView(generics.ListAPIView):
    queryset = EssayTheme.objects.all().order_by('-created_at')
    serializer_class = EssayThemeSerializer


class EssaySubmissionCreateAPIView(generics.CreateAPIView):
    queryset = EssaySubmission.objects.all()
    serializer_class = EssaySubmissionSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        # salvando redação
        submission = serializer.save(user=self.request.user, status='processing')

        # thread
        thread = threading.Thread(
            target=send_submission_to_webhook, 
            args=(submission, self.request)
        )
        thread.start() # executada em segundo plano

        print(f"Resposta imediata para a Redação ID {submission.id}. Webhook a executar em background.")


# histórico do usuário
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


# view para o n8n versão webhook
class N8nCorrectionWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # 1. Verificação de Segurança
        secret_token = request.headers.get('X-N8N-Api-Key')
        if secret_token != settings.N8N_WEBHOOK_SECRET:
            return Response({"error": "Acesso não autorizado."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        submission_id = data.get('submission_id')
        
        if not submission_id:
            return Response({"error": "submission_id é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 2. Encontrar a Submissão e garantir que está a ser processada
            submission = EssaySubmission.objects.get(id=submission_id, status='processing')
        except EssaySubmission.DoesNotExist:
            return Response({"error": "Submissão não encontrada ou já processada."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # 3. Usar uma transação para garantir a integridade dos dados
            with transaction.atomic():
                # Criar o objeto principal da Correção
                correction = Correction.objects.create(
                    submission=submission,
                    overall_score=data.get('overall_score', 0),
                    general_comment=data.get('general_comment', ''),
                    positive_points=data.get('positive_points', [])
                )

                # Criar os objetos de Critérios de Correção
                criteria_data = data.get('criteria', [])
                for criterion in criteria_data:
                    CorrectionCriterion.objects.create(
                        correction=correction,
                        name=criterion.get('name', 'Critério'),
                        score=criterion.get('score', 0),
                        max_score=criterion.get('max_score', 200),
                        feedback_text=criterion.get('feedback_text', ''),
                        is_perfect=criterion.get('is_perfect', False)
                    )

                # 4. Atualizar o status da submissão para concluído
                submission.status = 'completed'
                submission.save()

        except Exception as e:
            # Em caso de erro, marcar a submissão com erro para revisão manual
            submission.status = 'error'
            submission.save()
            return Response({"error": f"Erro ao processar a correção: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Correção processada com sucesso."}, status=status.HTTP_200_OK)


# utilizador e oAuth
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
    

class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Se existir uma conta com o e-mail fornecido, enviaremos um link para redefinir a senha."},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Senha redefinida com sucesso."},
            status=status.HTTP_200_OK
        )


class UserProfileDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user