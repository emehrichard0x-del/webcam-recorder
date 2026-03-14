import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import datetime
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from moviepy.editor import VideoFileClip, AudioFileClip
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class HDRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("HD Camera Recorder (1080p + Sound)")
        self.root.geometry("1000x800")

        self.cap = cv2.VideoCapture(0)

        # Set HD resolution (1080p)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        self.recording = False
        self.audio_data = []
        self.fs = 44100

        self.video_label = ctk.CTkLabel(root, text="")
        self.video_label.pack(pady=20)

        self.indicator = ctk.CTkLabel(root, text="", text_color="red", font=("Arial", 20))
        self.indicator.pack()

        button_frame = ctk.CTkFrame(root)
        button_frame.pack(pady=20)

        self.record_btn = ctk.CTkButton(button_frame, text="● Record (HD)",
                                        fg_color="green",
                                        command=self.start_recording)
        self.record_btn.grid(row=0, column=0, padx=20)

        self.stop_btn = ctk.CTkButton(button_frame, text="■ Stop",
                                      fg_color="red",
                                      command=self.stop_recording)
        self.stop_btn.grid(row=0, column=1, padx=20)

        self.update_video()

    def update_video(self):
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            self.video_label.configure(image=imgtk)
            self.video_label.image = imgtk

            if self.recording:
                self.video_writer.write(frame)

        self.root.after(10, self.update_video)

    def audio_callback(self, indata, frames, time, status):
        if self.recording:
            self.audio_data.append(indata.copy())

    def start_recording(self):
        if not self.recording:
            self.recording = True
            self.audio_data = []

            self.filename = datetime.datetime.now().strftime("HD_%Y%m%d_%H%M%S")
            self.video_path = self.filename + "_video.mp4"
            self.audio_path = self.filename + "_audio.wav"
            self.final_path = self.filename + "_FINAL.mp4"

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                self.video_path,
                fourcc,
                30.0,
                (1920, 1080)
            )

            self.stream = sd.InputStream(samplerate=self.fs,
                                         channels=2,
                                         callback=self.audio_callback)
            self.stream.start()

            self.indicator.configure(text="recording")

    def stop_recording(self):
        if self.recording:
            self.recording = False

            self.video_writer.release()
            self.stream.stop()
            self.stream.close()

            audio_np = np.concatenate(self.audio_data, axis=0)
            write(self.audio_path, self.fs, audio_np)

            video_clip = VideoFileClip(self.video_path)
            audio_clip = AudioFileClip(self.audio_path)
            final_clip = video_clip.set_audio(audio_clip)

            final_clip.write_videofile(self.final_path,
                                       codec="libx264",
                                       audio_codec="aac")

            video_clip.close()
            audio_clip.close()
            final_clip.close()

            os.remove(self.video_path)
            os.remove(self.audio_path)

            self.indicator.configure(text="saved")

    def __del__(self):
        if self.cap.isOpened():
            self.cap.release()

root = ctk.CTk()
app = HDRecorder(root)
root.mainloop()
