import streamlit as st
import boto3
from yt_dlp import YoutubeDL
import random
import string
from io import BytesIO

# Initialize S3 client
s3_client = boto3.client('s3')

# S3 bucket name (replace with your bucket name)
BUCKET_NAME = 'highlightgenerationbucket'

def generate_random_hash(length=10):
    """Generate a random hash for filenames."""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def download_and_upload_to_s3(youtube_url, bucket_name, object_name, progress_bar):
    """Download a video from YouTube and stream it directly to S3."""
    def upload_progress_callback(bytes_amount):
        upload_progress_callback.seen_so_far += bytes_amount
        progress = int(upload_progress_callback.seen_so_far / total_size * 100)
        progress_bar.progress(progress)

    upload_progress_callback.seen_so_far = 0

    try:
        ydl_opts = {
            'format': 'best',
            'noplaylist': True,
            'progress_hooks': [lambda d: update_download_progress(d, progress_bar)]
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            total_size = info_dict.get('filesize') or info_dict.get('filesize_approx')
            video_title = info_dict.get('title', None)

            # Download the video data directly to a stream buffer
            stream_buffer = BytesIO()
            ydl.download([youtube_url])
            stream_buffer.seek(0)

            # Upload directly to S3 from the stream buffer
            s3_client.upload_fileobj(
                stream_buffer,
                bucket_name,
                object_name,
                Callback=upload_progress_callback
            )
            st.success(f"Uploaded successfully! Public URL: https://{bucket_name}.s3.amazonaws.com/{object_name}")
                
    except Exception as e:
        st.error(f"Failed to download and upload video: {e}")

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
st.title("CricCenter Highlight Generation Channel")

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

            # Download video and upload to S3
            download_and_upload_to_s3(youtube_url, BUCKET_NAME, video_filename, download_progress_bar)

            # Upload email to S3 with the same base filename
            upload_email_to_s3(email, BUCKET_NAME, email_filename)
        else:
            st.error("Please enter an email address.")
