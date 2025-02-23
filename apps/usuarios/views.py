from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from supabase import create_client, Client
from django.conf import settings

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or 'home'
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not email or not password:
            messages.error(request, 'Preencha todos os campos obrigatórios.')
            return render(request, 'registration/login.html', {'next': next_url})
        
        try:
            response = settings.SUPABASE_CLIENT.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            user = response.user
            session = response.session
            
            if user and session:
                django_user, created = User.objects.update_or_create(
                    username=email,
                    defaults={
                        'email': email,
                        'is_active': True
                    }
                )
                django_user.set_unusable_password()
                django_user.save()
                
                login(request, django_user)
                messages.success(request, 'Login realizado com sucesso!')
                return redirect(next_url)
            
            messages.error(request, 'Credenciais inválidas.')
            
        except Exception as error:
            print(f"Erro de login: {error}")  # Para debug
            messages.error(request, 'Erro ao realizar login. Verifique suas credenciais.')
            return render(request, 'registration/login.html', {
                'email': email,
                'next': next_url
            })
    
    return render(request, 'registration/login.html', {
        'next': next_url
    })

@login_required
def logout_view(request):
    try:
        settings.SUPABASE_CLIENT.auth.sign_out()
    except Exception as error:
        print(f"Erro no logout Supabase: {error}")  # Para debug
    
    logout(request)
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('login')

@login_required(login_url='login')
def home(request):
    context = {
        'user': request.user
    }
    return render(request, 'home.html', context)