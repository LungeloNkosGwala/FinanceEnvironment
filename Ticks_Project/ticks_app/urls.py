
from django.urls import path, include
from ticks_app import views

# Create your views here.
urlpatterns = [
    path("index",views.index,name="index"),
    path("createAccount",views.createAccount, name="createAccount"),
    path("user_login/",views.user_login, name='user_login'),
    path("register/",views.register, name="register"),
    path("transactions/",views.transactions, name="transactions"),
    path("balance/",views.balance, name="balance"),
    path("settings/", views.settings, name="settings"),
    path("settings/setup/", views.setup, name="setup"),
    path("behaviour/",views.financialBehaviour,name="behaviour"),
    path("register/",views.register, name="register"),
    path("settings/notes", views.notes,name='notes'),
]