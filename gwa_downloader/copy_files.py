import shutil
from pathlib import Path
import importlib.resources as resources
import gwa_downloader.frontend as frontend

def copy_frontend():
    target_dir = Path(".")
    source = resources.files(frontend)

    def copy_dir(src, dst):
        for item in src.iterdir():
            dest = dst / item.name
            if item.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
                copy_dir(item, dest)
            else:
                with resources.as_file(item) as file_path:
                    shutil.copy(file_path, dest)

    copy_dir(source, target_dir)
    print(f"Copied frontend files to {target_dir}")
