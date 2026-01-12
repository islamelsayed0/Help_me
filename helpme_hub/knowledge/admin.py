from django.contrib import admin
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin interface for Article model."""
    list_display = ('title', 'author', 'category', 'status', 'school_group', 'view_count', 'helpful_votes', 'published_at', 'created_at')
    list_filter = ('status', 'category', 'school_group', 'published_at', 'created_at')
    search_fields = ('title', 'content', 'tags')
    readonly_fields = ('view_count', 'helpful_votes', 'created_at', 'updated_at', 'published_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'content', 'author', 'school_group')
        }),
        ('Organization', {
            'fields': ('category', 'tags', 'status')
        }),
        ('Statistics', {
            'fields': ('view_count', 'helpful_votes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('published_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Filter articles based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Regular admins can only see articles from their organization
        if hasattr(request.user, 'current_organization') and request.user.current_organization:
            return qs.filter(school_group=request.user.current_organization)
        return qs.none()
