from django.urls import path

from tests import views

urlpatterns = [
    path("profiles/", views.ProfileList.as_view()),
    path("profiles/<uuid:id>/", views.ProfileDetail.as_view()),
    path("profiles/<uuid:id>/<str:action>/", views.ProfileDetail.as_view()),
    path("staff/<uuid:id>/", views.StaffDetail.as_view()),
    path("user/", views.UserSelf.as_view()),
    path("users/", views.UserList.as_view()),
    path("users/<int:id>/", views.UserDetail.as_view()),
    path("without-model-overriding-handler/", views.ViewWithoutModelListOverridingHandler.as_view()),
    path("without-model/<uuid:task_id>", views.ViewWithoutModelDetail.as_view()),
    path("without-model/", views.ViewWithoutModelList.as_view()),
    path("custom-tasks/", views.CustomTaskAPI.as_view()),
]
