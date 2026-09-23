from django.db import migrations, models
import tracker.models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobapplication',
            name='applied_date',
            field=models.DateField(validators=[tracker.models.validate_not_in_future]),
        ),
    ]
