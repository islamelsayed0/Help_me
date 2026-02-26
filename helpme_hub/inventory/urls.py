from django.urls import path
from . import views
from . import admin_views

app_name = 'inventory'

urlpatterns = [
    path('', views.item_list_view, name='item_list'),
    path('<int:item_id>/', views.item_detail_view, name='item_detail'),
    path('admin/', admin_views.admin_item_list_view, name='admin_item_list'),
    path('admin/create/', admin_views.admin_item_create_view, name='admin_item_create'),
    path('admin/<int:item_id>/edit/', admin_views.admin_item_edit_view, name='admin_item_edit'),
    path('admin/<int:item_id>/delete/', admin_views.admin_item_delete_view, name='admin_item_delete'),
]
