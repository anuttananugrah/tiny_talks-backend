from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("user", "0002_alter_user_gender")]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="otp",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="otp_attempts",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="user",
            name="otp_created_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
