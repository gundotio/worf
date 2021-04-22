class Serializer:
    def __init__(self, model, *args, **kwargs):
        self.model = model
        super().__init__()

    # todo add validation that fields in these methods are actually on the model

    def read(self):
        return dict()

    def write(self):
        return []

    @classmethod
    def create(cls):
        return []
