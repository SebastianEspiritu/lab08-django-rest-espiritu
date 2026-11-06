from django.contrib import admin

from .models import Exam, Option, Question


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ["id", "title"]
    search_fields = ["title"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["id", "text", "exam"]
    list_filter = ["exam"]
    search_fields = ["text"]
    list_select_related = ["exam"]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ["id", "text", "question", "is_correct"]
    list_filter = ["is_correct", "question__exam"]
    search_fields = ["text", "question__text"]
    list_select_related = ["question"]
