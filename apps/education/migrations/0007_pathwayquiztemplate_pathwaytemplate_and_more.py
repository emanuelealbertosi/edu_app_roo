# Generated by Django 5.1.7 on 2025-04-04 12:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('education', '0006_remove_pathwayassignment_due_date_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PathwayQuizTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(help_text='Order of the quiz template within the pathway template.', verbose_name='Order')),
                ('quiz_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='education.quiztemplate')),
            ],
            options={
                'verbose_name': 'Pathway Quiz Template',
                'verbose_name_plural': 'Pathway Quiz Templates',
                'ordering': ['pathway_template', 'order'],
            },
        ),
        migrations.CreateModel(
            name='PathwayTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='E.g., points_on_completion. Example: {"points_on_completion": 50}', verbose_name='Metadata')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('quiz_templates', models.ManyToManyField(related_name='pathway_templates', through='education.PathwayQuizTemplate', to='education.quiztemplate', verbose_name='Quiz Templates')),
                ('teacher', models.ForeignKey(limit_choices_to={'role': 'TEACHER'}, on_delete=django.db.models.deletion.CASCADE, related_name='created_pathway_templates', to=settings.AUTH_USER_MODEL, verbose_name='Teacher')),
            ],
            options={
                'verbose_name': 'Pathway Template',
                'verbose_name_plural': 'Pathway Templates',
                'ordering': ['title'],
            },
        ),
        migrations.AddField(
            model_name='pathwayquiztemplate',
            name='pathway_template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='education.pathwaytemplate'),
        ),
        migrations.AddField(
            model_name='pathway',
            name='source_template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pathways_from_template', to='education.pathwaytemplate', verbose_name='Source Template'),
        ),
        migrations.AlterUniqueTogether(
            name='pathwayquiztemplate',
            unique_together={('pathway_template', 'order')},
        ),
    ]
