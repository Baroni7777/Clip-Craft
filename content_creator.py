import os
import shutil
import time
import copy
import json
import uuid
import re
import io
import requests
import logging as log
from urllib.parse import quote, urlparse

from utils.video_helpers import *
from moviepy.config import change_settings
import google.generativeai as genai
import google.cloud.texttospeech as tts
from google.cloud import speech_v1p1beta1 as speech



change_settings(
    {"IMAGEMAGICK_BINARY": os.getenv('IMAGE_MAGICK_PATH')}
)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

PEXEL_HEADERS = {"Authorization": os.getenv("PEXEL_API_KEY")}
VID_PREF = "https://api.pexels.com/videos/search?"
IMG_PREF = "https://api.pexels.com/v1/search?"
SAVED_VIDEO_FORMAT = ".mp4"
SAMPLE_RATE = 44100
SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".webp", ".heic"]
SUPPORTED_VIDEO_FORMATS = [".mp4", ".mov", ".mpeg", ".avi"]


class ContentCreator:

    
    def __init__(self, user_video_options: dict, DATABASE_OPERATIONS_SERVICE: any):
        self.user_video_options = user_video_options;
        self.DATABASE_OPERATIONS_SERVICE = DATABASE_OPERATIONS_SERVICE;
      
        unique_folder_id_param = user_video_options["user_media_path"];
        
        self.title = user_video_options["title"]
        self.desc = user_video_options["description"]
        self.style = user_video_options["template"]
        self.duration = user_video_options["duration"]
        self.orientation = user_video_options["orientation"]

        self.uploaded_files_names = user_video_options["uploaded_files_names"]
        self.user_media_path = f"temp\\{unique_folder_id_param}"
        self.use_stock_media = user_video_options["use_stock_media"]
        self.user_has_provided_media = user_video_options["user_has_provided_media"]

        if self.user_has_provided_media and self.use_stock_media:
            self.SYSTEM_MESSAGE = self.get_system_prompt("media+stock")
        elif self.user_has_provided_media and not self.use_stock_media:
            self.SYSTEM_MESSAGE = self.get_system_prompt("media")
        else:
            self.SYSTEM_MESSAGE = self.get_system_prompt("stock")

        with open("config/config.json", "r") as file:
            config = json.load(file)

        self.SYSTEM_MESSAGE += f'\nHere are some input options you can use:\n {config}'

        self.desc_model = genai.GenerativeModel("gemini-1.5-flash")
        self.video_model = genai.GenerativeModel(
                    "gemini-1.5-flash", system_instruction=self.SYSTEM_MESSAGE
        )


    def upload_img(self, img_path):
        img_file = genai.upload_file(img_path)
        img_file = genai.get_file(img_file.name)
        return img_file


    def upload_vid(self, vid_path):
        vid_file = genai.upload_file(vid_path)
        while vid_file.state.name == "PROCESSING":
            print(".", end="")
            time.sleep(2)
            vid_file = genai.get_file(vid_file.name)

        if vid_file.state.name == "FAILED":
            raise ValueError(vid_file.state.name)
        else:
            return vid_file


    def query_pexel(self, url):
        response = requests.get(url, headers=PEXEL_HEADERS)
        response.raise_for_status()

        return response.json()


    def download_stock(self, media_url, user_media_path: str):
        response = requests.get(media_url)
        response.raise_for_status()

        parsed_url = urlparse(media_url)
        filename = os.path.basename(parsed_url.path)
        file_path = os.path.join(f"{user_media_path}\\media", filename)

        with open(file_path, "wb") as file:
            file.write(response.content)

        return file_path


    def text_to_speech(self, text, out_name,  user_media_path: str):
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

        file_path = os.path.join(f"{user_media_path}\\audio", f"{out_name}.wav")
        with open(file_path, "wb") as out:
            out.write(response.audio_content)
            print(f'Generated speech saved to "{file_path}"')

        return file_path
    
    def speech_to_text(self, audio_path: str):
        client = speech.SpeechClient(client_options={"api_key": os.getenv("SPEECH_API_KEY")})
        with io.open(audio_path, "rb") as audio_file:
            content = audio_file.read()
            audio = speech.RecognitionAudio(content=content)

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code="en-US",
            audio_channel_count=2,
            enable_word_time_offsets=True
        )

        response = client.recognize(config=config, audio=audio)
        return response


    def format_json(self, raw):
        match = re.search(r"```json(.*?)```", raw, re.DOTALL)
        if match:
            text = match.group(1).strip()
            return json.loads(text)
        else:
            try:
                json_obj = json.loads(raw)
                return json_obj
            except json.JSONDecodeError:
                log.error("Could not parse JSON")
        return None


    def get_system_prompt(self, prompt_type: str):
        file_path = f'./constants/profiles/{prompt_type}.txt'
        log.info(f"Reading system prompt from {file_path}")
        with open(file_path, 'r') as file:
            file_content = file.read()
        return file_content


    def start_script_generation(self):
        
        if not self.title or not self.desc or not self.duration or not self.style or not self.orientation:
            return;
        else:
            
            if not os.path.exists(f"{self.user_media_path}\\media"):
                os.makedirs(f"{self.user_media_path}\\media")
                
            if not os.path.exists(f"{self.user_media_path}\\audio"):
                os.makedirs(f"{self.user_media_path}\\audio")

            if self.orientation == "portrait":
                res = (720, 1280)
            else:
                res = (1280, 720)

            
            media_data = []
            log.info("Analysing user media files")
            for file_name in self.uploaded_files_names:
                file_path = os.path.join(f"{self.user_media_path}\\media\\", file_name)
                file_obj = None
                prompt = None

                if any(file_path.endswith(ext) for ext in SUPPORTED_IMAGE_FORMATS):
                    prompt = "write a short one-sentence description for the image"
                    file_obj = self.upload_img(file_path)
                elif any(file_path.endswith(ext) for ext in SUPPORTED_VIDEO_FORMATS):
                    prompt = "write a short one-paragraph description for the video, depending on its duration."
                    file_obj = self.upload_vid(file_path)

                log.info(f"Generating description for {file_name}")
                response = self.desc_model.generate_content([file_obj, prompt])
                genai.delete_file(file_obj.name)

                media_data.append({"source": file_path, "desc": response.text})
                

            video_prompt = f"""title: {self.title} description: {self.desc} style: {self.style} duration: {self.duration}
            Media clips and AI descriptions: {media_data}
            """
            response = self.video_model.generate_content(video_prompt)
            script = self.format_json(raw=response.text)
        
            log.info("Retrieving pexel footage and media bucket links..")
            for clip in script["scenes"]:
                source, form = clip["type"].split("_")
                if source == "stock":
                    suffix = f"query={quote(clip['query'])}&per_page=1"

                    if form == "video":
                        response = self.query_pexel(VID_PREF + suffix)
                        media_url = response["videos"][0]["video_files"][0]["link"]
                        clip["media_url"] = media_url
                        file_path = self.download_stock(media_url, user_media_path=self.user_media_path)

                    elif form == "photo":
                        response = self.query_pexel(IMG_PREF + suffix)
                        media_url = response["photos"][0]["src"]["landscape"]
                        clip["media_url"] = media_url
                        file_path = self.download_stock(media_url, user_media_path=self.user_media_path)

                    clip["media_path"] = file_path
                    del clip["query"]

                else:
                    temp_media_path = clip["media_path"]
                    user_media_unique_name = str(uuid.uuid4())
                    self.DATABASE_OPERATIONS_SERVICE.upload_file_by_path(temp_media_path, user_media_unique_name)
                    user_media_signed_url = self.DATABASE_OPERATIONS_SERVICE.get_file_link(key=user_media_unique_name)
                    clip["media_url"] = user_media_signed_url
  

            log.info("Generating Narration")
            for clip in script["scenes"]:
                file_name = os.path.splitext(os.path.basename(clip["media_path"]))[0]
                text = clip["script"]
                audio_path = self.text_to_speech(text, file_name, user_media_path=self.user_media_path)
                clip["audio_path"] = audio_path
            
            
            log.info("Generating video clips..")
            mov_clips = []
            for i, pair in enumerate(script["scenes"]):
                form = pair["type"].split("_")[1]
                if form == "photo":
                    mov_clip = create_photo_clip(pair["media_path"], pair["audio_path"], res)
                elif form == "video":
                    mov_clip = create_video_clip(pair["media_path"], pair["audio_path"], res)

                if pair["text_overlay"]:
                    mov_clip = add_text_overlay(mov_clip, pair["text_overlay"])

                # transitions
                # if i > 0:
                #     prev_clip = clips[-1]
                #     transition_type = script["scenes"][i - 1].get("transition", "fade")
                #     prev_clip, clip = VideoTransitionHelper.apply_transition(
                #         prev_clip, clip, transition_type
                #     )
                #     clips[-1] = prev_clip

                mov_clips.append(mov_clip)

            
            final_video = concatenate_videoclips(mov_clips)
            log.info('Writing timestamps..')
            for i in range(len(mov_clips)):
                clip_duration = mov_clips[i].duration
                if i == 0:
                    script["scenes"][i]["start_time"] = 0
                    script["scenes"][i]["end_time"] = 0+clip_duration
                else:
                    script["scenes"][i]["start_time"] = script["scenes"][i-1]["end_time"]
                    script["scenes"][i]["end_time"] = script["scenes"][i]["start_time"]+clip_duration

                del script["scenes"][i]["media_path"]
                del script["scenes"][i]["audio_path"]


            audio_path = f"{self.user_media_path}\\final_audio.wav"
            audio_clip = final_video.audio
            audio_clip.fps = SAMPLE_RATE
            audio_clip.write_audiofile(audio_path)

            log.info("Generating subtitles..")

            transcript = self.speech_to_text(audio_path)
            subtitles = get_subtitle_clips(transcript)
            final_video = CompositeVideoClip([final_video] + subtitles)

            log.info("Adding background music..")
            music_file = os.path.join("music", script["music"] + ".mp3")
            final_video = add_background_music(final_video, music_file)
            final_video_path = f"{self.user_media_path}\\final_video.mp4"
            
            final_video.write_videofile(
                final_video_path, codec="libx264", audio_codec="aac"
            )


            unique_final_video_name = str(uuid.uuid4())+SAVED_VIDEO_FORMAT
            self.DATABASE_OPERATIONS_SERVICE.upload_file_by_path(final_video_path, unique_final_video_name)
            signed_file_url = self.DATABASE_OPERATIONS_SERVICE.get_file_link(key=unique_final_video_name)
            shutil.rmtree(self.user_media_path, ignore_errors=True)
            
            return {"signed_url": signed_file_url, "script": script}
