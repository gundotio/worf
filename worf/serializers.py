class Serializer:
    def __init__(self, model, *args, **kwargs):
        self.model = model
        super().__init__()

    def read(self):
        return dict()

    def write(self):
        return []

    def create(self):
        return []
