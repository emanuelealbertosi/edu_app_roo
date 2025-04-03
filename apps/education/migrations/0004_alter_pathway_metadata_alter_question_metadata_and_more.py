# Generated by Django 5.1.7 on 2025-04-03 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('education', '0003_pathwayprogress_first_correct_completion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pathway',
            name='metadata',
            field=models.JSONField(blank=True, default=dict, help_text='E.g., points_on_completion. Example: {"points_on_completion": 50}', verbose_name='Metadata'),
        ),
        migrations.AlterField(
            model_name='question',
            name='metadata',
            field=models.JSONField(blank=True, default=dict, help_text='Specific config based on type. E.g., for FILL_BLANK: {"correct_answers": ["Rome", "rome"], "case_sensitive": false}. For MC/TF: {"points_per_correct_answer": 1}. For OPEN_MANUAL: {"max_score": 5}.', verbose_name='Metadata'),
        ),
        migrations.AlterField(
            model_name='questiontemplate',
            name='metadata',
            field=models.JSONField(blank=True, default=dict, help_text='Specific config based on type. E.g., for FILL_BLANK: {"correct_answers": ["Paris", "paris"], "case_sensitive": false}. For MC/TF: {"points_per_correct_answer": 2}.', verbose_name='Metadata'),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='metadata',
            field=models.JSONField(blank=True, default=dict, help_text='E.g., difficulty, subject, completion_threshold_percent (0-100), points_on_completion. Example: {"difficulty": "hard", "completion_threshold_percent": 75.0, "points_on_completion": 10}', verbose_name='Metadata'),
        ),
        migrations.AlterField(
            model_name='quizattempt',
            name='status',
            field=models.CharField(choices=[('IN_PROGRESS', 'In Progress'), ('PENDING', 'Pending Manual Grading'), ('COMPLETED', 'Completed (Passed)'), ('FAILED', 'Completed (Failed)')], default='IN_PROGRESS', max_length=20, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='quiztemplate',
            name='metadata',
            field=models.JSONField(blank=True, default=dict, help_text='Extra data like difficulty ("easy", "medium", "hard"), subject ("Math", "History"), etc. Example: {"difficulty": "medium", "subject": "Physics"}', verbose_name='Metadata'),
        ),
    ]
