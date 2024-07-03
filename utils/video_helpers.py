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
import textwrap


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
    text_clip = TextClip(text["content"], fontsize=70, color="white", font=text['font'])
    text_clip = text_clip.set_position('center').set_duration(clip.duration)

    return CompositeVideoClip([clip, text_clip])


def add_subtitle(text, start_time, duration):
    wrap_txt = textwrap.fill(text.strip(), width=75)
    text_clip = TextClip(wrap_txt, fontsize=35, color="white", bg_color="black")
    text_clip = text_clip.set_start(start_time).set_duration(duration)
    text_clip = text_clip.set_position(('center', 'bottom'))

    return text_clip


def get_subtitle_clips(response, seconds_per_segment: int = 3):
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
