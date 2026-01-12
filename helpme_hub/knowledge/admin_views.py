"""
Admin-facing knowledge base views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import Article
from .forms import ArticleForm
from .decorators import admin_article_access_required
from accounts.decorators import role_required
from accounts.utils import get_user_school_group


@login_required
@role_required(['admin', 'superadmin'])
@admin_article_access_required
def admin_article_list_view(request):
    """Admin article list showing all articles for their organization."""
    user = request.user
    user_org = get_user_school_group(user)
    
    # Get articles for admin's organization
    if user.is_superadmin():
        # Superadmins can see all articles
        articles = Article.objects.all()
    else:
        articles = Article.objects.filter(school_group=user_org)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['draft', 'published']:
        articles = articles.filter(status=status_filter)
    
    # Filter by category
    category_filter = request.GET.get('category')
    if category_filter and category_filter in [choice[0] for choice in Article.CATEGORY_CHOICES]:
        articles = articles.filter(category=category_filter)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    articles = articles.order_by('-updated_at', '-created_at')
    
    # Get counts
    total_count = articles.count()
    draft_count = articles.filter(status='draft').count()
    published_count = articles.filter(status='published').count()
    
    context = {
        'articles': articles,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'search_query': search_query,
        'total_count': total_count,
        'draft_count': draft_count,
        'published_count': published_count,
        'categories': Article.CATEGORY_CHOICES,
        'user_org': user_org,
    }
    
    return render(request, 'knowledge/admin/article_list.html', context)


@login_required
@role_required(['admin', 'superadmin'])
@admin_article_access_required
@require_http_methods(['GET', 'POST'])
def admin_article_create_view(request):
    """Create a new article."""
    user = request.user
    user_org = get_user_school_group(user)
    
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = user
            article.school_group = user_org
            article.save()
            
            # If status is published, publish it
            if article.status == 'published':
                article.publish()
                # Log audit action
                from audit.utils import log_article_published
                log_article_published(user, article)
            
            messages.success(request, f'Article "{article.title}" created successfully.')
            return redirect('knowledge:admin_article_list')
    else:
        form = ArticleForm()
    
    context = {
        'form': form,
        'user_org': user_org,
    }
    
    return render(request, 'knowledge/admin/article_form.html', context)


@login_required
@role_required(['admin', 'superadmin'])
@admin_article_access_required
@require_http_methods(['GET', 'POST'])
def admin_article_edit_view(request, article_id):
    """Edit an existing article."""
    article = get_object_or_404(Article, id=article_id)
    user = request.user
    user_org = get_user_school_group(user)
    
    # Verify access (superadmins can edit all, regular admins can only edit their org's)
    if not user.is_superadmin() and article.school_group != user_org:
        messages.error(request, 'You do not have permission to edit this article.')
        return redirect('knowledge:admin_article_list')
    
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            article = form.save()
            
            # Handle publish/unpublish
            if article.status == 'published' and not article.published_at:
                article.publish()
                # Log audit action
                from audit.utils import log_article_published
                log_article_published(user, article)
            elif article.status == 'draft' and article.published_at:
                article.unpublish()
                # Log audit action
                from audit.utils import log_article_unpublished
                log_article_unpublished(user, article)
            
            messages.success(request, f'Article "{article.title}" updated successfully.')
            return redirect('knowledge:admin_article_list')
    else:
        form = ArticleForm(instance=article)
    
    context = {
        'form': form,
        'article': article,
        'user_org': user_org,
    }
    
    return render(request, 'knowledge/admin/article_form.html', context)


@login_required
@role_required(['admin', 'superadmin'])
@admin_article_access_required
@require_http_methods(['POST'])
def admin_article_delete_view(request, article_id):
    """Delete an article."""
    article = get_object_or_404(Article, id=article_id)
    user = request.user
    user_org = get_user_school_group(user)
    
    # Verify access
    if not user.is_superadmin() and article.school_group != user_org:
        messages.error(request, 'You do not have permission to delete this article.')
        return redirect('knowledge:admin_article_list')
    
    title = article.title
    article.delete()
    
    messages.success(request, f'Article "{title}" deleted successfully.')
    return redirect('knowledge:admin_article_list')


@login_required
@role_required(['admin', 'superadmin'])
@admin_article_access_required
@require_http_methods(['POST'])
def admin_article_publish_view(request, article_id):
    """Publish/unpublish an article."""
    article = get_object_or_404(Article, id=article_id)
    user = request.user
    user_org = get_user_school_group(user)
    
    # Verify access
    if not user.is_superadmin() and article.school_group != user_org:
        messages.error(request, 'You do not have permission to modify this article.')
        return redirect('knowledge:admin_article_list')
    
    action = request.POST.get('action', 'publish')
    
    if action == 'publish':
        article.publish()
        # Log audit action
        from audit.utils import log_article_published
        log_article_published(user, article)
        messages.success(request, f'Article "{article.title}" published successfully.')
    elif action == 'unpublish':
        article.unpublish()
        # Log audit action
        from audit.utils import log_article_unpublished
        log_article_unpublished(user, article)
        messages.success(request, f'Article "{article.title}" unpublished successfully.')
    
    return redirect('knowledge:admin_article_list')
