from django.contrib.auth.models import User
from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
import random
from django.core.mail import send_mail
from cryptography.fernet import Fernet
from mechanize import Browser
import favicon
from .models import Password

br = Browser()
br.set_handle_robots(False)

fernet = Fernet(settings.KEY)

def home(request):
    if request.method == "POST":
        if "signup-form" in request.POST:
            username = request.POST.get("username")
            email = request.POST.get("email")
            password = request.POST.get("password")
            password2 = request.POST.get("password2")
            #if passwords are not identical
            if password!= password2:
                msg = "please makje sure the passwords are identical"
                messages.error(request,msg)
                return HttpResponseRedirect(request.path)
            #ser identical
            elif User.objects.filter(username=username).exists():
                msg = f"{username} already exists"
                messages.error(request,msg)
                return HttpResponseRedirect(request.path)
            #email identical
            elif User.objects.filter(email=email).exists():
                msg = f"{email} already exists"
                messages.error(request,msg)
                return HttpResponseRedirect(request.path)
            else:
                User.objects.create_user(username,email,password)
                new_user = authenticate(request,username=username,password=password2)
                if new_user is not None:
                    login(request,new_user)
                    msg = f"{username} Logged in!"
                    messages.success(request,msg)
                    return HttpResponseRedirect(request.path)
        elif "logout" in request.POST:
            msg = "Logged out!"
            logout(request)
            messages.success(request,msg)
            return HttpResponseRedirect(request.path)
        elif 'login-form' in request.POST:
            username = request.POST.get("username")
            password = request.POST.get("password")
            new_login = authenticate(request,username=username,password=password)
            if new_login is None:
                msg = "Log in failed"
                messages.error(request,msg)
                return HttpResponseRedirect(request.path)
            else:
                code = str(random.randint(100000,999999))
                global global_code
                global_code = code
                send_mail(
                    "Django Password Manager: confirm email",
                    f"Your verification code is {code}.",
                    settings.EMAIL_HOST_USER,
                    [new_login.email],
                    fail_silently=False,

                )
                return render(request,"home.html", {
                    "code":code,
                    "user":new_login,
                })

        elif "confirm" in request.POST:
            input_code = request.POST.get("code")
            user = request.POST.get("user")
            if input_code != global_code:
                msg = "wrong code mr"
                messages.error(request,msg)
                return HttpResponseRedirect(request.path)
            else:
                login(request,User.objects.get(username=user))
                msg = "succes dude"
                messages.success(request,msg)
                return HttpResponseRedirect(request.path)
        
        elif "add-password" in request.POST:
            url = request.POST.get("url")
            email = request.POST.get("email")
            password = request.POST.get("password")
            #encrypt
            encrypted_email = fernet.encrypt(email.encode())

            encrypted_password = fernet.encrypt(password.encode())
            #get title of the website
            br.open(url)
            title = br.title()
            #link of the logo favicon
            icon = favicon.get(url)[0].url
            #save data
            new_password = Password.objects.create(
                user = request.user,
                name = title,
                logo = icon,
                email = encrypted_email.decode(),
                password = encrypted_password.decode(),
            )
            msg = "Password has been saved successfully"
            messages.success(request,msg)
            return HttpResponseRedirect(request.path)

        elif "delete" in request.POST:
            to_delete = request.POST.get("password-id")
            msg = "Password has been deleted :("
            Password.objects.get(id=to_delete).delete()
            messages.success(request,msg)
            return HttpResponseRedirect(request.path)
            
    context = {}
    if request.user.is_authenticated:
        passwords = Password.objects.all().filter(user = request.user.id)
        for password in passwords:
            password.email = fernet.decrypt(password.email.encode()).decode()
            password.password = fernet.decrypt(password.password.encode()).decode()
        context = {
            "passwords": passwords,
        }

    return render(request, "home.html", )