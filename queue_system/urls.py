from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from queue_app import views as queue_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', queue_views.home, name='main_display'),

    # Patient-related pages
    path('patient/<int:patient_id>/dashboard/', queue_views.patient_dashboard, name='patient_dashboard'),
    path('patient/register/', queue_views.patient_register, name='patient_register'),
    path('patient/<int:patient_id>/virtual-card/', queue_views.patient_virtual_card, name='patient_virtual_card'),

    # Include any other app urls
    path('', include('queue_app.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
