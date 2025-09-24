# api/admin.py

from django.contrib import admin
from .models import (
    UserProfile, 
    StuartCoinTransaction, 
    EssayTheme, 
    EssaySubmission, 
    Correction, 
    CorrectionCriterion
)

class EssaySubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'submission_date')
    list_filter = ('status', 'submission_date')
    search_fields = ('user__username', 'id')

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'stuart_coins_balance')
    search_fields = ('user__username',)


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(StuartCoinTransaction)
admin.site.register(EssayTheme)
admin.site.register(EssaySubmission, EssaySubmissionAdmin)
admin.site.register(Correction)
admin.site.register(CorrectionCriterion)
