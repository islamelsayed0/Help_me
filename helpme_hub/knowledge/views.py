"""
User-facing knowledge base views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension

from .models import Article
from .decorators import article_membership_required
from accounts.utils import get_user_school_group, has_accepted_membership


@login_required
@article_membership_required
def article_list_view(request):
    """List all published articles for the current user's organization."""
    user = request.user
    user_org = get_user_school_group(user)
    
    # Get published articles: group-specific + global (school_group=None)
    articles = Article.objects.filter(status='published')
    articles = articles.filter(
        Q(school_group=user_org) | Q(school_group__isnull=True)
    ).order_by('-published_at', '-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Category filter
    category_filter = request.GET.get('category')
    if category_filter and category_filter in [choice[0] for choice in Article.CATEGORY_CHOICES]:
        articles = articles.filter(category=category_filter)
    
    # Get categories for filter dropdown
    categories = Article.CATEGORY_CHOICES
    
    context = {
        'articles': articles,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': categories,
        'user_org': user_org,
    }
    
    return render(request, 'knowledge/article_list.html', context)


@login_required
@article_membership_required
def article_detail_view(request, article_id):
    """Display article details."""
    article = get_object_or_404(Article, id=article_id, status='published')
    user = request.user
    user_org = get_user_school_group(user)
    
    # Verify user has access (group-specific or global)
    if article.school_group and article.school_group != user_org:
        messages.error(request, 'You do not have permission to view this article.')
        return redirect('knowledge:article_list')
    
    # Increment view count
    article.increment_view_count()
    
    # Render markdown content
    md = markdown.Markdown(
        extensions=[
            'fenced_code',
            'codehilite',
            'tables',
            'nl2br',
        ],
        extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': True,
            }
        }
    )
    rendered_content = md.convert(article.content)
    
    # Get related articles (same category, same organization or global)
    related_articles = Article.objects.filter(
        status='published',
        category=article.category
    ).exclude(id=article.id)
    related_articles = related_articles.filter(
        Q(school_group=user_org) | Q(school_group__isnull=True)
    )[:5]
    
    context = {
        'article': article,
        'rendered_content': rendered_content,
        'related_articles': related_articles,
        'user_org': user_org,
    }
    
    return render(request, 'knowledge/article_detail.html', context)


@login_required
@article_membership_required
@require_http_methods(['POST'])
def mark_helpful_view(request, article_id):
    """Mark an article as helpful."""
    article = get_object_or_404(Article, id=article_id, status='published')
    user = request.user
    user_org = get_user_school_group(user)
    
    # Verify user has access
    if article.school_group and article.school_group != user_org:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    article.mark_helpful()
    
    return JsonResponse({
        'success': True,
        'helpful_votes': article.helpful_votes
    })
