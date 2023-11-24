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
    context = {
        "user": user
    }
    return render(request, "doctorHome.html", {"context": context})


def image_to_str(image, format='PNG'):
    # Convert the PIL Image to a BytesIO object
    img_byte_array = BytesIO()
    image.save(img_byte_array, format=format)

    # Convert the BytesIO object to a base64-encoded string
    img_str = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')

    # Add the 'data:image' prefix based on the specified format
    return f'data:image/{format.lower()};base64,{img_str}'
@login_required(login_url='/login/')
@user_passes_test(lambda user: user.user_type == '2')
def segmentation(request):
    if 'submit' in request.POST:
        file = request.FILES['fileInput']
        imagep = PIL_Image.open(file)
        mask = predict(imagep)
        imgAndMask = PIL_Image.composite(imagep.convert('RGBA'),
                                               mask.convert('L').resize(imagep.size).convert('RGBA'), mask.convert('L'))

        context = {
            "imageAndMask": image_to_str(imgAndMask, format='PNG'),
            "mask": image_to_str(mask, format='PNG'),
            "image": image_to_str(imagep, format='JPEG'),
        }
        return render(request, 'carouselimages.html', context)


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
