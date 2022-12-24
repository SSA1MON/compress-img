from pathlib import Path

img_path = Path("C:/Users/LocalUser/Desktop")
app = Path(Path.cwd(), "mozjpeg/cjpeg")
image_format = [".jpg", ".jpeg", ".png"]
log_name = "compress"
postfix = "_compressed"
quality = "40"
timeout_time = 1    # time to establish a connection to the directory in seconds (0 - instant interruption)
creation_time = 0    # days
