import re

from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend


class ExamFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        exam = request.query_params.get("exam")
        if exam is None:
            return queryset
        if (
            re.fullmatch(r"[1-9][0-9]{0,18}", exam) is None
            or int(exam) > 9223372036854775807
        ):
            raise ValidationError(
                {"exam": "Use a positive integer exam ID (up to 2^63 - 1)."}
            )
        return queryset.filter(exam_id=int(exam))
