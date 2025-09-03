from django.contrib.auth.backends import ModelBackend
from inventory_app.models import UserAccount
from django.db.models import Q

class MobileOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = UserAccount.objects.get(
                Q(email=username) | Q(mobile=username)
            )
        except UserAccount.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
