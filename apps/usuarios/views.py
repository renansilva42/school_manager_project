from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
import postgrest
from supabase import create_client

def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or 'home'
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not email or not password:
            messages.error(request, 'Preencha todos os campos obrigatórios.')
            return render(request, 'registration/login.html', {'next': next_url})
        
        try:
            # Create a new Supabase client for each request
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
            # Try to sign in
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Create or update Django user
                django_user, created = User.objects.update_or_create(
                    username=email,
                    defaults={
                        'email': email,
                        'is_active': True
                    }
                )
                
                login(request, django_user)
                messages.success(request, 'Login realizado com sucesso!')
                return redirect(next_url)
            
        except postgrest.exceptions.APIError as e:
            print(f"Supabase API Error: {e}")
            messages.error(request, 'Erro de API do Supabase.')
        except Exception as e:
            print(f"Login error: {e}")
            messages.error(request, 'Credenciais inválidas.')
        
        return render(request, 'registration/login.html', {
            'email': email,
            'next': next_url
        })
    
    return render(request, 'registration/login.html', {'next': next_url})

@login_required
def logout_view(request):
    try:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        supabase.auth.sign_out()
    except Exception as e:
        print(f"Supabase logout error: {e}")
    
    logout(request)
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('login')

@login_required(login_url='login')
def home(request):
    return render(request, 'home.html', {'user': request.user})