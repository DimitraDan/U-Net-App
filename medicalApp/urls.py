"""medicalApp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from base import views, doctorViews, adminViews
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import View
from django.http import HttpResponse

class ImageServeView(View):
    def get(self, request, *args, **kwargs):
        image_path = kwargs.get('image_path')
        with open(image_path, 'rb') as f:
            image_data = f.read()
        return HttpResponse(image_data, content_type='image/png')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.showLoginPage, name="showLoginPage"),
    path('doLogin', views.doLogin, name="doLogin"),
    path('logout', views.logout, name="logout"),
    path('sign_up', views.showSignUpPage, name="signUp"),
    path('doSignUp', views.doSignUp, name='doSignUp'),
    path('doctorHome', doctorViews.doctorHome, name="doctorHome"),
    path('adminHome', adminViews.adminHome, name="adminHome"),
    path('modifyImages', adminViews.modifyImages, name="modifyImages"),
    path('predictMask', adminViews.predictMask, name="predictMask"),
    path('modifyDoctors', adminViews.modifyDoctors, name="modifyDoctors"),
    path('add_image', adminViews.addImage, name="add_image"),
    path('Segmentation', doctorViews.segmentation, name="segmentation"),
    path('Patients', doctorViews.patients, name="patients"),
    path('delete_image/<str:image_id>', adminViews.deleteImage, name="delete_image"),
    path('delete_doctor/<str:doctor_id>', adminViews.deleteDoctor, name="delete_doctor"),
    path('editDoctor/<str:user_id>', adminViews.editUser, name="editUser"),
    path('edit_doctor_save', adminViews.editUserSave, name="edit_doctor_save"),
    path('trainList', adminViews.trainList, name='trainList'),
    path('train_selected', adminViews.trainSelected, name='train_selected'),
    path('train_evaluated', adminViews.trainEvaluated, name='train_evaluated'),
    path('train_results/<str:run_id>/', adminViews.train_results, name='train_results'),
    path('image/<path:image_path>/', ImageServeView.as_view(), name='image_serve'),
    path('correctMasks', adminViews.correctMasks, name='correctMasks'),
    path('update_model', adminViews.update_model, name='update_model'),
    path('updateRunProcess/<int:run_id>/', adminViews.updateRunProcess, name='updateRunProcess'),
    path('runs/delete/<int:run_id>/', adminViews.deleteRun, name='delete_run'),
    path('download_csv_runs/', adminViews.download_csv, name='download_csv'),
    path('download_csv_user/', adminViews.download_csv_user, name='download_csv_user'),
    path('download_csv_train_results/<int:run_id>/', adminViews.download_csv_train_results, name='download_csv_train_results'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
