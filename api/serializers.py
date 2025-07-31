from rest_framework import serializers
from .models import EssayTheme, EssaySubmission, Correction, CorrectionCriterion
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class CorrectionCriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorrectionCriterion
        fields = ['name', 'score', 'max_score', 'feedback_text', 'is_perfect']

class CorrectionSerializer(serializers.ModelSerializer):
    criteria = CorrectionCriterionSerializer(many=True, read_only=True)

    class Meta:
        model = Correction
        fields = ['overall_score', 'general_comment', 'positive_points', 'corrected_at', 'criteria']

class EssayThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EssayTheme
        fields = ['id', 'title', 'motivational_text', 'category', 'image_url', 'created_at']

class EssaySubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EssaySubmission
        fields = ['id', 'user', 'submitted_text', 'submitted_file', 'status', 'submission_date']
        read_only_fields = ['user', 'status', 'submission_date']

class SubmissionHistorySerializer(serializers.ModelSerializer):
    correction = CorrectionSerializer(read_only=True, required=False)

    class Meta:
        model = EssaySubmission
        fields = ['id', 'submission_date', 'status', 'correction']

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Sua senha antiga foi digitada incorretamente. Por favor, tente novamente.")
        return value