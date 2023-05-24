from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from base.manageImages import *
from base.predict import predict


@login_required(login_url='/login/')
@user_passes_test(lambda user: user.user_type == '2')
def doctorHome(request):
    user = request.user
    # patientcount = user.doctor.patient.all().count()
    context = {

    }
    return render(request, "doctorHome.html", {"context": context})


@login_required(login_url='/login/')
@user_passes_test(lambda user: user.user_type == '2')
def segmentation(request):
    if 'submit' in request.POST:
        try:
            file = request.FILES['fileInput']
            data = file.read()
            encoded = b64encode(data).decode()
            mime = 'image/jpeg;'
            imagep = PIL_Image.open(file)
            mask = predict(imagep)
            image = "data:%sbase64,%s" % (mime, encoded)
            imgAndMask = PIL_Image.composite(imagep.convert('RGB'), mask.convert('RGB'), mask)

            context = {
                "imageAndMask": imageToStr(imgAndMask),
                "mask": imageToStr(mask),
                "image": image,
            }

            return render(request, 'carouselimages.html', context)
        except:
            messages.error(request, "Failed to upload")
            return HttpResponseRedirect(reverse("segmentation"))

    if 'submitReport' in request.POST:
        all_points_x = request.POST.get('x')
        all_points_y = request.POST.get('y')
        image = request.POST.get('i')
        mask = request.POST.get('m')
        imgAndMask = request.POST.get('im')

        context = {
            "imageAndMask": imgAndMask,
            "mask": mask,
            "image": image,
        }

        createMask(request, image, all_points_x, all_points_y, save='YES')
        try:
            messages.success(request, "Thank you for your feedback!")
            return render(request, 'carouselimages.html', context)
        except:
            messages.error(request, "Failed to send feedback...")
            return render(request, 'carouselimages.html', context)

    return render(request, 'uploadImagePage.html')


@login_required(login_url='/login/')
@user_passes_test(lambda user: user.user_type == '2')
def patients(request):
    user = request.user
    # patients = user.doctor.patient.all() 
    # logging.warning(patients) 

    content = {
        "user": user,
        # "patients" : patients
        # "patientMoreInfo" : patientMoreInfo
    }

    return render(request, 'patients.html', content)
