from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from base.emailBackEnd import EmailBackEnd
from base.models import CustomUser, Doctor


def showLoginPage(request):
    return render(request, "Authentication/loginPage.html")


def showSignUpPage(request):
    return render(request, "Authentication/signUpPage.html")


def doSignUp(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        lastname = request.POST.get("lastname")
        name = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        birthday = request.POST.get("birthday")
        role = request.POST.get("role")
        try:
            user = CustomUser.objects.create_user(
                username=name,
                first_name=name,
                last_name=lastname,
                birthday=birthday,
                email=email,
                password=password,
                is_staff=False,
                is_active=True,
                is_superuser=False,
                user_type=role
            )
            user.save()

            if role == 2:
                u = CustomUser.objects.get(email=email)
                doctor = Doctor(user=u)
                doctor.save()

            messages.success(request, "Successfully signed up")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        except:
            messages.error(request, "Failed to signed up")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def doLogin(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        user = EmailBackEnd.authenticate(request, username=request.POST.get("email"),
                                         password=request.POST.get("password"))
        if user != None:
            login(request, user)
            if user.user_type == "1":
                return HttpResponseRedirect('/adminHome')
            elif user.user_type == "2":
                return HttpResponseRedirect("/doctorHome")
            else:
                return HttpResponseRedirect("/")
        else:
            messages.error(request, "Invalid Login Details")
            return HttpResponseRedirect("/")


def logout(request):
    logout(request)
    return HttpResponseRedirect("/")
