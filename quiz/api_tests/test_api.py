from copy import deepcopy

from django.urls import resolve, reverse
from rest_framework.test import APITestCase

from quiz.models import Exam, Option, Question
from quiz.urls import router
from quiz.views import ExamViewSet, OptionViewSet, QuestionViewSet


class QuizAPITests(APITestCase):
    def setUp(self):
        self.exam = Exam.objects.create(title="Python")
        self.question = Question.objects.create(
            exam=self.exam, text="What is Python?"
        )
        self.correct = Option.objects.create(
            question=self.question, text="A language", is_correct=True
        )
        self.incorrect = Option.objects.create(
            question=self.question, text="A database"
        )
        self.payload = {
            "exam": self.exam.pk,
            "text": "New question",
            "options": [
                {"text": "Yes", "is_correct": True},
                {"text": "No", "is_correct": False},
            ],
        }

    def snapshot(self):
        return (
            list(Exam.objects.values()),
            list(Question.objects.values()),
            list(Option.objects.values()),
        )

    def assert_rejected_without_changes(self, method, url, data=None):
        before = self.snapshot()
        response = getattr(self.client, method)(url, data, format="json")
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(self.snapshot(), before)
        return response

    def test_router_registers_three_viewsets_and_root_links(self):
        self.assertEqual(
            [(prefix, view) for prefix, view, _ in router.registry],
            [("exams", ExamViewSet), ("questions", QuestionViewSet),
             ("options", OptionViewSet)],
        )
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {"exams", "questions", "options"})
        for name in ["exam", "question", "option"]:
            self.assertEqual(
                resolve(reverse(f"{name}-list")).url_name, f"{name}-list"
            )

    def test_all_lists_and_details_return_200(self):
        for name, instance in [
            ("exam", self.exam), ("question", self.question),
            ("option", self.correct),
        ]:
            with self.subTest(name=name):
                response = self.client.get(reverse(f"{name}-list"))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.data["count"], 1 if name != "option" else 2
                )
                response = self.client.get(
                    reverse(f"{name}-detail", args=[instance.pk])
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["id"], instance.pk)

    def test_question_response_has_nested_options_and_exam_id(self):
        response = self.client.get(
            reverse("question-detail", args=[self.question.pk])
        )
        self.assertEqual(response.data["exam"], self.exam.pk)
        self.assertEqual(len(response.data["options"]), 2)
        self.assertEqual(response.data["options"][0]["id"], self.correct.pk)
        self.assertTrue(response.data["options"][0]["is_correct"])

    def test_browsable_api_renders_root_lists_and_details(self):
        urls = ["/api/"]
        for name, instance in [
            ("exam", self.exam), ("question", self.question),
            ("option", self.correct),
        ]:
            urls.extend([
                reverse(f"{name}-list"),
                reverse(f"{name}-detail", args=[instance.pk]),
            ])
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url, HTTP_ACCEPT="text/html")
                self.assertEqual(response.status_code, 200)
                self.assertIn("text/html", response["Content-Type"])
                self.assertContains(response, "Django REST framework")
        response = self.client.get("/api/", HTTP_ACCEPT="text/html")
        for resource in ["exams", "questions", "options"]:
            self.assertContains(response, f"/api/{resource}/")

    def test_create_exam_returns_201(self):
        response = self.client.post(
            reverse("exam-list"), {"title": "Django"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Exam.objects.filter(pk=response.data["id"]).exists())

    def test_create_question_returns_201_with_nested_options(self):
        response = self.client.post(
            reverse("question-list"), self.payload, format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        question = Question.objects.get(pk=response.data["id"])
        self.assertEqual(question.options.count(), 2)
        self.assertEqual(question.options.filter(is_correct=True).count(), 1)

    def test_create_incorrect_option_returns_201(self):
        response = self.client.post(reverse("option-list"), {
            "question": self.question.pk, "text": "Other",
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertFalse(response.data["is_correct"])
        self.assertEqual(self.question.options.count(), 3)

    def test_patch_each_resource_returns_200(self):
        cases = [
            ("exam", self.exam, {"title": "Updated"}),
            ("question", self.question, {"text": "Updated"}),
            ("option", self.correct, {"text": "Updated"}),
        ]
        option_ids = list(self.question.options.values_list("pk", flat=True))
        for name, instance, data in cases:
            with self.subTest(name=name):
                response = self.client.patch(
                    reverse(f"{name}-detail", args=[instance.pk]),
                    data, format="json",
                )
                self.assertEqual(response.status_code, 200, response.data)
                instance.refresh_from_db()
                for field, value in data.items():
                    self.assertEqual(getattr(instance, field), value)
        self.assertEqual(
            list(self.question.options.values_list("pk", flat=True)),
            option_ids,
        )

    def test_patch_question_replaces_options_and_switches_answer(self):
        response = self.client.patch(
            reverse("question-detail", args=[self.question.pk]),
            {"options": [
                {"text": "First", "is_correct": False},
                {"text": "Second", "is_correct": True},
            ]}, format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data["options"]), 2)
        self.assertEqual(
            self.question.options.get(is_correct=True).text, "Second"
        )

    def test_put_updates_all_three_resources(self):
        cases = [
            ("exam", self.exam, {"title": "Complete update"}),
            ("question", self.question, self.payload),
        ]
        for name, instance, data in cases:
            response = self.client.put(
                reverse(f"{name}-detail", args=[instance.pk]),
                data, format="json",
            )
            self.assertEqual(response.status_code, 200, response.data)
        option = self.question.options.get(is_correct=True)
        response = self.client.put(
            reverse("option-detail", args=[option.pk]),
            {"question": self.question.pk, "text": "Correct",
             "is_correct": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)

    def test_delete_incorrect_option_returns_204(self):
        response = self.client.delete(
            reverse("option-detail", args=[self.incorrect.pk])
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Option.objects.filter(pk=self.incorrect.pk).exists())
        self.assertEqual(
            self.question.options.filter(is_correct=True).count(), 1
        )

    def test_delete_correct_option_returns_400_without_changes(self):
        self.assert_rejected_without_changes(
            "delete", reverse("option-detail", args=[self.correct.pk])
        )

    def test_second_correct_option_returns_400_without_changes(self):
        self.assert_rejected_without_changes("post", reverse("option-list"), {
            "question": self.question.pk, "text": "Another",
            "is_correct": True,
        })

    def test_unmarking_correct_option_returns_400_without_changes(self):
        self.assert_rejected_without_changes(
            "patch", reverse("option-detail", args=[self.correct.pk]),
            {"is_correct": False},
        )

    def test_marking_second_correct_option_returns_400_without_changes(self):
        self.assert_rejected_without_changes(
            "patch", reverse("option-detail", args=[self.incorrect.pk]),
            {"is_correct": True},
        )

    def test_moving_either_option_is_rejected_without_changes(self):
        other = Question.objects.create(exam=self.exam, text="Other")
        Option.objects.create(question=other, text="Correct", is_correct=True)
        for option in [self.correct, self.incorrect]:
            for method in ["patch", "put"]:
                with self.subTest(option=option.pk, method=method):
                    response = self.assert_rejected_without_changes(
                        method, reverse("option-detail", args=[option.pk]),
                        {"question": other.pk, "text": option.text,
                         "is_correct": option.is_correct},
                    )
                    self.assertIn("question", response.data)

    def test_same_question_relation_is_allowed(self):
        response = self.client.patch(
            reverse("option-detail", args=[self.incorrect.pk]),
            {"question": self.question.pk, "text": "Edited"}, format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)

    def test_delete_question_cascades_options_with_204(self):
        response = self.client.delete(
            reverse("question-detail", args=[self.question.pk])
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Question.objects.exists())
        self.assertFalse(Option.objects.exists())
        self.assertTrue(Exam.objects.filter(pk=self.exam.pk).exists())

    def test_delete_exam_cascades_with_204(self):
        response = self.client.delete(
            reverse("exam-detail", args=[self.exam.pk])
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Exam.objects.exists())
        self.assertFalse(Question.objects.exists())
        self.assertFalse(Option.objects.exists())

    def test_missing_resources_return_404_for_get_patch_and_delete(self):
        for name in ["exam", "question", "option"]:
            for method in ["get", "patch", "delete"]:
                with self.subTest(name=name, method=method):
                    response = getattr(self.client, method)(
                        reverse(f"{name}-detail", args=[999999])
                    )
                    self.assertEqual(response.status_code, 404)

    def test_invalid_question_posts_return_400_without_changes(self):
        payloads = []
        for flags in [(False, False), (True, True)]:
            data = deepcopy(self.payload)
            for option, flag in zip(data["options"], flags):
                option["is_correct"] = flag
            payloads.append(data)
        for field, value in [("options", []), ("exam", "invalid")]:
            data = deepcopy(self.payload)
            data[field] = value
            payloads.append(data)
        data = deepcopy(self.payload)
        data.pop("text")
        payloads.append(data)
        for data in payloads:
            with self.subTest(data=data):
                self.assert_rejected_without_changes(
                    "post", reverse("question-list"), data
                )

    def test_invalid_patch_keeps_question_and_options_unchanged(self):
        for options in [[], [{"text": "Wrong", "is_correct": False}],
                        [{"is_correct": True}]]:
            self.assert_rejected_without_changes(
                "patch", reverse("question-detail", args=[self.question.pk]),
                {"text": "Should not persist", "options": options},
            )

    def test_question_list_query_count_does_not_grow_with_questions(self):
        url = reverse("question-list")
        with self.assertNumQueries(3):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        for index in range(4):
            question = Question.objects.create(exam=self.exam, text=str(index))
            Option.objects.create(
                question=question, text="Yes", is_correct=True
            )
        with self.assertNumQueries(3):
            response = self.client.get(url)
        self.assertEqual(len(response.data["results"]), 5)

    def test_browsable_renderer_supports_post_patch_and_delete(self):
        headers = {"HTTP_ACCEPT": "text/html"}
        exam = self.client.post(
            reverse("exam-list"), {"title": "HTML workflow"},
            format="json", **headers,
        )
        self.assertEqual(exam.status_code, 201)
        payload = deepcopy(self.payload)
        payload["exam"] = exam.data["id"]
        question = self.client.post(
            reverse("question-list"), payload, format="json", **headers
        )
        self.assertEqual(question.status_code, 201)
        option = self.client.post(
            reverse("option-list"),
            {"question": question.data["id"], "text": "Extra"},
            format="json", **headers,
        )
        self.assertEqual(option.status_code, 201)
        resources = [
            ("exam", exam, {"title": "Edited"}),
            ("question", question, {"text": "Edited"}),
            ("option", option, {"text": "Edited"}),
        ]
        for name, created, data in resources:
            self.assertIn("text/html", created["Content-Type"])
            response = self.client.patch(
                reverse(f"{name}-detail", args=[created.data["id"]]),
                data, format="json", **headers,
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("text/html", response["Content-Type"])
        for name, created, _ in reversed(resources):
            response = self.client.delete(
                reverse(f"{name}-detail", args=[created.data["id"]]),
                **headers,
            )
            # BrowsableAPIRenderer converts 204 to 200 to display HTML.
            self.assertEqual(response.status_code, 200)
            model = {"exam": Exam, "question": Question, "option": Option}[name]
            self.assertFalse(
                model.objects.filter(pk=created.data["id"]).exists()
            )
