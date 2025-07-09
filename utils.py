import os
import secrets
from PIL import Image # pip install Pillow
from flask import current_app

# Utility for saving user profile pictures
def save_profile_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pictures', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    # FIX: Replace backslashes with forward slashes for web URLs
    return os.path.join('uploads', 'profile_pictures', picture_fn).replace('\\', '/')


# Utility for saving event posters
def save_event_poster(form_poster):
    random_hex = secrets.token_hex(16)
    _, f_ext = os.path.splitext(form_poster.filename)
    poster_fn = random_hex + f_ext
    poster_path = os.path.join(current_app.root_path, 'static', 'uploads', 'event_posters', poster_fn)

    # Resize poster
    output_size = (800, 600)
    i = Image.open(form_poster)
    i.thumbnail(output_size)
    i.save(poster_path)

    # FIX: Replace backslashes with forward slashes for web URLs
    return os.path.join('uploads', 'event_posters', poster_fn).replace('\\', '/')