from django.core.management.base import BaseCommand
from django.db import transaction

from quiz.models import Exam, Option, Question


class Command(BaseCommand):
    help = "Append two demo exams and 21 questions; preserve existing data."

    @transaction.atomic
    def handle(self, *args, **options):
        exams = [
            Exam.objects.create(title="Demo: Python basics"),
            Exam.objects.create(title="Demo: Web development"),
        ]
        for exam, count in zip(exams, [15, 6]):
            for index in range(1, count + 1):
                topic = (
                    "Python" if exam == exams[0] or index <= 3 else "Django"
                )
                question = Question.objects.create(
                    exam=exam, text=f"{topic} demo question {index}"
                )
                Option.objects.bulk_create([
                    Option(question=question, text="Correct", is_correct=True),
                    Option(question=question, text="Incorrect"),
                ])
        self.stdout.write(self.style.SUCCESS(
            f"Created exams {exams[0].pk} and {exams[1].pk}, "
            "21 questions and 42 options. Existing records were preserved."
        ))
