from django.urls import path, re_path
from . import views
from .views import *
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
                  path('admin/registration/', views.admin_registration),
                  path('login', views.login),
                  path('user/registration/', views.user_registration),
                  path('org/registration/', views.org_registration),
                  path('list/own_org/', views.get_user_org),
                  path('database/list/', views.database_list)
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
