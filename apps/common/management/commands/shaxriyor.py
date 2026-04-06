from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Calls Shaxriyor and if he does not answer, assumes he is with girls!"

    def add_arguments(self, parser):
        parser.add_argument("girl_name", nargs="+", type=str, default="")

    def handle(self, *args, **options):
        girl_name = options["girl_name"][0]
        import random

        shaxriyor_response = random.choice([True, False])
        if shaxriyor_response:
            self.stdout.write(self.style.SUCCESS("Shaxriyor answered! He is aqlli bola!"))
        else:
            self.stdout.write(self.style.WARNING(f"Shaxriyor is with {girl_name}! What the heck bro? :)"))
