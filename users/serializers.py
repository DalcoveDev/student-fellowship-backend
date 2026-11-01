from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import UserAuditLog

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'avatar',
            'bio',
            'twitter',
            'github',
            'website')
        read_only_fields = ('id', 'role')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name')

    def validate_password(self, value):
        # Run Django's built-in password validators
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role='reader',
        )
        return user


class CMSUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'avatar',
            'bio',
            'twitter',
            'github',
            'website',
            'is_active',
            'date_joined')
        read_only_fields = ('id', 'date_joined')

    def validate_email(self, value):
        if value:
            qs = User.objects.filter(email__iexact=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        if request and self.instance and self.instance.pk == request.user.pk:
            if 'role' in attrs and attrs['role'] != self.instance.role:
                raise serializers.ValidationError({
                    'role': 'You cannot change your own role.'
                })
            if attrs.get('is_active') is False:
                raise serializers.ValidationError({
                    'is_active': 'You cannot deactivate your own account.'
                })
        return attrs


class CMSUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'role',
            'is_active',
            'avatar',
            'bio',
            'twitter',
            'github',
            'website')

    def validate_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        avatar = validated_data.get('avatar')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', 'reader'),
            is_active=validated_data.get('is_active', True),
        )
        # Set avatar if provided
        if avatar:
            user.avatar = avatar
        # Set staff status based on role
        user.is_staff = user.role in ('admin', 'editor', 'journalist')
        # Set other profile fields
        user.bio = validated_data.get('bio', '')
        user.twitter = validated_data.get('twitter', '')
        user.github = validated_data.get('github', '')
        user.website = validated_data.get('website', '')
        user.save()
        return user


class UserAuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True, default='System')
    target_username = serializers.CharField(source='target_user.username', read_only=True)

    class Meta:
        model = UserAuditLog
        fields = ('id', 'actor', 'actor_username', 'target_user', 'target_username', 'action', 'details', 'timestamp')
