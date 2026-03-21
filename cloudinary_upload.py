import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_image(file_path, folder="zeintimes"):
    try:
        result = cloudinary.uploader.upload(
            file_path,
            folder=folder,
            resource_type="image"
        )
        return result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return None

def upload_file_object(file_obj, folder="zeintimes"):
    try:
        result = cloudinary.uploader.upload(
            file_obj,
            folder=folder,
            resource_type="image"
        )
        return result.get("secure_url")
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return None