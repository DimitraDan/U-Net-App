import csv
import json
from django.conf import settings

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse

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


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def adminHome(request):
    # Execute the SQL query and get the results as a queryset
    user_type_counts_statistics = CustomUser.objects.raw(
        'SELECT id, user_type, COUNT(id) as user_type_count FROM base_customuser GROUP BY user_type')
    user_date_joined_counts_statistics = CustomUser.objects.raw(
        'SELECT id, CAST(date_joined AS TEXT) AS date_joined_formatted, COUNT(id) AS user_date_count FROM base_customuser GROUP BY date_joined_formatted')

    # Initialize empty lists to store the user types and counts
    user_types = []
    user_type_counts = []

    user_dates = []
    user_date_counts = []

    # Loop through the queryset and extract the user types and counts
    for row in user_type_counts_statistics:
        user_types.append(row.user_type)
        user_type_counts.append(row.user_type_count)

    for row in user_date_joined_counts_statistics:
        user_dates.append(row.date_joined)
        user_date_counts.append(row.user_date_count)

    # Pass the user types and counts to the context dictionary
    context = {
        'user_types': user_types,
        'user_type_counts': user_type_counts,
        'user_dates': user_dates,
        'user_date_counts': user_date_counts
    }

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
    validationImages = MultipleImage.objects.filter(purpose="test")

    context = {
        'run': run,
        'train_loss_data': run.train_loss.all(),
        'train_loss_chart': list(run.train_loss.all().values()),
        'validation_data': run.validation_loss.all(),
        'validation_chart': list(run.validation_loss.all().values()),
        'checkpoints': run.checkpoint.all()
    }
    return render(request, "Admin/trainResults.html", context)


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def updateRunProcess(request, run_id):
    run = Run.objects.get(id=run_id)
    checkpoints = Checkpoint.objects.filter(run=run)
    testImages = MultipleImage.objects.filter(purpose="test")

    content = {
        "run": run,
        "checkpoints": checkpoints,
        "testImages": testImages
    }
    return render(request, "Admin/evaluateModel.html", content)


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def trainSelected(request):
    if request.method == "POST":
        selected_images = request.POST.getlist("selectedImages")

        objs = MultipleImage.objects.filter(id__in=selected_images)

        dir_image = "media/selected/image/train/"
        dir_mask = "media/selected/mask/train/"

        try:
            for obj in objs:
                shutil.copyfile(
                    os.path.join(settings.MEDIA_ROOT, obj.images.name),
                    (
                        os.path.join(
                            settings.MEDIA_ROOT + "/selected/image/train/",
                            str(obj.id) + ".jpeg",
                        )
                    ),
                )
                shutil.copyfile(
                    os.path.join(settings.MEDIA_ROOT, obj.masks.name),
                    (
                        os.path.join(
                            settings.MEDIA_ROOT + "/selected/mask/train/",
                            str(obj.id) + "_Segmentation.png",
                        )
                    ),
                )

            training(request=request)
        except Exception as e:
            print(f"Error for object : {e}")

        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def trainEvaluated(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        selected = request.POST.getlist("selection")
        checkpoint_path = request.POST.get("checkpoint")
        dir_image = os.path.join(settings.MEDIA_ROOT, "selected/image/train/")
        dir_mask = os.path.join(settings.MEDIA_ROOT, "selected/mask/train/")

        # try:
        for obj in selected:
            obj = obj.replace("'", '"')
            json_obj = json.loads(obj)
            insertToFolder(dir_image, dir_mask, json_obj["image"], json_obj["prediction"])

        training(model_path=checkpoint_path, request=request)
        # except Exception as e:
        #     print(f"Error for object : {e}")

        return HttpResponseRedirect("trainModel")


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def predictMask(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")

    else:
        evaluation = []
        imageFiles = request.FILES.getlist("images")
        checkpoint = request.POST.get("prediction_checkpoint")
        selected_images = request.POST.getlist("selectedImages")

        for file in imageFiles:
            imagep = PIL_Image.open(file)
            prediction = predict(imagep, model_path=f'media/{checkpoint}')
            evaluation.append({"image": imageToStr(imagep), "prediction": imageToStr(prediction)})

        for image in selected_images:
            prediction = predict(image, model_path=f'media/{checkpoint}')
            evaluation.append({"image": imageToStr(image), "prediction": imageToStr(prediction)})

        context = {
            "evaluation": evaluation,
            "checkpoint": checkpoint
        }

        return JsonResponse(context)



@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def update_model(request):
    checkpoint = request.POST.get("checkpoint")
    src_path = os.getcwd() + "/" + checkpoint
    dst_path = os.getcwd() + "/base/MODEL.pth"
    shutil.copy(src_path, dst_path)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def report(request):
    if request.method == "POST":
        results = []
        updated_results = []
        counter = int(request.POST.get('counter'))
        if request.POST.get("counter_updated") is None:
            updated_counter = 0
        else:
            updated_counter = int(request.POST.get("counter_updated"))

        for i in range(1, updated_counter + 1):
            updated_results.append({"image": request.POST.get("updated_prediction_img" + str(i)),
                                    "prediction": request.POST.get("updated_prediction_mask" + str(i))})

        for i in range(1, counter + 1):
            save = request.POST.get(str(i))
            if save is None:
                save = "NO"
            results.append(
                {
                    "image": request.POST.get("image" + str(i)),
                    "prediction": request.POST.get("prediction" + str(i)),
                    "x_points": request.POST.get("x_points" + str(i)),
                    "y_points": request.POST.get("y_points" + str(i)),
                    "save": save,
                }
            )

        for result in results:
            if (
                    result["x_points"] is not None
                    and result["y_points"] is not None
                    and result["x_points"] != ""
                    and result["y_points"] != ""
            ):
                mask = createMask(
                    request,
                    result["image"],
                    result["x_points"],
                    result["y_points"],
                    result["save"],
                )
                updated_results.append({"image": result["image"], "prediction": mask})
                results.remove(result)

        if "train" in request.POST:
            try:
                deleteFiles(os.path.join(settings.MEDIA_ROOT, "selected/image/train"))
                deleteFiles(os.path.join(settings.MEDIA_ROOT, "selected/mask/train"))
            except:
                pass

            reported = request.POST.getlist("reported")
            selected = request.POST.getlist("selected")

            dir_image = "media/selected/image/train/"
            dir_prediction = "media/selected/mask/train/"

            for selection_str in selected:
                fixed_json_str = selection_str.replace("'", '"')
                selection_json = json.loads(fixed_json_str)
                insertToFolder(
                    dir_image,
                    dir_prediction,
                    selection_json["image"],
                    selection_json["prediction"],
                )

            for report in reported:
                fixed_json_str = report.replace("'", '"')
                selection_json = json.loads(fixed_json_str)
                insertToFolder(
                    dir_image,
                    dir_prediction,
                    selection_json["image"],
                    selection_json["mask"],
                )
                updated_results.append(
                    {"image": selection_json["image"], "mask": selection_json["mask"]}
                )

            training(request=request)
            messages.success(request, "Training finished succesfully!")

        content = {
            "updated_size": len(updated_results),
            "updated_evaluation": updated_results,
            "evaluation": results,
            "size": len(results),
        }

    return render(request, "Admin/evaluateModel.html", content)


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
def editDoctor(request, user_id):
    user = CustomUser.objects.get(id=user_id)

    content = {
        "user": user
    }

    return render(request, "Admin/editUser.html", content)


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def editDoctorSave(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        user_id = request.POST.get("user_id")
        password = request.POST.get("password")
        username = request.POST.get("username")
        email = request.POST.get("email")

        try:
            user = CustomUser.objects.get(id=user_id)
            user.username = username
            user.email = email
            user.password = password
            user.save()

            messages.success(request, "Successfully Edited user")
            return HttpResponseRedirect(
                reverse("editDoctor", kwargs={"doctor_id": user_id})
            )
        except:
            messages.error(request, "Failed to Edit user")
            return HttpResponseRedirect(
                reverse("editDoctor", kwargs={"doctor_id": user_id})
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
