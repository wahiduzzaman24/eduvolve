from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('accounts/', include('accounts.urls')),
    path('courses/', include('courses.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


# print("EduVolve Project Setup Complete!")
# print("\nNext steps:")
# print("1. Install dependencies: pip install -r requirements.txt")
# print("2. Create migrations: python manage.py makemigrations")
# print("3. Run migrations: python manage.py migrate")
# print("4. Create superuser: python manage.py createsuperuser")
# print("5. Run server: python manage.py runserver")