from rest_framework import serializers
from .models import (
    EssayTheme, EssaySubmission, Correction, CorrectionCriterion,
    UserProfile, StuartCoinTransaction
)
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.conf import settings
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['role', 'stuart_coins_balance']


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'profile']
        extra_kwargs = {'password': {'write_only': True}}

    def get_profile(self, obj):
        try:
            profile = obj.profile
            return UserProfileSerializer(profile).data
        except UserProfile.DoesNotExist:
            return None

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


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        self.reset_form = PasswordResetForm(data={'email': value})
        if not self.reset_form.is_valid():
            raise serializers.ValidationError('Nenhum utilizador encontrado com este e-mail.')
        return value

    def save(self):
        request = self.context.get('request')
        opts = {
            'use_https': request.is_secure(),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            'email_template_name': 'registration/password_reset_email.html',
            'request': request,
            'domain_override': settings.FRONTEND_URL.split('//')[-1]
        }
        self.reset_form.save(**opts)


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password1 = serializers.CharField(max_length=128, write_only=True)
    new_password2 = serializers.CharField(max_length=128, write_only=True)
    uidb64 = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        try:
            uid = urlsafe_base64_decode(attrs['uidb64']).decode()
            self.user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError('Link inválido.')

        if not default_token_generator.check_token(self.user, attrs['token']):
            raise serializers.ValidationError('Link inválido ou expirado.')

        self.set_password_form = SetPasswordForm(user=self.user, data=attrs)
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)

        return attrs

    def save(self):
        self.set_password_form.save()