from django.urls import path
from .views import *

urlpatterns = [
    path('login/',login),
    path('signup/',signup),
    path('chat/',chat_llm),
    path('get/user/files/',get_filenames),
    path('upload/document/',document_add),
]
