# U-Net

This Django project is designed to automate the segmentation of images.

## Getting Started

Follow these instructions to set up the Django project locally.

### Prerequisites

Ensure you have the following prerequisites installed:

- Python 
- Pip
  
Install project dependencies and set up the database:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

 Run server
```bash
python manage.py runserver
```

The application will be accessible at http://localhost:8000/.

## Download Pre-trained Model State
Before running the application, download the pre-trained model state (`MODEL.pth`) from [releases page](https://github.com/milesial/Pytorch-UNet/releases/tag/v3.0) of the Pytorch-UNet repository. Place the downloaded file in the project's base folder.
