from django.urls import path, re_path, include
from . import views
from .views import *
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register('own/courses', OwnCourseApiView)
router.register('course/modules', CourseModulesApiView)
router.register('course/modules/(?P<course>)', CourseModulesApiView)
router.register('course/submodules', SubModuleApiView)
router.register('course/submodules/(?P<module>)', SubModuleApiView)
urlpatterns = [
                  path('cms/courses/', views.get_courses),
                  path('cms/purchase/courses/', views.purchase_course),
                  path('list/organizations/', views.get_organization),
                  path('', include(router.urls))
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
