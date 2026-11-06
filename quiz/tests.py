from django.test import TestCase

from .models import Exam, Option, Question


class QuizRelationshipTests(TestCase):
    def test_relationships_keep_questions_and_options_in_their_parent(self):
        exam = Exam.objects.create(title="Python basics")
        other_exam = Exam.objects.create(title="Django basics")
        question = Question.objects.create(exam=exam, text="What is Python?")
        other_question = Question.objects.create(
            exam=other_exam, text="What is Django?"
        )
        correct = Option.objects.create(
            question=question, text="A programming language", is_correct=True
        )
        incorrect = Option.objects.create(question=question, text="A database")
        other_option = Option.objects.create(
            question=other_question, text="A web framework", is_correct=True
        )

        self.assertEqual(question.exam, exam)
        self.assertEqual(correct.question, question)
        self.assertQuerySetEqual(exam.questions.all(), [question])
        self.assertQuerySetEqual(question.options.all(), [correct, incorrect])
        self.assertQuerySetEqual(other_exam.questions.all(), [other_question])
        self.assertQuerySetEqual(other_question.options.all(), [other_option])
        self.assertFalse(incorrect.is_correct)

    def test_deleting_question_cascades_only_to_its_options(self):
        exam = Exam.objects.create(title="Python basics")
        question = Question.objects.create(exam=exam, text="First question")
        sibling = Question.objects.create(exam=exam, text="Second question")
        option = Option.objects.create(question=question, text="First option")
        sibling_option = Option.objects.create(question=sibling, text="Other")

        question.delete()

        self.assertFalse(Option.objects.filter(pk=option.pk).exists())
        self.assertTrue(Exam.objects.filter(pk=exam.pk).exists())
        self.assertTrue(Question.objects.filter(pk=sibling.pk).exists())
        self.assertTrue(Option.objects.filter(pk=sibling_option.pk).exists())

    def test_deleting_exam_cascades_without_affecting_other_exams(self):
        exam = Exam.objects.create(title="Python basics")
        question = Question.objects.create(exam=exam, text="What is Python?")
        option = Option.objects.create(question=question, text="A language")
        other_exam = Exam.objects.create(title="Django basics")
        other_question = Question.objects.create(exam=other_exam, text="Django?")
        other_option = Option.objects.create(question=other_question, text="Web")

        exam.delete()

        self.assertFalse(Question.objects.filter(pk=question.pk).exists())
        self.assertFalse(Option.objects.filter(pk=option.pk).exists())
        self.assertTrue(Exam.objects.filter(pk=other_exam.pk).exists())
        self.assertTrue(Question.objects.filter(pk=other_question.pk).exists())
        self.assertTrue(Option.objects.filter(pk=other_option.pk).exists())
