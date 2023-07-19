from django.contrib.auth.hashers import make_password
from rest_framework.serializers import ModelSerializer, CharField, EmailField, ValidationError, Serializer
from .models import *
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField


class OrganizationSerializer(ModelSerializer):
    class Meta:
        model = OrganizationModel
        fields = '__all__'

    db_type = serializers.ChoiceField(choices=[("separate", "separate"), ("combined", "combined")], required=True)

    def validate(self, attrs):
        attrs.pop('db_type')
        return attrs

    def to_representation(self, obj):
        # remove the db_type field
        """
            https://www.django-rest-framework.org/api-guide/serializers/#overriding-serialization-and-deserialization-behavior
        """
        if "db_type" in self.fields:
            self.fields.pop('db_type')
        ret = super(OrganizationSerializer, self).to_representation(obj)
        return ret


class AdminRegistrationSerializer(ModelSerializer):
    class Meta:
        model = CustomUserModel
        fields = '__all__'

        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUserModel(**validated_data)
        user.set_password(password)
        user.save()
        return user
    # organization_name = CharField(max_length=150, required=True)
    # organization_mail = EmailField(max_length=256, required=True)
    # organization_mob_no = PhoneNumberField(required=True)
    # organization_address = CharField(max_length=500, required=True)
    #
    # def validate(self, attrs):
    #     org_mail = attrs.get('organization_mail')
    #     org_mob_no = attrs.get('organization_mob_no')
    #
    #     # Check for duplicate entry for mail & mobile number within the organization model
    #
    #     existing_mail = OrganizationModel.objects.filter(email=org_mail).exists()
    #     existing_mob_no = OrganizationModel.objects.filter(mobile_number=org_mob_no).exists()
    #     if existing_mail:
    #         raise ValidationError(
    #             {"organization_mail": "Organization mail already exists"})
    #     if existing_mob_no:
    #         raise ValidationError(
    #             {"organization_mob_no": "Organization mobile number already exists"})
    #     return attrs


class LoginSerializer(Serializer):
    username = CharField(required=True)
    password = CharField(required=True)


class UserRegistrationSerializer(ModelSerializer):
    class Meta:
        model = CustomUserModel
        fields = '__all__'

        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUserModel(**validated_data)
        user.set_password(password)
        user.save()
        return user


class OrgDbSerializer(ModelSerializer):
    class Meta:
        model = OrgDbModel
        fields = '__all__'
