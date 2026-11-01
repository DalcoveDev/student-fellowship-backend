from django.db import migrations


def sync_superuser_roles(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(is_superuser=True).update(role='admin', is_staff=True)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_user_bio'),
    ]

    operations = [
        migrations.RunPython(sync_superuser_roles, migrations.RunPython.noop),
    ]
