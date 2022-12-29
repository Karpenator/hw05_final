from django.db import models


class CreatedModel(models.Model):
    """Добавляет дату создания."""
    pub_date = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        abstract = True
