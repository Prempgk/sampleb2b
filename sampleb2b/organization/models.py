from uuid import uuid4
from django.db import models


class Courses(models.Model):
    id = models.UUIDField(default=uuid4, editable=False, primary_key=True)
    organization = models.UUIDField(null=False, blank=False)
    course_details = models.JSONField(null=False, blank=False)
    is_purchased = models.BooleanField(null=False, blank=False)
    purchased_course_id = models.UUIDField(null=True, blank=True)


class Modules(models.Model):
    id = models.UUIDField(default=uuid4, editable=False, primary_key=True)
    module_details = models.JSONField(null=False, blank=False)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE, null=False, blank=False)


class SubModules(models.Model):
    id = models.UUIDField(default=uuid4, editable=False, primary_key=True)
    sub_module_details = models.JSONField(null=False, blank=False)
    module = models.ForeignKey(Modules, on_delete=models.CASCADE, null=False, blank=False)
