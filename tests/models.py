from django.db import models


class DummyModel(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    email = models.CharField(max_length=64)
    phone = models.CharField(max_length=64)

    def api(self):
        return dict(id=self.id, email=self.email, phone=self.phone)

    def api_update_fields(self):
        return [
            "id",
            "email",
            "phone",
        ]
