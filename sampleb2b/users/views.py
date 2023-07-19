import requests
from django.core.management import call_command
from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .serializers import *
from .models import *
from django.conf import settings
from sampleb2b.settings import env
from django.db import connections


# Create your views here.
# mysql configuration settings
def database_creation(db_name, username, password, admin_id, org_id):
    # own_db = sql_connector.connect(
    #     host=env('DB_HOST'),
    #     port=env('DB_PORT'),
    #     user=env('DB_USER'),
    #     password=env('DB_PASSWORD'),
    #     auth_plugin='mysql_native_password'
    # )

    # connection for own server need to change server we can use above commented execution
    own_db = connections['default']
    own_cursor = own_db.cursor()

    # sql statements for database, user creation & permission grants
    own_cursor.execute('CREATE DATABASE {};'.format(db_name))
    user_sql = "CREATE USER '{}'@'localhost' IDENTIFIED BY '{}';".format(username, password)
    own_cursor.execute(user_sql)
    grant_sql = "GRANT ALL ON {}.* TO '{}'@localhost;".format(db_name, username)
    own_cursor.execute(grant_sql)

    # save db configurations
    db_data = {
        "db_name": db_name,
        "db_host": env('DB_HOST'),
        "db_user": username,
        "db_password": password,
        "db_port": int(env('DB_PORT')),
        "admin_data": admin_id,
        "organization":  [org_id]
    }
    db_serializer = OrgDbSerializer(data=db_data)
    if db_serializer.is_valid():
        db_serializer.save()
    return db_serializer.data


# table migrations
def org_db_migration(db_data):
    settings.DATABASES['custom']['HOST'] = db_data['db_host']
    settings.DATABASES['custom']['PORT'] = db_data['db_port']
    settings.DATABASES['custom']['NAME'] = db_data['db_name']
    settings.DATABASES['custom']['USER'] = db_data['db_user']
    settings.DATABASES['custom']['PASSWORD'] = db_data['db_password']

    call_command('migrate', 'organization', database='custom')
    return True


# database connection
def org_db_connection(db_data):
    settings.DATABASES['custom']['HOST'] = db_data['db_host']
    settings.DATABASES['custom']['PORT'] = db_data['db_port']
    settings.DATABASES['custom']['NAME'] = db_data['db_name']
    settings.DATABASES['custom']['USER'] = db_data['db_user']
    settings.DATABASES['custom']['PASSWORD'] = db_data['db_password']


# custom validation
# def org_data_custom_validation(org_data, db_connection):
#     existing_db_model = OrganizationModel.objects.using(db_connection).all()
#     org_name = []
#     org_mail = []
#     for i in existing_db_model:
#         org_name.append(i.name)
#         org_mail.append(i.mail)
#
#     error = []
#
#     if org_data['name'] in org_name:
#         error.append({"name": 'Organization name already exists'})
#     if org_data['email'] in org_mail:
#         error.append({"email": 'Organization mail already exists'})
#
#     return error


# admin registration process
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_registration(request):
    data = request.data
    data['is_admin'] = True
    data['is_user'] = False

    # get the organization's data from request
    org_data = data['organization_data']

    # Admin serializer  & validation
    admin_serializer = AdminRegistrationSerializer(data=data)
    if not admin_serializer.is_valid():
        return Response({"message": "error", "error_message": admin_serializer.errors},
                        status=status.HTTP_200_OK)
    admin_serializer.save()
    org_data['admin'] = admin_serializer.data['id']
    # changes in admin data
    admin_data = CustomUserModel.objects.get(username=admin_serializer.data['username'])
    admin_data.is_admin = True
    admin_data.is_user = False
    admin_data.save()
    # # retrieve db data from database
    # db_data = OrgDbModel.objects.get(id=db_creation['id'])
    #
    # # database connection
    # org_db_connection(db_data)
    # new_db_connection = 'users'

    # serializer validation
    org_serializer = OrganizationSerializer(data=org_data)
    if org_serializer.is_valid():
        org_serializer.save()
        # Get current time
        current_time = datetime.now().strftime('%Y%m%d%H%M%S')
        # Make the db name unique
        db_name = str(org_data['name'] + str(current_time))
        # Database creation
        db_creation = database_creation(db_name, data['username'], data['password'], admin_serializer.data['id'],
                                        org_serializer.data['id'])
        # table migration
        org_db_migration(db_creation)
        # validated_data = org_serializer.validated_data
        #
        # # custom validation for specific database (Cause serializer validation using default database configuration)
        # validation_errors = org_data_custom_validation(validated_data, new_db_connection)
        # if validation_errors:
        #     return Response(validation_errors, status=status.HTTP_200_OK)
        #
        # # save the data in the organization's specific database
        # org_instance = OrganizationModel(**validated_data)
        # org_instance.save(using=new_db_connection)
        #
        # # serializer representation for model instance
        # response_data = org_serializer.to_representation(org_instance)
    else:
        return Response(
            {
                "message": "error",
                "error_message": org_serializer.errors
            },
            status=status.HTTP_200_OK)

    return Response(
        {
            "message": "success",
            "data": admin_serializer.data,
            "organization_data": org_serializer.data
        },
        status=status.HTTP_200_OK
    )


# login
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    login_serializer = LoginSerializer(data=request.data)
    try:
        user = CustomUserModel.objects.get(username=request.data['username'])
    except:
        return Response(
            {
                "message": "error",
                "error_message": "user not found"
            }, status=status.HTTP_200_OK)

    # validate the password
    if not user.check_password(request.data['password']):
        return Response(
            {
                "message": "error",
                "error_message": "wrong password"
            }, status=status.HTTP_200_OK)

    # oauth2 token api call
    r = requests.post('http://127.0.0.1:8000/o/token/',
                      data={
                          'grant_type': 'password',
                          'username': user.username,
                          'password': request.data['password'],
                          'client_id': settings.OAUTH_CLIENT_ID,
                          'client_secret': settings.OAUTH_CLIENT_SECRET}
                      )
    return Response(
        {
            "message": "success",
            "user_data": AdminRegistrationSerializer(user).data,
            "headers": r.json()
        }
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def user_registration(request):
    data = request.data
    data['is_admin'] = False
    data['is_user'] = True
    if 'organization' in request.data:
        try:
            org = OrganizationModel.objects.get(id=request.data['organization'])
        except:
            return Response(
                {
                    "message": "error",
                    "error_message": {
                        "organization": {"Invalid organization details"}
                    }
                },
                status=status.HTTP_200_OK
            )

    user_serializer = UserRegistrationSerializer(data=data)
    if not user_serializer.is_valid():
        return Response({"message": "error", "error_message": user_serializer.errors},
                        status=status.HTTP_200_OK)

    user_serializer.save()

    return Response(
        {
            "message": "success",
            "data": user_serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def org_registration(request):
    if request.user.is_admin:
        if request.data['db_type'] == "combined":
            if "database" not in request.data:
                return Response(
                    {
                        "message": "error",
                        "error_message": {
                            "database": "This field is required"
                        }
                    }
                )
        request.data['admin'] = request.user.id
        org_serializer = OrganizationSerializer(data=request.data)
        if not org_serializer.is_valid():
            return Response(
                {
                    "message": "error",
                    "error_message": org_serializer.errors
                },
                status=status.HTTP_200_OK
            )
        org_serializer.save()
        if request.data['db_type'] == "combined":
            db_model = OrgDbModel.objects.filter(id=request.data['database'])
            if not db_model.exists():
                return Response(
                    {
                        "message": "error",
                        "error_message": "Invalid database details"
                    },
                    status=status.HTTP_200_OK
                )
            db = db_model.first()
            print(db, org_serializer.data)
            db.organization.add(org_serializer.data['id'])
        else:
            current_time = datetime.now().strftime('%Y%m%d%H%M%S')
            db_name = str(org_serializer.data['name'] + str(current_time))
            username = request.user.username+str(current_time)
            password = request.user.username+current_time[-5:]
            db = database_creation(db_name, username, password, request.user.id, org_serializer.data['id'])
            org_db_migration(db)
        return Response(
            {
                "message": "success",
                "data": org_serializer.data
            }
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
@permission_classes([IsAuthenticated])
def database_list(request):
    if request.user.is_admin:
        database = request.user.orgdbmodel_set.all()
        db_serializer = OrgDbSerializer(database, many=True)
        return Response(
            {
                "message": "success",
                "data": db_serializer.data
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
@permission_classes([IsAuthenticated])
def get_user_org(request):
    if request.user.is_admin:
        org_data = request.user.organizationmodel_set.all()
        org_serializer = OrganizationSerializer(org_data, many=True)
        return Response(
            {
                "message": "success",
                "data": org_serializer.data
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
