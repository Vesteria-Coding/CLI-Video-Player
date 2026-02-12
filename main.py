import cv2
import sys
import time
import shutil
import subprocess
import numpy as np

BLOCK = '▀'
RESET = "\033[0m"

def RGB(R, G, B):
    return f"\033[48;2;{R};{G};{B}m"

def GetVideoCapture(Path):
    Cap = cv2.VideoCapture(Path)
    if not Cap.isOpened():
        print("Error: Cannot open video.")
        sys.exit(1)
    Fps = Cap.get(cv2.CAP_PROP_FPS)
    return Cap, Fps

def ResizeFrame(Frame, Width, Height):
    Frame = cv2.cvtColor(Frame, cv2.COLOR_BGR2RGB)
    return cv2.resize(Frame, (Width, Height * 2), interpolation=cv2.INTER_AREA)

def FrameToAscii(FrameImg):
    Height, Width, _ = FrameImg.shape
    TopPixels = FrameImg[0::2]
    BottomPixels = FrameImg[1::2]
    if BottomPixels.shape[0] < TopPixels.shape[0]:
        BottomPixels = np.vstack([BottomPixels, np.zeros((1, Width, 3), dtype=np.uint8)])
    Lines = []
    for TRow, BRow in zip(TopPixels, BottomPixels):
        Line = ''.join([
            f"\033[48;2;{b[0]};{b[1]};{b[2]}m\033[38;2;{r[0]};{r[1]};{r[2]}m{BLOCK}"
            for r, b in zip(TRow, BRow)
        ]) + RESET
        Lines.append(Line)
    return Lines

def PrintAsciiFrame(Lines):
    FrameStr = "\033[H" + "\n".join(Lines)
    sys.stdout.write(FrameStr)
    sys.stdout.flush()

def GetTerminalSize():
    Size = shutil.get_terminal_size(fallback=(80, 24))
    return Size.columns, Size.lines

def PlayVideoAscii(VideoPath):
    TermWidth, TermHeight = GetTerminalSize()
    Width = TermWidth
    Height = TermHeight
    Cap, Fps = GetVideoCapture(VideoPath)
    FrameDuration = 1 / Fps
    AudioProcess = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", VideoPath])
    StartTime = time.time()
    FrameNumber = 0
    while True:
        Ret, Frame = Cap.read()
        if not Ret:
            break
        Resized = ResizeFrame(Frame, Width, Height)
        AsciiLines = FrameToAscii(Resized)
        PrintAsciiFrame(AsciiLines)
        FrameNumber += 1
        TargetTime = StartTime + FrameNumber * FrameDuration
        Now = time.time()
        SleepTime = TargetTime - Now
        if SleepTime > 0:
            time.sleep(SleepTime)
    Cap.release()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <video_path>")
        sys.exit(1)

    VideoPath = sys.argv[1]
    PlayVideoAscii(VideoPath)
