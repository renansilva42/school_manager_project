from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.conf import settings
from supabase import create_client
from .models import UserProfile
from core.models import SiteSettings
from core.utils import send_email_with_site_settings
import os

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
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get or create site settings
    site_settings = SiteSettings.get_settings()
    
    if request.method == 'POST':
        # Handle profile photo upload
        if 'profile_photo' in request.FILES:
            # Delete old photo if it exists
            if profile.photo:
                if os.path.isfile(profile.photo.path):
                    os.remove(profile.photo.path)
            
            # Save new photo
            profile.photo = request.FILES['profile_photo']
            profile.save()
            messages.success(request, 'Foto de perfil atualizada com sucesso!')
        
        # Handle general settings
        if 'school_name' in request.POST:
            site_settings.school_name = request.POST.get('school_name')
            site_settings.contact_email = request.POST.get('contact_email')
            site_settings.save()
            messages.success(request, 'Configurações gerais salvas com sucesso!')
        
        # Handle email settings
        if 'smtp_server' in request.POST:
            site_settings.smtp_server = request.POST.get('smtp_server')
            
            # Handle smtp_port (convert to int if not empty)
            smtp_port = request.POST.get('smtp_port')
            if smtp_port and smtp_port.isdigit():
                site_settings.smtp_port = int(smtp_port)
            else:
                site_settings.smtp_port = None
                
            site_settings.save()
            messages.success(request, 'Configurações de email salvas com sucesso!')
            
            # Test email settings if requested
            if 'test_email' in request.POST and request.POST.get('test_email') == 'true':
                if site_settings.contact_email:
                    success = send_email_with_site_settings(
                        subject='Teste de Configuração de Email',
                        message='Este é um email de teste para verificar as configurações de SMTP.',
                        recipient_list=[site_settings.contact_email],
                        html_message='<p>Este é um <strong>email de teste</strong> para verificar as configurações de SMTP.</p>'
                    )
                    
                    if success:
                        messages.success(request, f'Email de teste enviado com sucesso para {site_settings.contact_email}')
                    else:
                        messages.error(request, 'Falha ao enviar email de teste. Verifique as configurações de SMTP.')
                else:
                    messages.warning(request, 'Não foi possível enviar email de teste. Configure um email de contato primeiro.')
        
        return redirect('settings')
    
    # Get photo modification timestamp for cache busting
    photo_timestamp = None
    if profile.photo and profile.photo.name:
        try:
            photo_path = profile.photo.path
            photo_timestamp = int(os.path.getmtime(photo_path))
        except Exception:
            photo_timestamp = None
    
    return render(request, 'usuarios/settings.html', {
        'profile': profile,
        'settings': site_settings,
        'photo_timestamp': photo_timestamp,
    })

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
