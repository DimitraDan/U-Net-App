import csv
import uuid

from django.conf import settings

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.hashers import make_password

from base.manageFolders import *
from base.manageImages import *
from base.predict import predict
from base.train import training


def download_csv_train_results(request, run_id):
    run = Run.objects.get(id=run_id)
    train_loss_data = run.train_loss.all()
    validation_data = run.validation_loss.all()

    # Prepare CSV data
    csv_data = []

    headers = set()  # Set to store unique headers
    headers.add('Run')
    headers.add('Created by')
    headers.add('Status')
    headers.add('Timestamp')
    headers.add('Epoch')
    headers.add('Step')
    headers.add('Train Loss')
    headers.add('Image')
    headers.add('True Image')
    headers.add('Predicted Image')
    headers.add('Validation IoU')

    # Append headers to csv_data
    csv_data.append(list(headers))

    # Fill data rows
    for train in train_loss_data:
        row = [run.name, run.trainer.username, run.status, str(run.date), train.epoch, train.step, train.train_loss]

        validation = find_matching_validation(validation_data, train.step, train.epoch)
        if validation is not None:
            row.extend([
                validation.image.url,
                validation.true_mask.url,
                validation.pred_mask.url,
                validation.validation_Iou
            ])
        else:
            row.extend(['', '', '', ''])

        csv_data.append(row)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="train_results.csv"'

    writer = csv.writer(response)
    for row in csv_data:
        writer.writerow(row)

    return response


def find_matching_validation(validation_data, step, epoch):
    for validation in validation_data:
        if validation.step == step and validation.epoch == epoch:
            return validation
    return None


def download_csv_user(request):
    users = CustomUser.objects.all()

    csv_data = []
    csv_data.append(['Id', 'Username', 'Last name', 'Email', 'Date joined', 'Role'])
    for user in users:
        csv_data.append([user.id, user.username, user.last_name, user.email, user.date_joined, user.user_type])

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="user_list_{}.csv"'.format(uuid.uuid4())

    writer = csv.writer(response)
    for row in csv_data:
        writer.writerow(row)

    return response


def download_csv(request):
    # Retrieve the data for the specified run_id
    runs = Run.objects.all()

    # Prepare the CSV data
    csv_data = []
    csv_data.append(['Run ID', 'Status', 'Created Date', 'Created By'])  # Header row
    for run in runs:
        csv_data.append([run.id, run.status, run.date, run.trainer.username])  # Data rows

    # Create a CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="run_{}.csv"'.format(uuid.uuid4())

    # Write the CSV data to the response
    writer = csv.writer(response)
    for row in csv_data:
        writer.writerow(row)

    return response


# views.py

from django.shortcuts import render
from django.db.models import Count
from django.db.models.functions import TruncDate
from .models import CustomUser


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def adminHome(request):
    user_type_counts_statistics = CustomUser.objects.values('user_type').annotate(user_type_count=Count('id'))
    # Truncate date to get only the date part
    user_date_joined_counts_statistics = CustomUser.objects.annotate(
        date_joined_formatted=TruncDate('date_joined')
    ).values('date_joined_formatted').annotate(user_date_count=Count('id'))

    # Initialize empty lists to store the user types and counts
    user_types = []
    user_type_counts = []

    user_dates = []
    user_date_counts = []

    # Loop through the queryset and extract the user types and counts
    for row in user_type_counts_statistics:
        user_types.append(row['user_type'])
        user_type_counts.append(row['user_type_count'])

    for row in user_date_joined_counts_statistics:
        user_dates.append(row['date_joined_formatted'].strftime('%Y-%m-%d'))  # Convert to string
        user_date_counts.append(row['user_date_count'])

    runs_per_date_statistics = Run.objects.values('date').annotate(run_count=Count('id'))
    runs_per_trainer_statistics = Run.objects.values('trainer_id').annotate(run_count=Count('id'))

    # Initialize empty lists to store the results
    dates = []
    run_counts_per_date = []

    trainer_ids = []
    run_counts_per_trainer = []

    # Loop through the queryset and extract the results
    for row in runs_per_date_statistics:
        dates.append(row['date'].strftime('%Y-%m-%d'))
        run_counts_per_date.append(row['run_count'])

    for row in runs_per_trainer_statistics:
        trainer_ids.append(row['trainer_id'])
        run_counts_per_trainer.append(row['run_count'])

        runs_per_date_statistics = Run.objects.values('date').annotate(run_count=Count('id'))
        run_status_statistics = Run.objects.values('status').annotate(run_count=Count('id'))

        dates = []
        run_counts_per_date = []

        run_statuses = []
        run_counts_per_status = []

        for row in runs_per_date_statistics:
            dates.append(row['date'].strftime('%Y-%m-%d'))
            run_counts_per_date.append(row['run_count'])

        for row in run_status_statistics:
            run_statuses.append(row['status'])
            run_counts_per_status.append(row['run_count'])

    # Pass the user types and counts to the context dictionary
    context = {
        'user_types': user_types,
        'user_type_counts': user_type_counts,
        'user_dates': user_dates,
        'user_date_counts': user_date_counts,
        'dates': dates,
        'run_counts_per_date': run_counts_per_date,
        'trainer_ids': trainer_ids,
        'run_counts_per_trainer': run_counts_per_trainer,
        'run_statuses': run_statuses,
        'run_counts_per_status': run_counts_per_status,
    }

    print(context)
    # Render the template with the context dictionary
    return render(request, 'Admin/adminHome.html', context)

@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def train_model(request, experiment_id):
    return render(request, "train_model.html", {"experiment_id": experiment_id})


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def trainList(request):
    runs = Run.objects.all()
    trainImages = MultipleImage.objects.filter(purpose="train")

    content = {
        "runs": runs,
        "trainImages": trainImages
    }
    return render(request, "Admin/trainList.html", content)


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def deleteRun(request, run_id):
    try:
        run = Run.objects.get(id=run_id)
        run.delete()

        messages.success(request, "Successfully deleted run")
        return HttpResponseRedirect(reverse("trainList"))
    except:
        messages.error(request, "Failed to delete run")
        return HttpResponseRedirect(reverse("trainList"))


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def train_results(request, run_id):
    run = Run.objects.get(id=run_id)

    context = {
        'run': run,
        'average_train_loss': list(run.average_loss_round.all().values()),
        'validation_data': run.validation_round.all(),
        'checkpoints': run.checkpoint.all()
    }
    return render(request, "Admin/trainResults.html", context)


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def updateRunProcess(request, run_id):
    run = Run.objects.get(id=run_id)
    checkpoints = Checkpoint.objects.filter(run=run)
    reportImages = MultipleImage.objects.filter(purpose="report")
    testImages = MultipleImage.objects.filter(purpose="test")
    validationRunImages = Run.objects.get(id=run_id).validation_round.all()
    trainImages = []

    for image in validationRunImages:
        trainImages.append({
            "image": image.image,
            "id": image.id,
            "mask": image.pred_mask,
            "purpose": "train"
        })

    content = {
        "run": run,
        "checkpoints": checkpoints,
        "reportImages": reportImages,
        "trainImages": trainImages,
        "testImages": testImages
    }
    return render(request, "Admin/updateModelPage1.html", content)


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def trainSelected(request):
    if request.method == "POST":
        selected_images = request.POST.getlist("selectedImages")

        objs = MultipleImage.objects.filter(id__in=selected_images)
        try:
            for obj in objs:
                shutil.copyfile(
                    os.path.join(settings.MEDIA_ROOT, obj.images.name),
                    (
                        os.path.join(
                            settings.MEDIA_ROOT + "/image/run/",
                            str(obj.id) + ".jpeg",
                        )
                    ),
                )
                shutil.copyfile(
                    os.path.join(settings.MEDIA_ROOT, obj.masks.name),
                    (
                        os.path.join(
                            settings.MEDIA_ROOT + "/mask/run/",
                            str(obj.id) + "_Segmentation.png",
                        )
                    ),
                )

            training(request=request)
        except Exception as e:
            print(f"Error for object : {e}")

        return HttpResponseRedirect("trainList")


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def trainEvaluated(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        selected_images_index = request.POST.getlist("selectedImages")
        checkpoint_path = request.POST.get("prediction_checkpoint")

        dir_image = os.path.join(settings.MEDIA_ROOT, "image/run/")
        dir_mask = os.path.join(settings.MEDIA_ROOT, "mask/run/")

        # try:
        for index in selected_images_index:
            image = request.POST.get("image" + index)

            if image.startswith("/media/image/runImage/"):
                image = imageToStr(PIL_Image.open(os.getcwd() + image), 'png')

            mask = request.POST.get("mask" + index)

            insertToFolder(dir_image, dir_mask, image, mask)

        training(model_path=settings.MEDIA_ROOT + "/" + checkpoint_path, request=request)
        # except Exception as e:
        #     print(f"Error for object : {e}")

        return HttpResponseRedirect("trainList")


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def predictMask(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")

    else:
        evaluation = []
        uploadedImages = request.FILES.getlist("uploadedImages")
        checkpoint = request.POST.get("prediction_checkpoint")
        reportImagesId = request.POST.getlist("reportImagesStep2")
        testImagesId = request.POST.getlist("testImagesStep2")
        trainImagesId = request.POST.getlist("trainImagesStep2")

        for file in uploadedImages:
            imagep = PIL_Image.open(file)
            prediction = predict(imagep, model_path=f'media/{checkpoint}')
            evaluation.append({"image": imageToStr(imagep), "prediction": imageToStr(prediction)})

        for report_id in reportImagesId:
            image = MultipleImage.objects.get(id=report_id)
            evaluation.append({"image": image.images.url, "prediction": image.masks.url})

        for train_id in trainImagesId:
            image = Validation.objects.get(id=train_id)
            evaluation.append({"image": image.image.url, "prediction": image.pred_mask.url})

        for test_id in testImagesId:
            image = MultipleImage.objects.get(id=test_id)
            evaluation.append({"image": image.images.url, "prediction": image.masks.url})

        context = {
            "evaluation": evaluation,
            "checkpoint": checkpoint
        }

        return JsonResponse(context)


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def update_model(request):
    checkpoint = request.POST.get("checkpoint")
    src_path = os.getcwd() + "/media/" + checkpoint
    dst_path = os.getcwd() + "/base/MODEL.pth"
    shutil.copy(src_path, dst_path)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def correctMasks(request):
    if request.method == "POST":
        train_images = []
        counter = int(request.POST.get('counter'))

        for i in range(1, counter + 1):
            image = request.POST.get("image" + str(i))
            mask = request.POST.get("mask" + str(i))
            x_points = request.POST.get("x" + str(i))
            y_points = request.POST.get("y" + str(i))
            corrected = False

            if x_points is not None and x_points != "":
                mask = createMask(
                    request,
                    image,
                    x_points,
                    y_points,
                )
                corrected = True

            train_images.append({
                "image": image,
                "mask": mask,
                "x_points": x_points,
                "y_points": y_points,
                "corrected": corrected
            })

        content = {
            "train_images": train_images,
        }
        return JsonResponse(content)


def modifyDoctors(request):
    users = CustomUser.objects.all()

    content = {
        "users": users,
    }

    return render(request, "Admin/modifyDoctors.html", content)


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def modifyImages(request):
    images = MultipleImage.objects.all().order_by("date")

    content = {
        "trainCount": MultipleImage.objects.filter(purpose="train").count(),
        "testCount": MultipleImage.objects.filter(purpose="test").count(),
        "reportCount": MultipleImage.objects.filter(purpose="report").count(),
        "evaluateCount": MultipleImage.objects.filter(purpose="evaluate").count(),
        "images": images,
    }
    return render(request, "Admin/modifyImages.html", content)


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def deleteImage(request, image_id):
    try:
        image = MultipleImage.objects.get(id=image_id)
        image.delete()
        os.remove(os.path.join(settings.MEDIA_ROOT, image.images.name))
        os.remove(os.path.join(settings.MEDIA_ROOT, image.masks.name))

        messages.success(request, "Successfully deleted image")
        return HttpResponseRedirect(reverse("modifyImages"))
    except:
        messages.error(request, "Failed to delete image")
        return HttpResponseRedirect(reverse("modifyImages"))


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def editUser(request, user_id):
    user = CustomUser.objects.get(id=user_id)

    content = {
        "user": user
    }

    return render(request, "Admin/editUser.html", content)


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def editUserSave(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        user_id = request.POST.get("user_id")
        password = request.POST.get("password")
        username = request.POST.get("username")
        email = request.POST.get("email")
        is_active = request.POST.get("is_active")

        try:
            user = CustomUser.objects.get(id=user_id)
            user.username = username
            user.email = email
            user.is_active = is_active is not None
            user.password = make_password(password)
            user.save()

            messages.success(request, "Successfully Edited user")
            return HttpResponseRedirect(
                reverse("editUser", kwargs={"user_id": user_id})
            )
        except:
            messages.error(request, "Failed to Edit user")
            return HttpResponseRedirect(
                reverse("editUser", kwargs={"user_id": user_id})
            )


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def deleteDoctor(request, doctor_id):
    try:
        user = CustomUser.objects.get(id=doctor_id)
        user.delete()

        messages.success(request, "Successfully deleted doctor")
        return HttpResponseRedirect(reverse("modifyDoctors"))
    except:
        messages.error(request, "Failed to delete doctor")
        return HttpResponseRedirect(reverse("modifyDoctors"))


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def addImage(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")
    else:
        purpose = request.POST.get("purpose")
        imageFiles = request.FILES.getlist("imageFiles")
        maskFiles = request.FILES.getlist("maskFiles")

        if len(imageFiles) != len(maskFiles):
            messages.error(request, "Failed to Add images.List index out of range")
            return HttpResponseRedirect(reverse("modifyImages"))
        try:
            for (image, mask) in zip(imageFiles, maskFiles):
                MultipleImage.objects.create(
                    images=convert_image(image, "JPEG"),
                    masks=convert_image(mask, "PNG"),
                    purpose=purpose,
                    postedBy=request.user,
                )

            messages.success(request, "Successfully Added images")
            return HttpResponseRedirect(reverse("modifyImages"))
        except Exception as e:
            messages.error(request, e)
            return HttpResponseRedirect(reverse("modifyImages"))
