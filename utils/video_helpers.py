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
    video = VideoFileClip(video_path).set_fps(25).resize(res)

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

def add_background_music(video, music_file, volume=0.4):
    background_music = AudioFileClip(music_file).volumex(volume)
    video_audio = video.audio
    final_audio = CompositeAudioClip([video_audio, background_music.set_duration(video.duration)])
    video = video.set_audio(final_audio)
    return video
