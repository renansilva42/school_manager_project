from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from supabase import create_client, Client
from django.conf import settings

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            user = response.user
            if user:
                # Simula um usuário Django para autenticação
                from django.contrib.auth.models import User
                django_user, created = User.objects.get_or_create(username=email, email=email)
                login(request, django_user)
                return redirect('lista_alunos')
            else:
                messages.error(request, 'Credenciais inválidas.')
        except Exception as e:
            messages.error(request, f'Erro ao fazer login: {str(e)}')
    return render(request, 'usuarios/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')