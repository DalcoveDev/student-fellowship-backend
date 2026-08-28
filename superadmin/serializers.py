from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers

from .models import SystemAuditLog
from layout.models import SiteSetting

User = get_user_model()


class SystemAuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True, default='System')
    actor_email = serializers.CharField(source='actor.email', read_only=True, default='')
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = SystemAuditLog
        fields = (
            'id',
            'actor',
            'actor_username',
            'actor_email',
            'action',
            'action_display',
            'target_model',
            'target_id',
            'details',
            'ip_address',
            'timestamp',
        )
        read_only_fields = fields


class PermissionSerializer(serializers.ModelSerializer):
    app_label = serializers.CharField(source='content_type.app_label', read_only=True)
    model = serializers.CharField(source='content_type.model', read_only=True)

    class Meta:
        model = Permission
        fields = ('id', 'name', 'codename', 'app_label', 'model')


class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        source='permissions',
        write_only=True,
        required=False,
    )
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ('id', 'name', 'permissions', 'permission_ids', 'user_count')

    def get_user_count(self, obj):
        return obj.user_set.count()


class SuperAdminUserSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        read_only=True,
    )
    group_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        source='groups',
        write_only=True,
        required=False,
    )
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'role_display',
            'is_active',
            'is_staff',
            'is_superuser',
            'avatar',
            'bio',
            'twitter',
            'github',
            'website',
            'groups',
            'group_ids',
            'date_joined',
            'last_login',
        )
        read_only_fields = ('date_joined', 'last_login')


class SuperAdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    group_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        source='groups',
        required=False,
    )

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
            'is_staff',
            'is_superuser',
            'bio',
            'twitter',
            'github',
            'website',
            'group_ids',
        )

    def create(self, validated_data):
        groups = validated_data.pop('groups', [])
        password = validated_data.pop('password')
        role = validated_data.get('role', 'reader')

        if 'is_staff' not in validated_data:
            validated_data['is_staff'] = role in ('admin', 'editor', 'journalist')
        if 'is_superuser' not in validated_data:
            validated_data['is_superuser'] = role == 'admin'

        user = User.objects.create_user(password=password, **validated_data)
        if groups:
            user.groups.set(groups)
        return user


class SuperAdminSiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = '__all__'

