from copy import deepcopy
from unittest.mock import patch

from django.test import TestCase
from rest_framework import serializers

from quiz.models import Exam, Option, Question
from quiz.serializers import (
    ExamSerializer,
    OptionSerializer,
    QuestionSerializer,
)


class SerializerTests(TestCase):
    def setUp(self):
        self.exam = Exam.objects.create(title="Python basics")
        self.payload = {
            "exam": self.exam.pk,
            "text": "What is Python?",
            "options": [
                {"text": "A language", "is_correct": True},
                {"text": "A database", "is_correct": False},
            ],
        }

    def create_question(self):
        serializer = QuestionSerializer(data=deepcopy(self.payload))
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def test_exam_serialization_and_creation(self):
        self.assertEqual(
            ExamSerializer(self.exam).data,
            {"id": self.exam.pk, "title": "Python basics"},
        )
        serializer = ExamSerializer(data={"id": 999, "title": "Django"})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("id", serializer.validated_data)
        self.assertEqual(serializer.save().title, "Django")

    def test_nested_serialization_and_exam_identifier(self):
        question = self.create_question()
        data = QuestionSerializer(question).data
        self.assertEqual(data["exam"], self.exam.pk)
        self.assertEqual(data["text"], self.payload["text"])
        self.assertEqual(len(data["options"]), 2)
        self.assertEqual(data["options"][0]["text"], "A language")
        self.assertTrue(data["options"][0]["is_correct"])
        self.assertNotIn("question", data["options"][0])

    def test_create_question_with_one_correct_option(self):
        question = self.create_question()
        self.assertEqual(question.exam, self.exam)
        self.assertEqual(question.options.count(), 2)
        self.assertEqual(question.options.filter(is_correct=True).count(), 1)

    def test_reject_zero_or_multiple_correct_options(self):
        for flags in [(False, False), (True, True)]:
            with self.subTest(flags=flags):
                payload = deepcopy(self.payload)
                for option, flag in zip(payload["options"], flags):
                    option["is_correct"] = flag
                serializer = QuestionSerializer(data=payload)
                self.assertFalse(serializer.is_valid())
                self.assertIn("options", serializer.errors)
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Option.objects.count(), 0)

    def test_reject_missing_empty_or_null_options(self):
        for value in ["missing", [], None]:
            with self.subTest(value=value):
                payload = deepcopy(self.payload)
                if value == "missing":
                    payload.pop("options")
                else:
                    payload["options"] = value
                serializer = QuestionSerializer(data=payload)
                self.assertFalse(serializer.is_valid())
                self.assertIn("options", serializer.errors)

    def test_reject_incorrect_types_and_unknown_exam(self):
        cases = [
            ("exam", "not-an-id"), ("exam", 999999),
            ("text", {"invalid": "object"}), ("options", "not-a-list"),
            ("options", [{"text": [], "is_correct": "invalid"}]),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                payload = deepcopy(self.payload)
                payload[field] = value
                serializer = QuestionSerializer(data=payload)
                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)

    def test_patch_without_options_preserves_them(self):
        question = self.create_question()
        before = list(question.options.values())
        serializer = QuestionSerializer(
            question, data={"text": "Updated question"}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        self.assertEqual(question.text, "Updated question")
        self.assertEqual(list(question.options.values()), before)

    def test_patch_rejects_existing_invalid_state(self):
        question = self.create_question()
        question.options.update(is_correct=False)
        serializer = QuestionSerializer(
            question, data={"text": "New"}, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("options", serializer.errors)

    def test_update_replaces_options_and_switches_correct_answer(self):
        question = self.create_question()
        payload = deepcopy(self.payload)
        payload["options"][0]["is_correct"] = False
        payload["options"][1]["is_correct"] = True
        serializer = QuestionSerializer(question, data=payload)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        self.assertEqual(question.options.count(), 2)
        self.assertEqual(
            question.options.get(is_correct=True).text, "A database"
        )

    def test_patch_options_require_complete_replacement_items(self):
        question = self.create_question()
        serializer = QuestionSerializer(
            question, data={"options": [{"is_correct": True}]}, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("text", serializer.errors["options"][0])

    def test_patch_can_replace_options_with_defaults(self):
        question = self.create_question()
        serializer = QuestionSerializer(
            question,
            data={"options": [
                {"text": "Yes", "is_correct": True}, {"text": "No"},
            ]},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        self.assertFalse(question.options.get(text="No").is_correct)

    def test_create_rolls_back_when_nested_write_raises_validation_error(self):
        serializer = QuestionSerializer(data=deepcopy(self.payload))
        serializer.is_valid(raise_exception=True)
        with patch(
            "quiz.serializers.Option.objects.bulk_create",
            side_effect=serializers.ValidationError("Nested write failed."),
        ):
            with self.assertRaises(serializers.ValidationError):
                serializer.save()
        self.assertFalse(Question.objects.exists())
        self.assertFalse(Option.objects.exists())

    def test_update_rolls_back_parent_and_deleted_options_on_failure(self):
        question = self.create_question()
        before = list(question.options.values())
        payload = deepcopy(self.payload)
        payload["text"] = "Changed"
        serializer = QuestionSerializer(question, data=payload)
        serializer.is_valid(raise_exception=True)
        with patch(
            "quiz.serializers.Option.objects.bulk_create",
            side_effect=serializers.ValidationError("Nested write failed."),
        ):
            with self.assertRaises(serializers.ValidationError):
                serializer.save()
        question.refresh_from_db()
        self.assertEqual(question.text, self.payload["text"])
        self.assertEqual(list(question.options.values()), before)

    def test_save_revalidates_options_after_is_valid(self):
        question = self.create_question()
        serializer = QuestionSerializer(
            question, data={"text": "New"}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        question.options.update(is_correct=False)
        with self.assertRaises(serializers.ValidationError):
            serializer.save()
        question.refresh_from_db()
        self.assertEqual(question.text, self.payload["text"])

    def test_option_serialization_and_safe_direct_writes(self):
        question = self.create_question()
        option = question.options.get(is_correct=False)
        self.assertEqual(
            OptionSerializer(option).data["question"], question.pk
        )
        serializer = OptionSerializer(
            option, data={"text": "No"}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.save().text, "No")
        serializer = OptionSerializer(
            data={"question": question.pk, "text": "Other"}
        )
        serializer.is_valid(raise_exception=True)
        self.assertFalse(serializer.save().is_correct)

    def test_direct_option_updates_cannot_break_correct_count(self):
        question = self.create_question()
        for option in question.options.all():
            serializer = OptionSerializer(
                option,
                data={"is_correct": not option.is_correct},
                partial=True,
            )
            self.assertFalse(serializer.is_valid())
            self.assertIn("options", serializer.errors)
        serializer = OptionSerializer(data={
            "question": question.pk, "text": "Another", "is_correct": True,
        })
        self.assertFalse(serializer.is_valid())

    def test_direct_option_cannot_change_question(self):
        question = self.create_question()
        other = Question.objects.create(exam=self.exam, text="Other")
        serializer = OptionSerializer(
            question.options.first(), data={"question": other.pk}, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("question", serializer.errors)

    def test_direct_option_save_rechecks_current_state(self):
        question = self.create_question()
        serializer = OptionSerializer(
            data={"question": question.pk, "text": "Other"}
        )
        serializer.is_valid(raise_exception=True)
        question.options.update(is_correct=False)
        with self.assertRaises(serializers.ValidationError):
            serializer.save()
        self.assertEqual(question.options.count(), 2)

    def test_prefetched_questions_serialize_in_two_queries(self):
        self.create_question()
        self.create_question()
        with self.assertNumQueries(2):
            data = QuestionSerializer(
                Question.objects.prefetch_related("options"), many=True
            ).data
        self.assertEqual(len(data), 2)

    def test_identifiers_are_read_only(self):
        payload = deepcopy(self.payload)
        payload["id"] = 999
        payload["options"][0]["id"] = 998
        serializer = QuestionSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        self.assertNotIn("id", serializer.validated_data)
        self.assertNotIn("id", serializer.validated_data["options"][0])
