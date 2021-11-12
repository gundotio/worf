class FindInstance:
    lookup_field = "id"
    lookup_url_kwarg = "id"
    queryset = None

    def get_instance(self):
        self.lookup_kwargs = {self.lookup_field: self.kwargs[self.lookup_url_kwarg]}

        self.validate_lookup_field_values()

        if not hasattr(self, "instance"):
            self.instance = self.get_queryset().get(**self.lookup_kwargs)

        return self.instance

    def get_queryset(self):
        if self.queryset is None:
            return self.model.objects.all()
        return self.queryset.all()
