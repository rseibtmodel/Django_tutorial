from django.db import migrations


def seed_personas_sistema(apps, schema_editor):
    Persona = apps.get_model('app_chatbot', 'Persona')

    # Garante que a Persona Padrão exista
    if not Persona.objects.filter(slug="padrao", is_sistema=True).exists():
        Persona.objects.create(
            nome="Assistente Geral",
            slug="padrao",
            is_sistema=True,
            descricao_curta="Assistente inteligente padrão.",
            tom_de_voz="objetivo",
            profissao_cargo="Assistente Virtual",
            diretrizes_comportamento="Responda com clareza e precisão em português do Brasil.",
        )


def rollback_seed_personas(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app_chatbot', '0005_alter_sessaochat_acessado_em_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_personas_sistema, reverse_code=rollback_seed_personas),
    ]
