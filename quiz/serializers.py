from django.db import transaction
from rest_framework import serializers

from .models import Exam, Option, Question


def validate_correct_option_count(count):
    if count != 1:
        raise serializers.ValidationError(
            {"options": "A question must have exactly one correct option."}
        )


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ["id", "title"]
        read_only_fields = ["id"]


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "question", "text", "is_correct"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        question = attrs.get("question")
        if self.instance is not None:
            if (
                question is not None
                and question.pk != self.instance.question_id
            ):
                raise serializers.ValidationError(
                    {"question": "An option cannot move to another question."}
                )
            question = self.instance.question
        self._validate_result(question, attrs)
        return attrs

    def _validate_result(self, question, attrs):
        options = question.options.filter(is_correct=True)
        if self.instance is not None:
            options = options.exclude(pk=self.instance.pk)
        is_correct = attrs.get(
            "is_correct",
            self.instance.is_correct if self.instance is not None else False,
        )
        validate_correct_option_count(options.count() + int(is_correct))

    @transaction.atomic
    def create(self, validated_data):
        question = Question.objects.select_for_update().get(
            pk=validated_data["question"].pk
        )
        self._validate_result(question, validated_data)
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        question = Question.objects.select_for_update().get(
            pk=instance.question_id
        )
        instance = Option.objects.get(pk=instance.pk)
        self.instance = instance
        target = validated_data.get("question", question)
        if target.pk != question.pk:
            raise serializers.ValidationError(
                {"question": "An option cannot move to another question."}
            )
        self._validate_result(question, validated_data)
        return super().update(instance, validated_data)


class NestedOptionSerializer(serializers.ModelSerializer):
    text = serializers.CharField(max_length=500)
    is_correct = serializers.BooleanField(default=False)

    class Meta:
        model = Option
        fields = ["id", "text", "is_correct"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        # A supplied list replaces all options, including during PATCH.
        if "text" not in attrs:
            raise serializers.ValidationError(
                {"text": "This field is required."}
            )
        return attrs


class QuestionSerializer(serializers.ModelSerializer):
    options = NestedOptionSerializer(many=True, allow_empty=False)

    class Meta:
        model = Question
        fields = ["id", "exam", "text", "options"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if "options" in attrs:
            validate_correct_option_count(
                sum(
                    option.get("is_correct", False)
                    for option in attrs["options"]
                )
            )
        elif self.instance is not None:
            validate_correct_option_count(
                self.instance.options.filter(is_correct=True).count()
            )
        else:
            raise serializers.ValidationError(
                {"options": "This field is required."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        self.validate(validated_data)
        options = validated_data.pop("options")
        question = Question.objects.create(**validated_data)
        Option.objects.bulk_create(
            [Option(question=question, **option) for option in options]
        )
        return question

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = Question.objects.select_for_update().get(pk=instance.pk)
        self.instance = instance
        self.validate(validated_data)
        options = validated_data.pop("options", None)
        instance = super().update(instance, validated_data)
        if options is not None:
            instance.options.all().delete()
            Option.objects.bulk_create(
                [Option(question=instance, **option) for option in options]
            )
        return instance
