notify_msg = ">> Notifications can be turned off in the config file inside the host"
ERROR_TEXT = "Status: Completed with an error\n" \
             "Error: {error}\n" \
             "Path: {path}\n" \
             "Compressed files: {files}\n" \
             "Saved size: {size} MB\n" \
             "Time: {time} seconds\n\n" \
             f"{notify_msg} " + "{ip}"
SUCCESS_TEXT = "Status: Successfully completed\n" \
               "Path: {path}\n" \
               "Compressed files: {files}\n" \
               "Saved size: {size} MB\n" \
               "Time: {time} seconds\n\n" \
               f"{notify_msg} " + "{ip}"
