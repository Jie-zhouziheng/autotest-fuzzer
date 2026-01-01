import os
from .config import CRASHES_DIR

def ensure_dirs():
    os.makedirs(CRASHES_DIR, exist_ok=True)

def save_crash(data: bytes):
    idx = len(os.listdir(CRASHES_DIR))
    path = os.path.join(CRASHES_DIR, f"crash_{idx:06d}")
    with open(path, 'wb') as f:
        f.write(data)