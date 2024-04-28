import base64
import io
from PIL import Image


def base64_to_image(base64_string: str):
    image_data = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(image_data))
    return image
