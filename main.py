import os
import cv2
import sys
import time
import shutil
import subprocess
import numpy as np

BLOCK = "▀"
RESET = "\033[0m"

def ClearConsole():
    os.system("cls" if os.name == "nt" else "clear")

def GetVideoCapture(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print("Error: Cannot open video.")
        sys.exit(1)
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    if fps <= 0:
        fps = 30.0
    return cap, fps

def ResizeFrame(frame, width, height):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return cv2.resize(frame, (width, height * 2), interpolation=cv2.INTER_AREA)

def FrameToAscii(frame_img):
    height, width, _ = frame_img.shape
    top_pixels = frame_img[0::2]
    bottom_pixels = frame_img[1::2]
    if bottom_pixels.shape[0] < top_pixels.shape[0]:
        bottom_pixels = np.vstack([bottom_pixels, np.zeros((1, width, 3), dtype=np.uint8)])

    lines = []
    for top_row, bottom_row in zip(top_pixels, bottom_pixels):
        line = "".join(
            f"\033[48;2;{bottom_px[0]};{bottom_px[1]};{bottom_px[2]}m"
            f"\033[38;2;{top_px[0]};{top_px[1]};{top_px[2]}m{BLOCK}"
            for top_px, bottom_px in zip(top_row, bottom_row)
        ) + RESET
        lines.append(line)
    return lines

def PrintAsciiFrame(lines):
    frame_str = "\033[H" + "\n".join(lines)
    sys.stdout.write(frame_str)
    sys.stdout.flush()

def GetTerminalSize():
    size = shutil.get_terminal_size(fallback=(80, 24))
    # leave one row so we don't scroll the terminal
    return size.columns, max(1, size.lines - 1)

def PlayVideoAscii(video_path):
    term_width, term_height = GetTerminalSize()
    width = term_width
    height = term_height

    cap, fps = GetVideoCapture(video_path)
    frame_duration = 1 / fps

    audio_process = None
    try:
        audio_process = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", video_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        audio_process = None

    start_time = time.time()
    frame_number = 0

    while True:
        # skip frames if we are behind to reduce drift
        now = time.time()
        target_frame = int((now - start_time) / frame_duration)
        while frame_number < target_frame:
            ret, _ = cap.read()
            if not ret:
                cap.release()
                if audio_process:
                    audio_process.terminate()
                ClearConsole()
                return
            frame_number += 1

        ret, frame = cap.read()
        if not ret:
            break

        resized = ResizeFrame(frame, width, height)
        ascii_lines = FrameToAscii(resized)
        PrintAsciiFrame(ascii_lines)

        frame_number += 1
        target_time = start_time + frame_number * frame_duration
        sleep_time = target_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)

    cap.release()
    if audio_process:
        audio_process.terminate()
    ClearConsole()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    try:
        PlayVideoAscii(video_path)
    except KeyboardInterrupt:
        ClearConsole()
