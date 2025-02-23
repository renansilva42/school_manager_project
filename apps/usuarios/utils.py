from django.contrib.auth.models import User

def sync_supabase_user_to_django(supabase_user):
    user, created = User.objects.get_or_create(
        username=supabase_user.email,
        defaults={
            'email': supabase_user.email,
            'is_active': True
        }
    )
    return user