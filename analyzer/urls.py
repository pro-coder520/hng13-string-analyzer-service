from django.urls import path
from . import views

urlpatterns = [
    # Maps to /strings/
    path('', views.strings_view, name='strings'),
    
    # Maps to /strings/filter-by-natural-language?query=...
    path('filter-by-natural-language', views.filter_by_natural_language, name='filter_by_natural_language'),

    # Maps to /strings/{string_value}
    path('<str:string_value>', views.string_detail_view, name='string_detail'),
]
