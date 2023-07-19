from rest_framework import serializers
from .models import Courses, Modules, SubModules
from .firebase import fb_db
from users.models import OrganizationModel


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = '__all__'


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modules
        fields = '__all__'


class SubModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubModules
        fields = '__all__'


class PurchaseSerializer(serializers.Serializer):
    course_id = serializers.ListField(required=True)
    organization = serializers.UUIDField(required=True)

    def validate(self, attrs):
        course_id = attrs.get('course_id')
        courses = fb_db.child('course_details').get().val().values().mapping
        org_id = attrs.get('organization')
        for i in course_id:
            if i not in courses['course_id']:
                raise serializers.ValidationError(
                    {"course_id": "Course not found", "index": course_id.index(i)}
                )
            existing_course = Courses.objects.using('custom').filter(purchased_course_id=i, organization=org_id)
            if existing_course.exists():
                raise serializers.ValidationError(
                    {"course_id": "Already purchased", "index": course_id.index(i)}
                )
        return attrs


class CustomCourseSerializer(serializers.Serializer):
    organization = serializers.UUIDField(required=True)
    course_details = serializers.JSONField(required=True)
    is_purchased = serializers.BooleanField(required=True)
    purchased_course_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        org_id = attrs.get('organization')

        org_model = OrganizationModel.objects.filter(id=org_id)
        if not org_model.exists():
            raise serializers.ValidationError(
                {
                    "organization": "organization not found"
                }
            )
        return attrs


class CustomModuleSerializer(serializers.Serializer):
    module_details = serializers.JSONField(required=True)
    course = serializers.UUIDField(required=True)
    organization = serializers.UUIDField(required=True)

    def validate(self, attrs):
        course_id = attrs.get('course')
        org_id = attrs.get('organization')

        course_model = Courses.objects.using('custom').filter(organization=org_id, id=course_id)
        if not course_model.exists():
            raise serializers.ValidationError(
                {
                    "course": "Invalid course details"
                }
            )
        course_data = course_model.first()
        if course_data.is_purchased:
            raise serializers.ValidationError(
                {
                    "course": "You can't make any changes in purchased courses"
                }
            )
        attrs['course'] = course_data
        attrs.pop('organization')
        print(attrs)
        return attrs


class CustomSubModuleSerializer(serializers.Serializer):
    sub_module_details = serializers.JSONField(required=True)
    module = serializers.UUIDField(required=True)

    def validate(self, attrs):
        module_id = attrs.get('module')

        module_model = Modules.objects.using('custom').filter(id=module_id)

        if not module_model.exists():
            raise serializers.ValidationError(
                {
                    "module": "Invalid module details"
                }
            )
        module_data = module_model.first()
        attrs['module'] = module_data
        return attrs
