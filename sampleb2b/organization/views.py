from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from .serializers import *
from .firebase import fb_db
from .models import *
from users.serializers import OrgDbSerializer, OrganizationSerializer
from users.models import OrgDbModel, CustomUserModel, OrganizationModel
from users.views import org_db_connection, org_db_migration


# cms course get api
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_courses(request):
    if request.user.is_admin or request.user.is_common_user:
        # firebase database connection and retrieve common courses
        course_data = fb_db.child('course_details').get().val()
        return Response(course_data, status=status.HTTP_200_OK)


# api for course purchase
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase_course(request):
    if request.user.is_admin:
        if 'organization' not in request.data:
            return (
                {
                    "message": "error",
                    "error_message": {
                        "organization": "This field is required"
                    }
                }
            )
        # get organization's database details
        org_model = OrganizationModel.objects.filter(id=request.data['organization'])

        if not org_model.exists():
            return Response(
                {
                    "message": "error",
                    "error_message": {
                        "organization": {"Invalid organization details"}
                    }
                }
            )
        org_data = org_model.first()

        if org_data not in request.user.organizationmodel_set.all():
            return Response(
                {
                    "message": "error",
                    "error_message": {
                        "organization": {"Invalid organization details"}
                    }
                }
            )

        db_model = org_data.orgdbmodel_set.all()
        if db_model.exists():
            db_serializer = OrgDbSerializer(db_model[0])
            db_data = db_serializer.data
            org_db_connection(db_data)

            request.data['organization'] = org_data.id
        # serializer validation for purchased course was in cms & already purchased
        serializer = PurchaseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"message": "error",
                 "error_message": serializer.errors},
                status=status.HTTP_200_OK
            )

        # Get the course details from cms
        course_serializer_data = []
        for i in request.data['course_id']:
            course_sample_data = fb_db.child(i).get().val()
            course_data = {
                "organization": org_data.id,
                "course_details": course_sample_data,
                "is_purchased": True,
                "purchased_course_id": i
            }
            course_serializer_data.append(course_data)

        # serializer validation for course
        course_serializer = CustomCourseSerializer(data=course_serializer_data, many=True)
        if course_serializer.is_valid():
            validated_data = course_serializer.validated_data

            res_data = []

            # course model instance to save data to org's database
            for valid_data in validated_data:
                course_instance = Courses(**valid_data)
                course_instance.save(using='custom')
                created_data = CourseSerializer(course_instance)
                res_data.append(created_data.data)
            # serializer representation for model instance

            return Response(
                {
                    "message": "success",
                    "data": res_data
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": "error",
                 "error_message": course_serializer.errors},
                status=status.HTTP_200_OK)
    else:
        return Response(
            {
                "message": "error",
                "error_message": "un_authorized"
            },
            status=status.HTTP_200_OK
        )


# Api viewset to allow organization to create our own courses
class OwnCourseApiView(GenericViewSet):
    serializer_class = CourseSerializer
    queryset = Courses.objects.all()

    def create(self, request):

        if request.user.is_admin:
            # get organization's database details
            db_model = request.user.orgdbmodel_set.all()
            if db_model:
                db_serializer = OrgDbSerializer(db_model[0])
                db_data = db_serializer.data
                org_db_connection(db_data)

            org_model = request.user.organizationmodel_set.all().first()

            request.data['organization'] = org_model.id
            request.data['is_purchased'] = False
            course_serializer = CustomCourseSerializer(data=request.data)
            if not course_serializer.is_valid():
                return Response(
                    {
                        "message": "error",
                        "error_message": course_serializer.errors
                    },
                    status=status.HTTP_200_OK
                )
            validated_data = course_serializer.validated_data
            course_instance = Courses(**validated_data)
            course_instance.save(using='custom')
            res_data = CourseSerializer(course_instance).data
            return Response(
                {
                    "message": "success",
                    "data": res_data
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "message": "error",
                    "error_message": "un_authorized"
                },
                status=status.HTTP_200_OK
            )

    def get(self, request):
        if request.user.is_admin or request.user.is_org_user:
            if request.user.is_admin:
                org_model = request.user.organizationmodel_set.all().first()

                org_id = org_model.id
            else:
                org_id = request.user.organization
            admin = OrganizationModel.objects.get(id=org_id).admin
            db_model = admin.orgdbmodel_set.all()
            if db_model:
                db_serializer = OrgDbSerializer(db_model[0])
                db_data = db_serializer.data
                org_db_connection(db_data)
                courses = Courses.objects.using('custom').filter(organization=org_id)
                course_serializer = CourseSerializer(courses, many=True)
                return Response(
                    {
                        "message": "success",
                        "data": course_serializer.data
                    },
                    status=status.HTTP_200_OK
                )
        else:
            return Response(
                {
                    "message": "error",
                    "error_message": "un_authorized"
                },
                status=status.HTTP_200_OK
            )

    def put(self, request):
        if request.user.is_admin:
            org_model = request.user.organizationmodel_set.all().first()

            org_id = org_model.id
            request.data['is_purchased'] = False
            request.data['organization'] = org_id
            db_model = request.user.orgdbmodel_set.all()
            if db_model:
                db_serializer = OrgDbSerializer(db_model[0])
                db_data = db_serializer.data
                org_db_connection(db_data)
            try:
                course = Courses.objects.using('custom').get(id=request.data['id'])
            except:
                return Response(
                    {
                        "message": "error",
                        "error_message": "Invalid course details"
                    },
                    status=status.HTTP_200_OK
                )
            if course.is_purchased:
                return Response(
                    {
                        "message": "error",
                        "error_message": "can't edit the purchased course"
                    },
                    status=status.HTTP_200_OK
                )
            course_serializer = CustomCourseSerializer(data=request.data)
            if not course_serializer.is_valid():
                return Response(
                    {
                        "message": "error",
                        "error_message": course_serializer.errors
                    },
                    status=status.HTTP_200_OK
                )
            validated_data = course_serializer.validated_data
            course_instance = Courses.objects.using('custom').filter(id=request.data['id']).update(**validated_data)
            updated_course_data = Courses.objects.using('custom').get(id=request.data['id'])
            res_serializer = CourseSerializer(updated_course_data)
            return Response(
                {
                    "message": "success",
                    "data": res_serializer.data
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "message": "error",
                    "error_message": "un_authorized"
                },
                status=status.HTTP_200_OK
            )


# Api viewset for crud operation of modules
class CourseModulesApiView(GenericViewSet):
    serializer_class = ModuleSerializer
    queryset = Modules.objects.all()

    def create(self, request):

        if request.user.is_admin:
            # get organization's database details
            db_model = request.user.orgdbmodel_set.all()
            if db_model:
                db_serializer = OrgDbSerializer(db_model[0])
                db_data = db_serializer.data
                org_db_connection(db_data)

            org_model = request.user.organizationmodel_set.all().first()

            request.data['organization'] = org_model.id
            module_serializer = CustomModuleSerializer(data=request.data)
            if not module_serializer.is_valid():
                return Response(
                    {
                        "message": "error",
                        "error_message": module_serializer.errors
                    },
                    status=status.HTTP_200_OK
                )
            validated_data = module_serializer.validated_data
            module_instance = Modules(**validated_data)
            module_instance.save(using='custom')
            res_data = ModuleSerializer(module_instance).data
            return Response(
                {
                    "message": "success",
                    "data": res_data
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "message": "error",
                    "error_message": "un_authorized"
                },
                status=status.HTTP_200_OK
            )

    def get(self, request):
        if request.user.is_admin or request.user.is_org_user:
            if request.user.is_admin:
                org_model = request.user.organizationmodel_set.all().first()

                org_id = org_model.id
            else:
                org_id = request.user.organization
            admin = OrganizationModel.objects.get(id=org_id).admin
            db_model = admin.orgdbmodel_set.all()
            if db_model:
                db_serializer = OrgDbSerializer(db_model[0])
                db_data = db_serializer.data
                org_db_connection(db_data)

                course_id = self.request.query_params.get('course')
                modules = Modules.objects.using('custom').filter(course=course_id)
                module_serializer = ModuleSerializer(modules, many=True)
                return Response(
                    {
                        "message": "success",
                        "data": module_serializer.data
                    },
                    status=status.HTTP_200_OK
                )
        else:
            return Response(
                {
                    "message": "error",
                    "error_message": "un_authorized"
                },
                status=status.HTTP_200_OK
            )

    def put(self, request):
        if request.user.is_admin:
            # get organization's database details
            db_model = request.user.orgdbmodel_set.all()
            if db_model:
                db_serializer = OrgDbSerializer(db_model[0])
                db_data = db_serializer.data
                org_db_connection(db_data)

            org_model = request.user.organizationmodel_set.all().first()

            request.data['organization'] = org_model.id
            try:
                module = Modules.objects.using('custom').get(id=request.data['id'])
            except:
                return Response(
                    {
                        "message": "error",
                        "error_message": "Invalid module details"
                    },
                    status=status.HTTP_200_OK
                )
            module_serializer = CustomModuleSerializer(data=request.data)
            if not module_serializer.is_valid():
                return Response(
                    {
                        "message": "error",
                        "error_message": module_serializer.errors
                    },
                    status=status.HTTP_200_OK
                )
            validated_data = module_serializer.validated_data
            module_instance = Modules.objects.using('custom').filter(id=request.data['id']).update(**validated_data)
            updated_module_data = Modules.objects.using('custom').get(id=request.data['id'])
            res_serializer = ModuleSerializer(updated_module_data)
            return Response(
                {
                    "message": "success",
                    "data": res_serializer.data
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "message": "error",
                    "error_message": "un_authorized"
                },
                status=status.HTTP_200_OK
            )


# Api viewset for crud operation of  submodules
class SubModuleApiView(GenericViewSet):
    serializer_class = SubModuleSerializer
    queryset = SubModules.objects.all()

    def create(self, request):

        if request.user.is_admin:
            # get organization's database details
            db_model = request.user.orgdbmodel_set.all()
            if db_model:
                db_serializer = OrgDbSerializer(db_model[0])
                db_data = db_serializer.data
                org_db_connection(db_data)

            sub_module_serializer = CustomSubModuleSerializer(data=request.data)
            if not sub_module_serializer.is_valid():
                return Response(
                    {
                        "message": "error",
                        "error_message": sub_module_serializer.errors
                    },
                    status=status.HTTP_200_OK
                )
            validated_data = sub_module_serializer.validated_data
            sub_module_instance = SubModules(**validated_data)
            sub_module_instance.save(using='custom')
            res_data = SubModuleSerializer(sub_module_instance).data
            return Response(
                {
                    "message": "success",
                    "data": res_data
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "message": "error",
                    "error_message": "un_authorized"
                },
                status=status.HTTP_200_OK
            )

    def get(self, request):
        if request.user.is_admin or request.user.is_org_user:
            if request.user.is_admin:
                org_model = request.user.organizationmodel_set.all().first()

                org_id = org_model.id
            else:
                org_id = request.user.organization
            admin = OrganizationModel.objects.get(id=org_id).admin
            db_model = admin.orgdbmodel_set.all()
            if db_model:
                db_serializer = OrgDbSerializer(db_model[0])
                db_data = db_serializer.data
                org_db_connection(db_data)

                module_id = self.request.query_params.get('module')
                sub_modules = SubModules.objects.using('custom').filter(module=module_id)
                sub_module_serializer = SubModuleSerializer(sub_modules, many=True)
                return Response(
                    {
                        "message": "success",
                        "data": sub_module_serializer.data
                    },
                    status=status.HTTP_200_OK
                )
        else:
            return Response(
                {
                    "message": "error",
                    "error_message": "un_authorized"
                },
                status=status.HTTP_200_OK
            )

    def put(self, request):
        if request.user.is_admin:
            # get organization's database details
            db_model = request.user.orgdbmodel_set.all()
            if db_model:
                db_serializer = OrgDbSerializer(db_model[0])
                db_data = db_serializer.data
                org_db_connection(db_data)

            try:
                sub_module = SubModules.objects.using('custom').get(id=request.data['id'])
            except:
                return Response(
                    {
                        "message": "error",
                        "error_message": "Invalid sub module details"
                    },
                    status=status.HTTP_200_OK
                )
            sub_module_serializer = CustomSubModuleSerializer(data=request.data)
            if not sub_module_serializer.is_valid():
                return Response(
                    {
                        "message": "error",
                        "error_message": sub_module_serializer.errors
                    },
                    status=status.HTTP_200_OK
                )
            validated_data = sub_module_serializer.validated_data
            sub_module_instance = SubModules.objects.using('custom').filter(
                id=request.data['id']).update(**validated_data)
            updated_module_data = SubModules.objects.using('custom').get(id=request.data['id'])
            res_serializer = SubModuleSerializer(updated_module_data)
            return Response(
                {
                    "message": "success",
                    "data": res_serializer.data
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "message": "error",
                    "error_message": "un_authorized"
                },
                status=status.HTTP_200_OK
            )


@api_view(['POST'])
@permission_classes([AllowAny])
def get_organization(request):
    organization_data = OrganizationModel.objects.all()
    org_serializer = OrganizationSerializer(organization_data, many=True)
    return Response(
        {
            "message": "success",
            "data": org_serializer.data
        },
        status=status.HTTP_200_OK
    )
