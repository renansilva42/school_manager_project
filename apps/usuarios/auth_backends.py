from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        print(f"Tentando autenticar: email={username}, senha={password}")
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
            print(f"Usuário encontrado: {user}")
        except UserModel.DoesNotExist:
            print("Usuário não encontrado")
            return None
        else:
            if user.check_password(password):
                print("Senha correta")
                return user
            else:
                print("Senha incorreta")
        return None