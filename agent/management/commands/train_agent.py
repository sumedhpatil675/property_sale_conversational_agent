from django.core.management.base import BaseCommand
from agent.vanna_setup import setup_vanna_training

class Command(BaseCommand):
    help = 'Enhances Vanna training with DDL, documentation, and SQL examples.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Vanna training enhancement...'))
        try:
            setup_vanna_training()
            self.stdout.write(self.style.SUCCESS('Successfully completed Vanna training enhancement.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during training: {str(e)}'))

