from pytubefix import YouTube
import subprocess
import os
import ssl

# Disable SSL verification (use for debugging purposes only)
ssl._create_default_https_context = ssl._create_unverified_context


def check_ffmpeg():
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False
    return True


def install_ffmpeg(log_callback):
    log_callback("FFmpeg not found. Installing...")
    command = 'Start-Process powershell -ArgumentList \'-NoExit -Command "winget install \\"FFmpeg (Essentials Build)\\""\''
    subprocess.run(["powershell", "-Command", command], capture_output=True, text=True)
    log_callback(
        "FFmpeg is being installed. Please restart the computer after installation is completed."
    )


def get_video_qualities(url):
    try:
        yt = YouTube(url)
        video_streams = yt.streams.filter(only_video=True).order_by("resolution").desc()
        progressive_streams = (
            yt.streams.filter(progressive=True).order_by("resolution").desc()
        )

        qualities = {stream.resolution for stream in video_streams}
        qualities.update({stream.resolution for stream in progressive_streams})

        return sorted(qualities, key=lambda x: int(x.rstrip("p")), reverse=True)
    except Exception:
        return []


def download_youtube_video(url, path, quality, log_callback):
    try:
        # Check if ffmpeg is installed, if not, install it
        if not check_ffmpeg():
            install_ffmpeg(log_callback)
            return

        # Create a YouTube object
        yt = YouTube(url)

        # Get the selected video stream based on quality
        video_stream = yt.streams.filter(res=quality, progressive=True).first()

        if not video_stream:
            # If no progressive stream, get only video stream and merge with audio
            video_stream = yt.streams.filter(res=quality, only_video=True).first()
            audio_stream = (
                yt.streams.filter(only_audio=True).order_by("abr").desc().first()
            )

            log_callback(f"Downloading video in {quality}...")
            video_file = video_stream.download(output_path=path, filename="video.mp4")
            log_callback(f"Video downloaded to {video_file}")

            log_callback("Downloading audio...")
            audio_file = audio_stream.download(output_path=path, filename="audio.mp4")
            log_callback(f"Audio downloaded to {audio_file}")

            output_file = os.path.join(path, yt.title + ".mp4")
            log_callback(f"Merging video and audio to {output_file}...")

            command = [
                "ffmpeg",
                "-y",
                "-i",
                video_file,
                "-i",
                audio_file,
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                output_file,
            ]
            subprocess.run(command, check=True)

            os.remove(video_file)
            os.remove(audio_file)

            log_callback(
                f'Video "{yt.title}" has been successfully downloaded in {quality} quality.'
            )
        else:
            log_callback(f"Downloading video in {quality}...")
            video_file = video_stream.download(output_path=path)
            log_callback(f"Video downloaded to {video_file}")

            log_callback(
                f'Video "{yt.title}" has been successfully downloaded in {quality} quality.'
            )
    except subprocess.CalledProcessError as e:
        log_callback(f"An error occurred during ffmpeg processing: {e}")
    except Exception as e:
        log_callback(f"An error occurred: {e}")
