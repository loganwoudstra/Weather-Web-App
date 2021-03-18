from django.urls import path


from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name="search"),
    path('<int:id>', views.weather, name='weather'),
    path('<int:id>/alerts/', views.alerts, name="alerts"),
    path('favourites/', views.favourites, name='favourites'),
]
