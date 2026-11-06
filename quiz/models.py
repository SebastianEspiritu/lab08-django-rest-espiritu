from django.db import models

class Exam(models.Model):
    title = models.CharField(max_length=200)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.title


class Question(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    text = models.TextField()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.text


class Option(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options",
    )
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.text
