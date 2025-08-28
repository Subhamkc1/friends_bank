from io import BytesIO
import qrcode
from django.core.files.base import ContentFile
from django.conf import settings

def generate_qr_image(path_suffix: str):
    url = f"{settings.QR_BASE_URL}{path_suffix}"
    img = qrcode.make(url)
    bio = BytesIO()
    img.save(bio, format='PNG')
    return ContentFile(bio.getvalue(), name='qr.png')
