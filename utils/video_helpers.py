from moviepy.editor import (
    TextClip,
    ImageClip,
    VideoFileClip,
    CompositeVideoClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips,
    vfx,
)
from moviepy.video.fx.resize import resize
import google.cloud.texttospeech as tts
from google.cloud import speech_v1p1beta1 as speech
from urllib.parse import urlparse
import requests
import textwrap
import io
import os


class VideoTransitionHelper:
    @staticmethod
    def crossfade(clip1, clip2, duration):
        clip1 = clip1.crossfadeout(duration)
        clip2 = clip2.crossfadein(duration).set_start(clip1.duration - duration)
        return CompositeVideoClip([clip1, clip2])

    @staticmethod
    def fade_to_black(clip1, clip2, duration):
        clip1 = clip1.fx(vfx.fadeout, duration)
        clip2 = clip2.set_start(clip1.duration)
        return CompositeVideoClip([clip1, clip2])

    @staticmethod
    def fade_from_black(clip1, clip2, duration):
        clip2 = clip2.fx(vfx.fadein, duration).set_start(clip1.duration)
        return CompositeVideoClip([clip1, clip2])

    @staticmethod
    def slide(clip1, clip2, duration):
        def slide_position(t):
            if t < duration:
                return ("center", clip2.h - (clip2.h * t / duration))
            else:
                return ("center", "top")

        slide_clip = clip2.set_start(clip1.duration - duration).set_position(
            slide_position
        )
        return CompositeVideoClip([clip1, slide_clip])

    @staticmethod
    def wipe(clip1, clip2, duration):
        def wipe_position(t):
            if t < duration:
                return (clip2.w - (clip2.w * t / duration), "center")
            else:
                return ("center", "center")

        wipe_clip = clip2.set_start(clip1.duration - duration).set_position(
            wipe_position
        )
        return CompositeVideoClip([clip1, wipe_clip])

    @staticmethod
    def apply_transition(clip1, clip2, transition_type, duration=1):
        if transition_type == "crossfade":
            return VideoTransitionHelper.crossfade(clip1, clip2, duration)
        elif transition_type == "fade-to-black":
            return VideoTransitionHelper.fade_to_black(clip1, clip2, duration)
        elif transition_type == "fade-from-black":
            return VideoTransitionHelper.fade_from_black(clip1, clip2, duration)
        elif transition_type == "slide":
            return VideoTransitionHelper.slide(clip1, clip2, duration)
        elif transition_type == "wipe":
            return VideoTransitionHelper.wipe(clip1, clip2, duration)
        else:
            return concatenate_videoclips([clip1, clip2])


def create_video_clip(video_path, audio_path, res, fps):
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    video = VideoFileClip(video_path).set_fps(fps)
    video = resize(video, width=res[0], height=res[1])

    if video.duration > duration:
        video = video.subclip(0, duration)
    elif video.duration < duration:
        repeats = int(duration // video.duration) + 1
        video = concatenate_videoclips([video] * repeats).subclip(0, duration)

    video = video.set_audio(audio)

    return video


def create_photo_clip(photo_path, audio_path, res):
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    photo = ImageClip(photo_path).set_duration(duration)
    photo = resize(photo, width=res[0], height=res[1])

    photo = photo.set_audio(audio)
    return photo


def add_text_overlay(clip, text):
    font_path = os.path.join("fonts", text["font"] + ".TTF")
    text_clip = (
        TextClip(
            text["content"],
            fontsize=100,
            color="white",
            font=font_path,
            stroke_color="black",
            stroke_width=2,
        )
        .set_opacity(0.8)
        .set_position("center")
        .set_duration(clip.duration)
    )

    return CompositeVideoClip([clip, text_clip])


def add_subtitle(text, start_time, duration):
    wrap_txt = textwrap.fill(text.strip().lower(), 70)
    text_clip = (
        TextClip(
            wrap_txt,
            fontsize=35,
            color="white",
            bg_color="black",
            font=os.path.join("fonts", "trebuchet.TTF"),
        )
        .set_opacity(0.6)
        .set_start(start_time)
        .set_duration(duration)
        .set_position(("center", "bottom"))
    )

    return text_clip


def get_subtitle_clips(transcript, seconds_per_segment: int = 3):
    subtitle_clips = []
    segment_start_time = 0.0
    segment_text = ""

    for result in transcript:
        for word_info in result.alternatives[0].words:
            word_start_time = word_info.start_time.total_seconds()
            text = word_info.word

            if word_start_time - segment_start_time >= seconds_per_segment:
                subtitle_clip = add_subtitle(
                    segment_text, segment_start_time, seconds_per_segment
                )
                subtitle_clips.append(subtitle_clip)

                segment_start_time = word_start_time
                segment_text = text + " "
            else:
                segment_text += text + " "

    # Add the last segment
    if segment_text:
        final_duration = word_start_time - segment_start_time
        subtitle_clip = add_subtitle(
            segment_text, segment_start_time, final_duration
        )
        subtitle_clips.append(subtitle_clip)

    return subtitle_clips


def add_background_music(video, music_file, volume=0.4):
    background_music = AudioFileClip(music_file).volumex(volume)
    video_audio = video.audio
    final_audio = CompositeAudioClip(
        [video_audio, background_music.set_duration(video.duration)]
    )
    video = video.set_audio(final_audio)
    return video


def download_media(media_url, user_media_path: str):
        response = requests.get(media_url)
        response.raise_for_status()

        parsed_url = urlparse(media_url)
        filename = os.path.basename(parsed_url.path)
        file_path = os.path.join(user_media_path, "media", filename)

        with open(file_path, "wb") as file:
            file.write(response.content)

        return file_path

def text_to_speech(text, out_name, user_media_path: str):
    text_input = tts.SynthesisInput(text=text)
    voice_params = tts.VoiceSelectionParams(
        language_code="en-US", name="en-US-Studio-O"
    )
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)

    client = tts.TextToSpeechClient(
        client_options={"api_key": os.getenv("SPEECH_API_KEY")}
    )
    response = client.synthesize_speech(
        input=text_input,
        voice=voice_params,
        audio_config=audio_config,
    )

    file_path = os.path.join(user_media_path, "audio", f"{out_name}.wav")
    with open(file_path, "wb") as out:
        out.write(response.audio_content)

    return file_path

def speech_to_text(audio_path: str, sample_rate):
    client = speech.SpeechClient(
        client_options={"api_key": os.getenv("SPEECH_API_KEY")}
    )

    with io.open(audio_path, "rb") as audio_file:
        content = audio_file.read()

    # Split the content into chunks
    chunk_size = 10 * 1024 * 1024 - 1000  # Slightly less than 10 MB
    chunks = [
        content[i : i + chunk_size] for i in range(0, len(content), chunk_size)
    ]

    all_results = []

    for chunk in chunks:
        audio = speech.RecognitionAudio(content=chunk)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code="en-US",
            audio_channel_count=2,
            enable_word_time_offsets=True,
        )

        response = client.recognize(config=config, audio=audio)
        all_results.extend(response.results)

    return all_results
