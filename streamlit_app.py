import streamlit as st
import boto3
from yt_dlp import YoutubeDL
import random
import string
import os
from io import BytesIO

# Initialize S3 client
s3_client = boto3.client('s3')

# S3 bucket name (replace with your bucket name)
BUCKET_NAME = ''

def generate_random_hash(length=10):
    """Generate a random hash for filenames."""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def download_and_upload_to_s3(youtube_url, bucket_name, object_name, progress_bar):
    """Download a video from YouTube and upload it to S3, then delete the local file."""
    try:
        # Create a temporary file path
        temp_file_path = f"{object_name}.mp4"

        ydl_opts = {
            'format': 'best',
            'noplaylist': True,
            'outtmpl': temp_file_path,  # Download the video to a temp file
            'progress_hooks': [lambda d: update_download_progress(d, progress_bar)]
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            total_size = info_dict.get('filesize') or info_dict.get('filesize_approx')
            ydl.download([youtube_url])

        # Upload the file to S3
        with open(temp_file_path, "rb") as file_data:
            s3_client.upload_fileobj(
                file_data,
                bucket_name,
                object_name
            )
            st.success(f"Uploaded successfully! Public URL: https://{bucket_name}.s3.amazonaws.com/{object_name}")

        # Delete the local file after uploading
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            st.info(f"Local file {temp_file_path} has been deleted.")
        else:
            st.warning(f"File {temp_file_path} does not exist.")
                
    except Exception as e:
        st.error(f"Failed to download, upload, or delete the video: {e}")

def update_download_progress(d, progress_bar):
    if d['status'] == 'downloading':
        total_size = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)
        if total_size is not None:
            progress = int(downloaded / total_size * 100)
            progress_bar.progress(progress)

def upload_email_to_s3(email, bucket_name, object_name):
    """Upload the email content as a .txt file to S3."""
    try:
        email_content = BytesIO(email.encode('utf-8'))
        s3_client.upload_fileobj(
            email_content,
            bucket_name,
            object_name
        )
        st.success(f"Email uploaded successfully as {object_name}")
    except Exception as e:
        st.error(f"Failed to upload email: {e}")

# Streamlit UI
st.title("CricCenter Youtube Upload")

# Get user email
email = st.text_input("Enter your email address")

youtube_url = st.text_input("Enter YouTube video URL")

if youtube_url:
    if st.button("Download and Upload to S3"):
        if email:
            download_progress_bar = st.progress(0)
            file_hash = generate_random_hash()
            base_filename = f"{file_hash}"

            video_filename = f"{base_filename}.mp4"
            email_filename = f"{base_filename}.txt"

            # Download video, upload to S3, and delete the local file
            download_and_upload_to_s3(youtube_url, BUCKET_NAME, video_filename, download_progress_bar)

            # Upload email to S3 with the same base filename
            upload_email_to_s3(email, BUCKET_NAME, email_filename)
        else:
            st.error("Please enter an email address.")
