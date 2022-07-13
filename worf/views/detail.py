from worf.lookups import FindInstance
from worf.views.base import AbstractBaseAPI
from worf.views.update import UpdateAPI


class DetailAPI(FindInstance, AbstractBaseAPI):
    detail_serializer = None

    def get(self, *args, **kwargs):
        return self.render_to_response()

    def get_serializer(self):
        if self.detail_serializer and self.request.method == "GET":
            return self.detail_serializer(**self.get_serializer_kwargs())
        return super().get_serializer()


class DetailUpdateAPI(UpdateAPI, DetailAPI):
    pass
