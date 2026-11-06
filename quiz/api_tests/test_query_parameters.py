from io import StringIO
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.core.management import call_command
from rest_framework.test import APITestCase

from quiz.models import Exam, Option, Question


class QuestionQueryTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.exam = Exam.objects.create(title="Python")
        cls.other = Exam.objects.create(title="Django")
        for exam, count in [(cls.exam, 15), (cls.other, 6)]:
            for index in range(count):
                question = Question.objects.create(
                    exam=exam, text=f"Python question {index}"
                )
                Option.objects.bulk_create([
                    Option(question=question, text="Yes", is_correct=True),
                    Option(question=question, text="No"),
                ])
        cls.url = "/api/questions/"

    def test_filter_by_exam_keeps_nested_options(self):
        response = self.client.get(self.url, {"exam": self.exam.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 15)
        for question in response.data["results"]:
            self.assertEqual(question["exam"], self.exam.pk)
            self.assertEqual(len(question["options"]), 2)
            self.assertEqual(
                sum(option["is_correct"] for option in question["options"]), 1
            )

    def test_unknown_exam_returns_empty_paginated_list(self):
        response = self.client.get(self.url, {"exam": 999999})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            "count": 0, "next": None, "previous": None, "results": [],
        })

    def test_invalid_exam_identifiers_return_400(self):
        for value in ["", "abc", "-1", "0", "1.5", "1.0", "01",
                      "9223372036854775808", "9" * 100, "1 OR 1=1"]:
            with self.subTest(value=value):
                response = self.client.get(self.url, {"exam": value})
                self.assertEqual(response.status_code, 400)
                self.assertIn("exam", response.data)

    def test_partial_search_is_case_insensitive(self):
        for term in ["python", "PYTHON", "PyTh", "ython"]:
            with self.subTest(term=term):
                response = self.client.get(self.url, {"search": term})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["count"], 21)

    def test_search_without_matches_returns_empty_list(self):
        response = self.client.get(self.url, {"search": "unmatched"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])
        self.assertEqual(response.data["count"], 0)

    def test_combined_filter_search_and_pagination(self):
        params = {"exam": self.exam.pk, "search": "PYTHON"}
        response = self.client.get(self.url, params)
        self.assertEqual(response.data["count"], 15)
        self.assertEqual(len(response.data["results"]), 10)
        query = parse_qs(urlparse(response.data["next"]).query)
        self.assertEqual(query, {
            "exam": [str(self.exam.pk)], "search": ["PYTHON"], "page": ["2"],
        })
        second = self.client.get(response.data["next"])
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["count"], 15)
        self.assertEqual(len(second.data["results"]), 5)
        self.assertIsNone(second.data["next"])
        self.assertIsNotNone(second.data["previous"])
        for question in second.data["results"]:
            self.assertEqual(question["exam"], self.exam.pk)
            self.assertIn("python", question["text"].lower())
            self.assertEqual(
                sum(option["is_correct"] for option in question["options"]), 1
            )

    def test_combined_parameters_can_have_no_matches(self):
        response = self.client.get(self.url, {
            "exam": self.exam.pk, "search": "Django",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_first_second_and_last_pages_and_links(self):
        first = self.client.get(self.url)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["count"], 21)
        self.assertEqual(len(first.data["results"]), 10)
        self.assertIsNone(first.data["previous"])
        second = self.client.get(first.data["next"])
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(second.data["results"]), 10)
        self.assertIsNotNone(second.data["previous"])
        self.assertIsNotNone(second.data["next"])
        last = self.client.get(second.data["next"])
        self.assertEqual(len(last.data["results"]), 1)
        self.assertIsNone(last.data["next"])
        back = self.client.get(second.data["previous"])
        self.assertEqual(back.data["results"], first.data["results"])
        ids = [q["id"] for page in [first, second, last]
               for q in page.data["results"]]
        self.assertEqual(len(set(ids)), 21)
        self.assertEqual(ids, sorted(ids))

    def test_invalid_or_nonexistent_pages_return_404(self):
        for page in [0, -1, 4, "invalid"]:
            with self.subTest(page=page):
                response = self.client.get(self.url, {"page": page})
                self.assertEqual(response.status_code, 404)

    def test_filtered_nonexistent_page_returns_404(self):
        response = self.client.get(self.url, {
            "exam": self.exam.pk, "search": "python", "page": 3,
        })
        self.assertEqual(response.status_code, 404)

    def test_filtered_search_retains_constant_query_count(self):
        with self.assertNumQueries(3):
            response = self.client.get(self.url, {
                "exam": self.exam.pk, "search": "python",
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 10)


class DemoCommandTests(APITestCase):
    def test_command_is_additive_and_preserves_existing_records(self):
        exam = Exam.objects.create(title="Existing")
        question = Question.objects.create(exam=exam, text="Existing")
        option = Option.objects.create(
            question=question, text="Existing", is_correct=True
        )
        for iteration in range(1, 3):
            call_command("seed_quiz_demo", stdout=StringIO())
            self.assertEqual(Exam.objects.count(), 1 + 2 * iteration)
            self.assertEqual(Question.objects.count(), 1 + 21 * iteration)
            self.assertEqual(Option.objects.count(), 1 + 42 * iteration)
        exam.refresh_from_db()
        question.refresh_from_db()
        option.refresh_from_db()
        self.assertEqual(exam.title, "Existing")
        self.assertEqual(question.text, "Existing")
        self.assertEqual(option.text, "Existing")
        self.assertTrue(option.is_correct)
        for question in Question.objects.exclude(pk=question.pk):
            self.assertEqual(question.options.count(), 2)
            self.assertEqual(
                question.options.filter(is_correct=True).count(), 1
            )

    def test_command_rolls_back_on_write_failure(self):
        with patch(
            "quiz.management.commands.seed_quiz_demo."
            "Option.objects.bulk_create",
            side_effect=RuntimeError("Simulated failure"),
        ):
            with self.assertRaises(RuntimeError):
                call_command("seed_quiz_demo", stdout=StringIO())
        self.assertFalse(Exam.objects.exists())
        self.assertFalse(Question.objects.exists())
        self.assertFalse(Option.objects.exists())
