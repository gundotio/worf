class FindInstance:
    lookup_field = "id"
    lookup_url_kwarg = "id"
    queryset = None

    def get_instance(self):
        if not hasattr(self, "instance"):
            self.lookup_kwargs = {self.lookup_field: self.kwargs[self.lookup_url_kwarg]}
            self.instance = self.get_queryset().get(**self.lookup_kwargs)

        return self.instance

    def get_queryset(self):
        if self.queryset is None:
            return self.model.objects.all()
        return self.queryset.all()
