import os
import time
import json
import subprocess
from datetime import datetime
import pytz
from PIL import Image, ImageDraw, ImageFont

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def get_linux_environment():
    """Detects if the system is running X11 or Wayland."""
    xdg_session = os.environ.get("XDG_SESSION_TYPE", "").lower()
    return xdg_session if xdg_session in ["x11", "wayland"] else "x11"

def set_wallpaper(image_path, env):
    """Sets the wallpaper natively based on the desktop environment."""
    try:
        if env == "wayland":
            # Uses swww (highly efficient Wayland wallpaper daemon)
            subprocess.run(["swww", "img", image_path], check=True)
        else:
            # Uses feh for X11 backends
            subprocess.run(["feh", "--bg-scale", image_path], check=True)
    except FileNotFoundError:
        print(f"Error: Wallpaper utility for {env} not found. Please install 'feh' (X11) or 'swww' (Wayland).")

def generate_wallpaper(config, env):
    # Load original image safely without keeping it fully in memory
    with Image.open(config["image_path"]) as img:
        base_img = img.convert("RGB")
        draw = ImageDraw.Draw(base_img)
        
        # Fetch South African Time
        sa_tz = pytz.timezone('Africa/Johannesburg')
        sa_time = datetime.now(sa_tz).strftime("%H:%M")
        
        # Use a system font (fallback to default if not found)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", config["font_size"])
        except IOError:
            font = ImageFont.load_default()
            
        # Draw the time overlay
        draw.text(
            tuple(config["position"]), 
            sa_time, 
            fill=tuple(config["text_color"]), 
            font=font
        )
        
        # Save to a temporary fast-access location (RAM disk to eliminate disk wear)
        tmp_path = "/tmp/current_wallpaper.jpg"
        base_img.save(tmp_path, "JPEG", quality=90)
        
        # Set the desktop background
        set_wallpaper(tmp_path, env)

def main():
    env = get_linux_environment()
    print(f"Starting SA Wallpaper Service on standard {env.upper()} backend...")
    
    while True:
        try:
            config = load_config()
            generate_wallpaper(config, env)
        except Exception as e:
            print(f"Execution error: {e}")
            
        # High efficiency sleep to ensure near-zero CPU usage
        time.sleep(config.get("update_interval_seconds", 60))

if __name__ == "__main__":
    main()
