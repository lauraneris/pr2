from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    class Role(models.TextChoices):
        STUDENT = 'student', 'Aluno'
        TEACHER = 'teacher', 'Professor'
        ADMIN = 'admin', 'Admin'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    stuart_coins_balance = models.PositiveIntegerField(default=10)

    def __str__(self):
        return f"Perfil de {self.user.username} - Saldo: {self.stuart_coins_balance} SC"

# Sinal para criar um UserProfile automaticamente quando um User é criado
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# 2. DEFINIÇÃO DO STUARTCOINTRANSACTION (ESTAVA EM FALTA)
class StuartCoinTransaction(models.Model):
    class TransactionType(models.TextChoices):
        CREDIT = 'credit', 'Crédito'
        DEBIT = 'debit', 'Débito'

    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=6, choices=TransactionType.choices)
    amount = models.PositiveIntegerField()
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} de {self.amount} SC para {self.user_profile.user.username} - {self.description}"


class EssayTheme(models.Model):
    title = models.CharField(max_length=255)
    motivational_text = models.TextField()
    category = models.CharField(max_length=100)
    image_url = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class EssaySubmission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('error', 'Erro'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    submitted_text = models.TextField(blank=True, null=True)
    submitted_file = models.FileField(upload_to='uploads/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    submission_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Redação de {self.user.username} em {self.submission_date.strftime('%d/%m/%Y')}"

class Correction(models.Model):
    submission = models.OneToOneField(EssaySubmission, on_delete=models.CASCADE, related_name='correction')
    overall_score = models.IntegerField()
    general_comment = models.TextField()
    positive_points = models.JSONField(default=list)
    corrected_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Correção para a redação ID {self.submission.id}"

class CorrectionCriterion(models.Model):
    correction = models.ForeignKey(Correction, on_delete=models.CASCADE, related_name='criteria')
    name = models.CharField(max_length=100)
    score = models.IntegerField()
    max_score = models.IntegerField()
    feedback_text = models.TextField()
    is_perfect = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.score}/{self.max_score}"
    
class SubmissionLog(models.Model):
   
    submission = models.ForeignKey(EssaySubmission, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    step = models.CharField(max_length=100) # Ex: 'N8N_WORKFLOW_STARTED', 'CALLING_GEMINI'
    details = models.JSONField(default=dict) # Para guardar metadados, como IDs ou mensagens de erro

    def __str__(self):
        return f"Log para Submissão {self.submission.id} em {self.timestamp}: {self.step}"

    class Meta:
        ordering = ['timestamp']