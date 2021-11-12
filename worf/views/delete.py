from worf.views.base import AbstractBaseAPI


class DeleteAPI(AbstractBaseAPI):
    def delete(self, request, *args, **kwargs):
        self.destroy()
        return self.render_to_response("", 204)

    def destroy(self):
        self.get_instance().delete()
