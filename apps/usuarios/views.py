from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from supabase import create_client
from .utils import sync_supabase_user_to_django

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                django_user = sync_supabase_user_to_django(auth_response.user)
                login(request, django_user)
                return redirect('home')
            
        except Exception as e:
            print(f"Erro de login: {str(e)}")
            messages.error(request, 'Credenciais inválidas')
    
    return render(request, 'registration/login.html')

@login_required
def logout_view(request):
    try:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        supabase.auth.sign_out()
    except Exception as e:
        print(f"Erro ao fazer logout no Supabase: {str(e)}")
    
    logout(request)
    messages.success(request, 'Logout realizado com sucesso')
    return redirect('login')

@login_required
def home(request):
    return render(request, 'home.html')