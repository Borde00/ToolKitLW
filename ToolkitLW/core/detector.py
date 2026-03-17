import platform

def detect_os():
    system = platform.system()
    if system == "Linux":
        return "linux"
    elif system == "Windows":
        return "windows"
    else:
        return "unsupported"
