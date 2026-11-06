from django.db import transaction
from rest_framework.viewsets import ModelViewSet

from .models import Exam, Option, Question
from .serializers import (
    ExamSerializer,
    OptionSerializer,
    QuestionSerializer,
    validate_correct_option_count,
)


class ExamViewSet(ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer


class QuestionViewSet(ModelViewSet):
    queryset = Question.objects.select_related("exam").prefetch_related(
        "options"
    )
    serializer_class = QuestionSerializer


class OptionViewSet(ModelViewSet):
    queryset = Option.objects.select_related("question")
    serializer_class = OptionSerializer

    @transaction.atomic
    def perform_destroy(self, instance):
        question = Question.objects.select_for_update().get(
            pk=instance.question_id
        )
        validate_correct_option_count(
            question.options.exclude(pk=instance.pk)
            .filter(is_correct=True)
            .count()
        )
        instance.delete()
