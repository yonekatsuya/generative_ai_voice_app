import wave
import os
import pyaudio
from pydub import AudioSegment
import sounddevice as sd
import numpy as np
import time
from time import sleep
from scipy.io.wavfile import write
from pathlib import Path
import streamlit as st

def record_audio(fs=48000, dir="audio/input", silence_threshold=2.5, min_duration=0.05, amplitude_threshold=0.01):
    audio_directory = Path.cwd() / dir
    audio_directory.mkdir(parents=True, exist_ok=True)
    file_path = audio_directory / f"recorded_audio_input_{int(time.time())}.wav"

    recorded_audio = []
    silent_time = 0
    progress_num = 0

    desc_text = st.empty()
    desc_text.text("※無言の状態が5秒続くと、録音を終了します。")
    status_text = st.empty()
    progress_bar = st.progress(progress_num)

    with sd.InputStream(samplerate=fs, channels=2) as stream:
        while True:
            data, overflowed = stream.read(5000)
            if overflowed:
                st.error("メモリや音声入力速度の問題で、一部の音声データが失われた可能性があります。")
            recorded_audio.append(data)
            if np.all(np.abs(data) < amplitude_threshold):
                silent_time += min_duration
                progress_num += min_duration
                if round(progress_num*20)*2 <= 100:
                    status_text.text(f'Progress: {round(progress_num*20)*2}%')
                    progress_bar.progress(round(progress_num, 2) / 2.5)

                if silent_time >= silence_threshold:
                    desc_text.empty()
                    status_text.text('録音を終了しました。')
                    break
            else:
                silent_time = 0
                progress_num = 0
                progress_bar.progress(0)
                status_text.text(f'Progress: 0%')

    audio_data = np.concatenate(recorded_audio, axis=0)
    audio_data = np.int16(audio_data * 32767)# 録音データを16ビット整数に変換
    write(file_path, fs, audio_data)

    return file_path

def transcribe(file_path, client):
    with open(file_path, 'rb') as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript

def save_to_wav(response_content, output_file):
    """
    mp3形式の音声ファイルをwav形式に変換して保存
    """
    temp_file_name = "temp.mp3"
    with open(temp_file_name, "wb") as temp_file:
        temp_file.write(response_content)
    
    audio = AudioSegment.from_file(temp_file_name, format="mp3")
    audio.export(output_file, format="wav")

    # 一時ファイルを削除
    os.remove(temp_file_name)

def play_wav(filepath, speed=1.0):
    """
    音声ファイルの読み上げ
    Args:
        file_path: 音声ファイルのパス
        speed: 再生速度（1.0が通常速度、0.5で半分の速さ、2.0で倍速など）
    """

    # PyDubで音声ファイルを読み込む
    audio = AudioSegment.from_wav(filepath)
    
    # 速度を変更
    if speed != 1.0:
        # frame_rateを変更することで速度を調整
        modified_audio = audio._spawn(audio.raw_data, overrides={
            "frame_rate": int(audio.frame_rate * speed)
        })
        # 元のframe_rateに戻す（ピッチを保持したまま速度だけ変更）
        modified_audio = modified_audio.set_frame_rate(audio.frame_rate)
    else:
        modified_audio = audio

    # 一時ファイルとして保存
    temp_file = "temp_modified.wav"
    modified_audio.export(temp_file, format="wav")
    
    # PyAudioで再生
    play_target_file = wave.open(temp_file, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(play_target_file.getsampwidth()),
                    channels=play_target_file.getnchannels(),
                    rate=play_target_file.getframerate(),
                    output=True)

    data = play_target_file.readframes(1024)
    while data:
        stream.write(data)
        data = play_target_file.readframes(1024)

    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # 一時ファイルを削除
    os.remove(temp_file)