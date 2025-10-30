from django.views import View
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from web_project import TemplateLayout, TemplateHelper  # keep your existing layout logic
from django.contrib.auth.models import User
from django.contrib.auth import logout
from inventory_app.models import LoginRecord
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('auth-login-basic') 
    

class AuthView(View):
    template_name = "auth_login_basic.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("index")
        
        context = TemplateLayout.init(self, {})
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_blank.html", context),
        })
        return render(request, self.template_name, context)

    def post(self, request):
        username = request.POST.get("email-username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        context = TemplateLayout.init(self, {})
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_blank.html", context),
        })

        if user is not None:
            login(request, user)

            # 🔐 Optional: Safe logging and notification
            try:
                ip_address = get_client_ip(request)
                user_agent = request.META.get("HTTP_USER_AGENT", "")

                # Create login record in DB
                LoginRecord.objects.create(
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                # Send email notification to admin
                subject = f"Login Alert: {user.full_name}"
                message = (
                    f"User: {user.full_name} (ID: {user.id})\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"IP Address: {ip_address}\n"
                    f"User Agent: {user_agent}\n"
                )
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    fail_silently=False,
                )

            except Exception as e:
                # Log error if needed, but don’t interrupt login
                print(f"Login tracking failed: {e}")  # Optional: use logging.warning()

            return redirect("index")  # dashboard or homepage
        else:
            context["error"] = "Invalid username or password"
            return render(request, self.template_name, context)




class RegisterView(View):
    template_name = "auth_register_basic.html"

    def get(self, request):
        context = TemplateLayout.init(self, {})
        context["layout_path"] = TemplateHelper.set_layout("layout_blank.html", context)
        return render(request, self.template_name, context)

    def post(self, request):
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        terms = request.POST.get("terms")

        context = TemplateLayout.init(self, {})
        context["layout_path"] = TemplateHelper.set_layout("layout_blank.html", context)

        if not terms:
            context["error"] = "You must agree to the terms and conditions."
            return render(request, self.template_name, context)

        if User.objects.filter(username=username).exists():
            context["error"] = "Username already exists."
            return render(request, self.template_name, context)

        if User.objects.filter(email=email).exists():
            context["error"] = "Email already registered."
            return render(request, self.template_name, context)

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)  # Auto-login after registration
        return redirect("index")


from django.contrib.auth.tokens import default_token_generator
from inventory_app.models import UserAccount
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode
from django.views.generic import TemplateView
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone


class ForgotPasswordView(TemplateView):
    template_name = "auth_forgot_password_basic.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['layout_path'] = 'layout/auth_base.html'  # or your actual base
        return context

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        user = UserAccount.objects.filter(email=email).first()

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = request.build_absolute_uri(f'/reset-password/{uid}/{token}/')

            subject = "Password Reset Requested"
            from_email = 'no-reply@example.com'
            to_email = [email]

            html_content = render_to_string('reset_email.html', {
                'user': user,
                'reset_link': reset_link,
                'now': timezone.now(),
                'site_name': 'RADHE TOOLS AND HARDWARE',
            })

            msg = EmailMultiAlternatives(subject, "", from_email, to_email)
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            messages.success(request, "Reset link sent to your email.")
        else:
            messages.error(request, "User with this email does not exist.")

        return redirect('auth-forgot-password-basic')


class ResetPasswordView(View):
    def get(self, request, uidb64, token):
        context = TemplateLayout.init(self, {})
        context.update({
            'uidb64': uidb64,
            'token': token,
            'layout_path': TemplateHelper.set_layout("layout_blank.html", context),
        })
        return render(request, 'reset_password.html', context)

    def post(self, request, uidb64, token):
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        print(f"Received password: {password}, Confirm password: {password2}")

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect(request.path)

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = UserAccount.objects.get(pk=uid)

            if default_token_generator.check_token(user, token):
                user.set_password(password)
                user.save()
                messages.success(request, "Password reset successful.")
                return redirect('auth-login-basic')
            else:
                messages.error(request, "Invalid or expired reset link.")
        except Exception as e:
            messages.error(request, e)

        return redirect(request.path)
