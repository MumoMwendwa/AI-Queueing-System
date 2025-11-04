from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/queue/$', consumers.QueueConsumer.as_asgi()),
    re_path(r'ws/department/(?P<department_id>\w+)/$', consumers.DepartmentConsumer.as_asgi()),
]