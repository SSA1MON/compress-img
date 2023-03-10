from pathlib import Path

img_path = Path('C:/Users/LocalUser/Desktop')    # path to the directory with images
app = Path(Path.cwd(), 'mozjpeg/cjpeg')     # the path to the mozjpeg compression executable
image_format = ['.jpg', '.jpeg', '.png']    # list of file extensions suitable for compression

postfix = '_compressed'     # postfix in the file name after compression
quality = '40'     # percentage of preservation of the original image quality (100 is the original quality)

log_name = 'compress'
rotation = '1 day'  # the period after which the main logging file will be archived
compression = 'zip'     # logging file compression method

timeout_time = 2    # time to establish a connection to the directory in seconds (0 - instant interruption)
creation_time = 0    # how long ago should the photo be created (in days)
