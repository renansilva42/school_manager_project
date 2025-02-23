# apps/usuarios/views.py
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
        email = request.POST.get('username', '').strip()  # Alterado de 'email' para 'username'
        password = request.POST.get('password', '').strip()
        
        if not email or not password:
            messages.error(request, 'Preencha todos os campos obrigatórios.')
            return render(request, 'registration/login.html', {'next': next_url})
        
        try:
            # Usar o cliente diretamente do settings
            response = settings.SUPABASE_CLIENT.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # Verificação correta do usuário
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
            
            messages.error(request, 'Autenticação falhou.')
        
        except Exception as error:
            messages.error(request, f'Erro no login: {str(error)}')
            return render(request, 'registration/login.html', {
                'email': email,
                'next': next_url
            })
    
    return render(request, 'registration/login.html', {
        'next': next_url,
        'messages': messages.get_messages(request)
    })

def logout_view(request):
    try:
        # Logout no Supabase
        supabase.auth.sign_out()
    except Exception as error:
        messages.error(request, f'Erro no logout: {str(error)}')
    
    # Logout no Django
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('login')

@login_required(login_url='login')
def home(request):
    context = {
        'user': request.user,
        'supabase_user': supabase.auth.get_user() if supabase.auth else None
    }
    return render(request, 'home.html', context)