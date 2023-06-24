from django.contrib import admin
from .models import Account, UserProfile
# Register your models here.
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['id','user']
admin.site.register(UserProfile, UserProfileAdmin)  
admin.site.register(Account)