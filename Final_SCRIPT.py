import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Settings
video_duration = 5  # seconds
fps = 24
frame_size = (720, 1280)  # width x height
font_size = 40
font_color = (255, 255, 255)  # white
background_color = (0, 0, 0)  # black
output_dir = "quote_videos"

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Load quotes from file
with open("quotes.txt", "r", encoding="utf-8") as f:
    quotes = [line.strip() for line in f if line.strip()]

# Load a default font
try:
    font = ImageFont.truetype("arial.ttf", font_size)
except IOError:
    font = ImageFont.load_default()

# Function to create a frame with centered text
def create_text_frame(text, size, font, font_color, bg_color):
    img = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(img)

    # Wrap text if too long
    max_width = size[0] - 40
    words = text.split()
    lines = []
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if draw.textlength(test_line, font=font) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)

    # Calculate total text height
    total_text_height = sum([draw.textbbox((0, 0), line, font=font)[3] for line in lines])
    y = (size[1] - total_text_height) // 2

    for line in lines:
        text_width = draw.textlength(line, font=font)
        x = (size[0] - int(text_width)) // 2
        draw.text((x, y), line, font=font, fill=font_color)
        y += draw.textbbox((0, 0), line, font=font)[3]

    return np.array(img)

# Generate videos
for idx, quote in enumerate(quotes, start=1):
    frame = create_text_frame(quote, frame_size, font, font_color, background_color)
    video_path = os.path.join(output_dir, f"quote_{idx:03d}.mp4")
    out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, frame_size)

    for _ in range(video_duration * fps):
        out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    out.release()

print(f"Generated {len(quotes)} videos in '{output_dir}' folder.")
