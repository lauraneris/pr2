from django.db import models
from django.contrib.auth.models import User

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