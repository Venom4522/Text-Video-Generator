import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging
import platform
import subprocess

class VideoCreator:
    def __init__(self, config):
        self.config = config
        self.frame_size = tuple(config['video']['frame_size'])
        self.fps = config['video']['fps']
        self.font = self._find_font()

    def _find_font(self):
        """
        Tries to load a user-specified font from the assets folder first.
        If that fails, it searches for common system fonts.
        """
        user_font_path = self.config['text'].get('font_path', '')

        # 1. Try user-specified font
        if user_font_path and os.path.exists(user_font_path):
            try:
                font = ImageFont.truetype(user_font_path, self.config['text']['font_size'])
                logging.info(f"Successfully loaded user-specified font: {user_font_path}")
                return font
            except IOError:
                logging.warning(f"Could not load user font at '{user_font_path}', searching for system fonts.")

        # 2. Search for common system fonts
        system = platform.system()
        font_names = []
        if system == "Windows":
            font_names = ["arial.ttf", "calibri.ttf", "verdana.ttf"]
        elif system == "Darwin": # macOS
            font_names = ["Arial.ttf", "Helvetica.ttf"]
        else: # Linux
            font_names = ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Arial.ttf"]
        
        for font_name in font_names:
            try:
                font = ImageFont.truetype(font_name, self.config['text']['font_size'])
                logging.info(f"Found and loaded system font: {font_name}")
                return font
            except IOError:
                continue
        
        # 3. Fallback to default
        logging.warning("No suitable system fonts found. Using default PIL font.")
        return ImageFont.load_default()

    def _draw_text(self, draw, text, author):
        """Draws wrapped text and author onto the image."""
        max_width = self.frame_size[0] - self.config['text']['margin'] * 2
        line_spacing = self.config['text']['line_spacing']
        
        # --- Text Wrapping Logic ---
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            # Use getbbox for more accurate width calculation
            if self.font.getbbox(test_line)[2] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)

        # --- Calculate total height for vertical positioning ---
        total_text_height = 0
        line_heights = [self.font.getbbox(line)[3] + line_spacing for line in lines]
        total_text_height = sum(line_heights) - line_spacing # remove last spacing

        vertical_pos = self.config['text']['vertical_pos']
        if vertical_pos == 'middle':
            y = (self.frame_size[1] - total_text_height) / 2
        elif vertical_pos == 'top':
            y = self.config['text']['margin']
        else: # bottom
            y = self.frame_size[1] - total_text_height - self.config['text']['margin']

        # --- Draw each line ---
        text_align = self.config['text']['text_align']
        for line in lines:
            line_width = self.font.getbbox(line)[2]
            if text_align == 'center':
                x = (self.frame_size[0] - line_width) / 2
            elif text_align == 'left':
                x = self.config['text']['margin']
            else: # right
                x = self.frame_size[0] - line_width - self.config['text']['margin']
            
            draw.text((x, y), line, font=self.font, fill=tuple(self.config['text']['font_color']))
            y += self.font.getbbox(line)[3] + line_spacing

    def create_video(self, quote_data, video_index):
        """Generates a single video for the given quote data."""
        # --- Create Base Frame ---
        bg_image_path = os.path.join(self.config['paths']['assets'], 'images', quote_data['background_image'])
        if quote_data['background_image'] and os.path.exists(bg_image_path):
            logging.info(f"Using background image: {bg_image_path}")
            img = Image.open(bg_image_path).resize(self.frame_size).convert("RGB")
        else:
            img = Image.new("RGB", self.frame_size, tuple(self.config['video']['background_color']))
        
        draw = ImageDraw.Draw(img)
        self._draw_text(draw, quote_data['text'], quote_data['author'])
        
        final_frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # --- Video Writing ---
        output_filename = f"quote_{video_index:03d}.mp4"
        video_path = os.path.join(self.config['paths']['output'], output_filename)
        logging.info(f"Attempting to create video file at: {video_path}")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, self.fps, self.frame_size)

        if not out.isOpened():
            logging.error("CRITICAL ERROR: cv2.VideoWriter failed to open.")
            logging.error("This can be due to missing codecs, incorrect paths, or permissions.")
            return

        logging.info("VideoWriter opened successfully. Writing frames...")
        for _ in range(self.config['video']['duration'] * self.fps):
            out.write(final_frame)
            
        out.release()
        
        if os.path.exists(video_path):
            logging.info(f"Successfully created video: {output_filename}")
        else:
            logging.error(f"FAILED to create video file on disk: {output_filename}")

