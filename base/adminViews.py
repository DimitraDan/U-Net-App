import datetime as dt
import json
from datetime import timedelta
from django.conf import settings

import wandb
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from base.manageFolders import *
from base.manageImages import *
from base.predict import predict
from base.train import training
import math
import pandas as pd

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
def train(request):
    # Log in to WandB
    wandb.login(key="3e1234cfe5ed344ab23cea32ea863b2d5c110f09")

    # Specify the name of your project
    project_name = "U-Net"

    # Initialize the WandB API
    api = wandb.Api()

    # Retrieve a list of all runs in your project
    runs = api.runs(project_name)

    trainImgCount = MultipleImage.objects.filter(purpose="train").count()
    trainImages = MultipleImage.objects.filter(purpose="train")
    reportImgCount = MultipleImage.objects.filter(purpose="report").count()
    reportImages = MultipleImage.objects.filter(purpose="report")

    testImgCount = MultipleImage.objects.filter(purpose="test").count()
    testImages = MultipleImage.objects.filter(purpose="test")
    content = {
        "testImgCount": testImgCount,
        "testImages": testImages,
        "runCount": len(runs),
        "runs": runs,
        "trainImgCount": trainImgCount,
        "trainImages": trainImages,
        "reportImages": reportImages,
        "reportImgCount": reportImgCount,
    }

    return render(request, "Admin/train.html", content)


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def train_results(request, run_id):
    # Initialize W&B API
    api = wandb.Api()

    # Get the run object using its ID
    run = api.run(f"dimitradan/U-Net/{run_id}")

    history_data = pd.DataFrame(run.history())
    summary_data = run.summary._json_dict

    train_loss_data = []
    validation_data = []

    timestamp = run.created_at
    datetime = dt.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
    datetime = datetime - timedelta(seconds=1)
    formatted_timestamp = datetime.strftime("%Y%m%d_%H%M%S")
    path = find_dir_with_string("wandb", run.id) + "/files/"

    # Get the list of files in the 'checkpoints' directory

    try:
        checkpoints_dir = os.path.join(path, "base/checkpoints")
        checkpoints_files = os.listdir(checkpoints_dir)
    except FileNotFoundError:
        checkpoints_files = []

    for index, row in history_data.iterrows():
        try:
            step = row["_step"]
            epoch = row["epoch"]

            if not math.isnan(row["train_loss"]):
                train_loss = row["train_loss"]
                train_loss_data.append(
                    {"step": step, "epoch": epoch, "train_loss": train_loss}
                )
            else:
                learning_rate = row["learning_rate"]
                validation_Iou = row["validation_Iou"]
                image_path = row["images"]["path"]
                mask_pred_path = row["masks.pred"]["path"]
                mask_true_path = row["masks.true"]["path"]

                validation_data.append(
                    {
                        "step": step,
                        "epoch": epoch,
                        "image_path": path + image_path,
                        "mask_pred_path": path + mask_pred_path,
                        "mask_true_path": path + mask_true_path,
                        "learning_rate": learning_rate,
                        "validation_Iou": validation_Iou,
                    }
                )

        except TypeError:
            continue

    context = {
        "path": path,
        "checkpoints_dir": checkpoints_dir,
        "checkpoints_files": checkpoints_files,
        "run": run,
        "formatted_timestamp": formatted_timestamp,
        "summary_data": summary_data,
        "validation_data": validation_data,
        "train_loss_data": train_loss_data,
    }
    return render(request, "Admin/trainResults.html", context)


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def trainSelected(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        deleteFiles(os.path.join(settings.MEDIA_ROOT, "selected/image/train"))
        deleteFiles(os.path.join(settings.MEDIA_ROOT, "selected/mask/train"))

        selected = request.POST.getlist("selection")
        objs = MultipleImage.objects.filter(images__in=selected)

        dir_image = "media/selected/image/train/"
        dir_mask = "media/selected/mask/train/"

        # try:
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

        training()
        # except Exception as e:
        #     print(f"Error for object : {e}")

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

        training(model_path=checkpoint_path)
        # except Exception as e:
        #     print(f"Error for object : {e}")

        return HttpResponseRedirect("trainModel")


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def evaluateModel(request):
    return render(request, "Admin/evaluateModel.html")


@login_required(login_url="/login/")
@user_passes_test(lambda user: user.user_type == "1")
def evaluation(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")

    else:
        evaluation = []
        imageFiles = request.FILES.getlist("images")
        checkpoint = request.POST.get("predict_checkpoint")
        for file in imageFiles:
            imagep = PIL_Image.open(file)
            prediction = predict(imagep, model_path=checkpoint)
            evaluation.append(
                {"image": imageToStr(imagep), "prediction": imageToStr(prediction)}
            )
        context = {"evaluation": evaluation, "size": len(evaluation), "checkpoint": checkpoint}

        return render(request, "Admin/evaluateModel.html", context)


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

            training()

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
def editDoctor(request, doctor_id):
    doctor = CustomUser.objects.get(id=doctor_id)
    return render(request, "Admin/editDoctor.html", {"doctor": doctor, "id": doctor_id})


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