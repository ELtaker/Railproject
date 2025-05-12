from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_company")
    ]
    operations = [
        migrations.RemoveField(
            model_name="user",
            name="is_member",
        ),
        migrations.RemoveField(
            model_name="user",
            name="is_business",
        ),
    ]
