from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from hatchway.models import AuthToken

User = get_user_model()


class Command(BaseCommand):
    help = "Create an authentication token for a user"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)
        parser.add_argument("--days", type=int, default=365)
        parser.add_argument("--description", type=str, default="")

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{options["username"]}" does not exist')
            )
            return

        token = AuthToken.create_token(
            user=user, days_valid=options["days"], description=options["description"]
        )
        self.stdout.write(self.style.SUCCESS(f"Created token: {token.key}"))
