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
import uuid
import os
from urllib.parse import quote, urlparse

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
        slide_clip = clip2.set_start(clip1.duration - duration).set_position(slide_position)
        return CompositeVideoClip([clip1, slide_clip])

    @staticmethod
    def wipe(clip1, clip2, duration):
        def wipe_position(t):
            if t < duration:
                return (clip2.w - (clip2.w * t / duration), "center")
            else:
                return ("center", "center")
        wipe_clip = clip2.set_start(clip1.duration - duration).set_position(wipe_position)
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


def create_video_clip(video_path, audio_path, res):
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    video = VideoFileClip(video_path).set_fps(24).resize(res)

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
    photo = ImageClip(photo_path).set_duration(duration).resize(res)
    photo = photo.set_audio(audio)
    return photo


def add_text_overlay(clip, text):
    text_clip = TextClip(text["content"], fontsize=70, color="white", font="Amiri-Bold")
    text_clip = text_clip.set_position(text["position"]).set_duration(clip.duration)

    return CompositeVideoClip([clip, text_clip])


def add_subtitle(text, start_time, duration):
    text_clip = TextClip(text.strip(), fontsize=24, color="white", bg_color="black")
    text_clip = text_clip.set_start(start_time).set_duration(duration)
    text_clip = text_clip.set_position(('center', 'bottom'))

    return text_clip


def get_subtitle_clips(response, seconds_per_segment: int = 5):
    subtitle_clips = []
    segment_start_time = 0.0
    segment_text = ""

    for result in response.results:
        for word_info in result.alternatives[0].words:
            word_start_time = word_info.start_time.total_seconds()
            text = word_info.word

            if word_start_time - segment_start_time >= seconds_per_segment:
                subtitle_clip = add_subtitle(segment_text, segment_start_time, seconds_per_segment)
                subtitle_clips.append(subtitle_clip)

                segment_start_time = word_start_time
                segment_text = text + " "
            else:
                segment_text += text + " "

    # Add the last segment
    if segment_text:
        final_duration = word_start_time - segment_start_time
        subtitle_clip = add_subtitle(segment_text, segment_start_time, final_duration)
        subtitle_clips.append(subtitle_clip)

    return subtitle_clips


def add_background_music(video, music_file, volume=0.2):
    background_music = AudioFileClip(music_file).volumex(volume)
    video_audio = video.audio
    final_audio = CompositeAudioClip([video_audio, background_music.set_duration(video.duration)])
    video = video.set_audio(final_audio)
    return video


def edit_video(final_video_url: str, start_time, end_time, scene, DatabaseOperationsService, content_creator):
    unique_folder_name = str(uuid.uuid4())
    edit_video_path = f"..\\temp\\video_editing\\{unique_folder_name}"
    if not os.path.exists(edit_video_path):
        os.makedirs(edit_video_path)
    
    os.makedirs(edit_video_path+"\\audio", exist_ok=True)
    os.makedirs(edit_video_path+"\\media", exist_ok=True)

    #content_creator = ContentCreator()
    file_path_final_video = content_creator.download_stock(media_url=final_video_url, user_media_path=edit_video_path)
    
    
    video = VideoFileClip(file_path_final_video)
    video_before_cut = video.subclip(0, start_time)
    video_after_cut = video.subclip(end_time, video.duration)
    
    # generate tts with script and save it to a file
    content_creator.text_to_speech(text=scene["script"], out_name="new_script_audio", user_media_path=edit_video_path)
    # get the new media (image or video clip) and save to file if necessary
    content_creator.download_stock(media_url=scene["media_url"], user_media_path=edit_video_path)
    
    
    # make a new video with that new media with the tts audio over it
    parsed_url = urlparse(scene["media_url"])
    filename = os.path.basename(parsed_url.path)
    
    audio_path = f"{edit_video_path}\\audio\\new_script_audio.wav"
    media_path = f"{edit_video_path}\\media\\{filename}"
    
    
    # Load the audio file
    audio = AudioFileClip(audio_path)
    final_clip = None
    if is_image_file(media_path):
        # image_clip = ImageClip(media_path, duration=audio.duration)
        # final_clip = image_clip.set_audio(audio)
        final_clip = create_photo_clip(photo_path=media_path, audio_path=audio_path, res=(1280, 720))
        
    elif is_video_file(media_path):
        # new_media_video = VideoFileClip(media_path)
        # audio = audio.subclip(0, min(new_media_video.duration, audio.duration))
        # final_clip = new_media_video.set_audio(audio)
        final_clip = create_video_clip(video_path=media_path, audio_path=audio_path, res=(1280, 720))
    
    
    # concatenate the video_before_cut, new video, and video_after_cut
    final_video = concatenate_videoclips([video_before_cut, final_clip, video_after_cut])
    final_video.write_videofile(f"{edit_video_path}\\final_edited_video.mp4", codec="libx264", audio_codec="aac")
    
    # add the new video to google bucket and return the signed url
    DatabaseOperationsService.upload_file_by_path(file_path=f"{edit_video_path}\\final_edited_video.mp4", file_name=unique_folder_name)
    edited_final_video_url = DatabaseOperationsService.get_file_link(key=unique_folder_name)
    ## one issue is that the music will not be present in the new video scene
    return edited_final_video_url;






def is_image_file(filename):
        return filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".heic"))

def is_video_file(filename):
        return filename.lower().endswith((".mp4", ".mov", ".mpeg", ".avi"))