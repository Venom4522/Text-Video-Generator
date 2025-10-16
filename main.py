import os
import json
import csv
import logging
from video_creator import VideoCreator

# --- Absolute path for config file ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')

def setup_directories(paths_config):
    """Ensures all necessary project directories exist."""
    logging.info("Setting up project directories...")
    try:
        os.makedirs(paths_config['output'], exist_ok=True)
        assets_dir = paths_config['assets']
        os.makedirs(os.path.join(assets_dir, 'fonts'), exist_ok=True)
        os.makedirs(os.path.join(assets_dir, 'images'), exist_ok=True)
        logging.info("Directories are ready.")
        return True
    except Exception as e:
        logging.error(f"Error creating directories: {e}")
        return False

def load_quotes(file_path, assets_path):
    """Loads quotes from either a .txt or .csv file."""
    quotes = []
    logging.info(f"Loading quotes from: {file_path}")
    
    if file_path.endswith('.txt'):
        logging.info(f"Detected TXT file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    quotes.append({'text': line.strip(), 'author': '', 'background_image': ''})
    
    elif file_path.endswith('.csv'):
        logging.info(f"Detected CSV file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                quotes.append({
                    'text': row.get('text', ''),
                    'author': row.get('author', ''),
                    'background_image': row.get('background_image', '')
                })
    return quotes

def merge_configs(base, custom):
    """Merges custom GUI config into the base config from the file."""
    for key, value in custom.items():
        if isinstance(value, dict) and key in base:
            base[key].update(value)
        else:
            base[key] = value
    return base

def run_video_generation(quotes_path, custom_config):
    """Main function to orchestrate the video generation process."""
    logging.info("Starting video generation process...")
    try:
        logging.info(f"Attempting to load config from: {CONFIG_PATH}")
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.error(f"Error: Configuration file not found at '{CONFIG_PATH}'")
        logging.error("Exiting due to configuration error.")
        return
    
    # Merge GUI settings over the file settings
    config = merge_configs(config, custom_config)

    if not setup_directories(config['paths']):
        return
        
    quotes_data = load_quotes(quotes_path, config['paths']['assets'])
    if not quotes_data:
        logging.warning("No quotes found in the file. Nothing to generate.")
        return

    creator = VideoCreator(config)
    
    for i, quote in enumerate(quotes_data, 1):
        logging.info(f"Processing video {i}/{len(quotes_data)} for quote: \"{quote['text'][:30]}...\"")
        try:
            creator.create_video(quote, i)
        except Exception as e:
            logging.error(f"Failed to create video for quote: {quote['text']}. Error: {e}")

    logging.info("-" * 20)
    logging.info(f"SUCCESS: All {len(quotes_data)} videos have been generated in the '{config['paths']['output']}' folder.")
    logging.info("-" * 20)

