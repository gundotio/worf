from worf.lookups import FindInstance
from worf.views.base import AbstractBaseAPI
from worf.views.update import UpdateAPI


class DetailAPI(FindInstance, AbstractBaseAPI):
    def get(self, *args, **kwargs):
        return self.render_to_response()


class DetailUpdateAPI(UpdateAPI, DetailAPI):
    pass
