from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.conf import settings
from supabase import create_client

def is_admin(user):
    return user.is_superuser or user.groups.filter(name='Administradores').exists()

@login_required
@user_passes_test(is_admin)
def user_management(request):
    users = User.objects.all()
    return render(request, 'usuarios/user_management.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def settings_view(request):
    if request.method == 'POST':
        # Add settings save logic here
        messages.success(request, 'Configurações salvas com sucesso!')
        return redirect('settings')
    return render(request, 'usuarios/settings.html')

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
                # Create or update Django user
                django_user, created = User.objects.get_or_create(
                    username=email,
                    defaults={'email': email, 'is_active': True}
                )
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