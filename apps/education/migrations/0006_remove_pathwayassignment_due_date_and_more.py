# Generated by Django 5.1.7 on 2025-04-04 08:39

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('education', '0005_alter_quiz_description'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pathwayassignment',
            name='due_date',
        ),
        migrations.RemoveField(
            model_name='quizassignment',
            name='due_date',
        ),
        migrations.AddField(
            model_name='pathwayprogress',
            name='completed_orders',
            field=models.JSONField(blank=True, default=list, help_text='List of order numbers of successfully completed quizzes in this pathway.', verbose_name='Completed Quiz Orders'),
        ),
        migrations.AddField(
            model_name='pathwayprogress',
            name='points_earned',
            field=models.IntegerField(blank=True, null=True, verbose_name='Points Earned'),
        ),
        migrations.AlterField(
            model_name='pathwayassignment',
            name='assigned_by',
            field=models.ForeignKey(limit_choices_to={'role__in': ['TEACHER', 'ADMIN']}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_pathways', to=settings.AUTH_USER_MODEL, verbose_name='Assigned By'),
        ),
        migrations.AlterField(
            model_name='pathwayprogress',
            name='first_correct_completion',
            field=models.BooleanField(default=False, verbose_name='First Correct Completion'),
        ),
        migrations.AlterField(
            model_name='pathwayprogress',
            name='last_completed_quiz_order',
            field=models.IntegerField(blank=True, help_text='The order number of the last successfully completed quiz in the pathway.', null=True, verbose_name='Last Completed Quiz Order'),
        ),
        migrations.AlterField(
            model_name='quizassignment',
            name='assigned_by',
            field=models.ForeignKey(limit_choices_to={'role__in': ['TEACHER', 'ADMIN']}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_quizzes', to=settings.AUTH_USER_MODEL, verbose_name='Assigned By'),
        ),
        migrations.AlterField(
            model_name='studentanswer',
            name='answered_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Answered At'),
        ),
        migrations.AlterField(
            model_name='studentanswer',
            name='is_correct',
            field=models.BooleanField(blank=True, help_text='Null for manually graded questions until graded.', null=True, verbose_name='Is Correct?'),
        ),
        migrations.AlterField(
            model_name='studentanswer',
            name='score',
            field=models.FloatField(blank=True, help_text='Specific score for this answer, especially for manual grading.', null=True, verbose_name='Score'),
        ),
        migrations.AlterField(
            model_name='studentanswer',
            name='selected_answers',
            field=models.JSONField(help_text='Format depends on question type. E.g., {"answer_option_id": 123} for MC_SINGLE/TF, {"answer_option_ids": [123, 456]} for MC_MULTI, {"answers": ["Paris"]} for FILL_BLANK, {"text": "..."} for OPEN_MANUAL.', verbose_name='Selected Answers'),
        ),
    ]
