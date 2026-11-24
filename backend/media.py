"""Validate/re-encode images; keep media out of HTML/SVG and cap decoded dimensions."""
import base64
import io
import warnings
from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException
MAX_BYTES = 5 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 16_000_000

def validated_image(raw, content_type=None):
    if not raw or len(raw) > MAX_BYTES:
        raise HTTPException(422, 'Image must be non-empty and at most 5 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                if image.format not in ('PNG', 'JPEG', 'WEBP'):
                    raise ValueError()
                image.load()
                image = image.convert('RGB')
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=85)
                data = output.getvalue()
                if len(data) > MAX_BYTES:
                    raise ValueError()
    except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(422, 'A valid JPEG, PNG or WebP image within 16 megapixels is required.') from None
    return 'data:image/jpeg;base64,' + base64.b64encode(data).decode()

def validate_image_reference(value):
    if value is None or value == '':
        return value
    if not value.startswith('data:image/') or len(value) > MAX_BYTES * 2:
        raise ValueError('Use a validated image upload (maximum 5 MB).')
    try:
        header, encoded = value.split(',', 1)
        if ';base64' not in header:
            raise ValueError()
        return validated_image(base64.b64decode(encoded, validate=True))
    except (ValueError, HTTPException) as error:
        raise ValueError('Invalid or oversized image data.') from error
