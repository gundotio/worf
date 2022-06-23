from worf.views.base import AbstractBaseAPI


class DeleteAPI(AbstractBaseAPI):
    def delete(self, *args, **kwargs):
        self.destroy(*args, **kwargs)
        return self.render_to_response("", 204)

    def destroy(self, *args, **kwargs):
        self.get_instance().delete()
