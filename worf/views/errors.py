from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from worf import exceptions
from worf.views.base import AbstractBaseAPI


@method_decorator(csrf_exempt, name="dispatch")
class NotFound(AbstractBaseAPI):
    def perform_dispatch(self, *args, **kwargs):
        raise exceptions.NotFound()
