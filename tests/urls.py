from tests import views
from worf.urls import api
from worf.views import errors

urlpatterns = [
    api("profiles/", views.ProfileList),
    api("profiles/<uuid:id>/", views.ProfileDetail),
    api("staff/<uuid:id>/", views.StaffDetail),
    api("user/", views.UserSelf),
    api("users/", views.UserList),
    api("users/<int:id>/", views.UserDetail),
    api("<path:any>/", errors.NotFound),
]
