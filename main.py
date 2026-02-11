import cv2
import sys
import time
import shutil
import subprocess
import numpy as np

BLOCK = '▀'
RESET = "\033[0m"

def rgb_bg(r, g, b):
    return f"\033[48;2;{r};{g};{b}m"

def get_video_capture(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print("Error: Cannot open video.")
        sys.exit(1)
    fps = cap.get(cv2.CAP_PROP_FPS)
    return cap, fps

def resize_frame(frame, width, height):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return cv2.resize(frame, (width, height * 2), interpolation=cv2.INTER_AREA)

def frame_to_ascii(frame_img):
    height, width, _ = frame_img.shape
    top_pixels = frame_img[0::2]
    bottom_pixels = frame_img[1::2]
    if bottom_pixels.shape[0] < top_pixels.shape[0]:
        bottom_pixels = np.vstack([bottom_pixels, np.zeros((1, width, 3), dtype=np.uint8)])
    lines = []
    for t_row, b_row in zip(top_pixels, bottom_pixels):
        line = ''.join([
            f"\033[48;2;{b[0]};{b[1]};{b[2]}m\033[38;2;{r[0]};{r[1]};{r[2]}m{BLOCK}"
            for r, b in zip(t_row, b_row)
        ]) + RESET
        lines.append(line)
    return lines

def print_ascii_frame(lines):
    frame_str = "\033[H" + "\n".join(lines)
    sys.stdout.write(frame_str)
    sys.stdout.flush()

def get_terminal_size():
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines

def play_video_ascii(video_path):
    term_width, term_height = get_terminal_size()
    width = term_width
    height = term_height
    cap, fps = get_video_capture(video_path)
    frame_duration = 1 / fps
    audio_process = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", video_path])
    start_time = time.time()
    frame_number = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        resized = resize_frame(frame, width, height)
        ascii_lines = frame_to_ascii(resized)
        print_ascii_frame(ascii_lines)
        frame_number += 1
        target_time = start_time + frame_number * frame_duration
        now = time.time()
        sleep_time = target_time - now
        if sleep_time > 0:
            time.sleep(sleep_time)
    cap.release()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    play_video_ascii(video_path)
