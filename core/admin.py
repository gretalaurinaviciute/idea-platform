from django.contrib import admin
from .models import Category, User, Idea


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "suggested_by")
    list_filter = ("status",)
    actions = ["approve_category"]

    def approve_category(self, request, queryset):
        queryset.update(status="APPROVED")
    approve_category.short_description = "Approve selected categories"


class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "type", "skills", "category", "experience", "last_login")
    list_filter = ("type", "category", "experience")
    search_fields = ("username",)


class IdeaAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "user", "category", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("title", )


admin.site.register(Category, CategoryAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Idea, IdeaAdmin)

