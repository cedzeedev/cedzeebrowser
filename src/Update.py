import os
import sys
import shutil

from dulwich import porcelain
from pathlib import Path

from src.ConsoleLogger import logger

# Get project root directory
directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

path_dir = Path(directory)
src_dir = os.path.join(directory, "update_files")
dst_dir = directory
repo = "cedzeedev/cedzeebrowser"
repo_url = f"https://github.com/{repo}.git"
token = None
headers = {"Authorization": f"token {token}"} if token else {}

# Files to exclude from update
EXCLUDE = {
    os.path.normpath(os.path.join("resources", "config.json")),
    os.path.normpath(os.path.join("resources", "config", "history.csv")),
    os.path.normpath(os.path.join("resources", "saves", "favorites.json")),
}

# Folders to remove before update
FOLDERS_TO_REMOVE = ["scripts", "web", "src", "theme", "offline"]


def update_all():
    """
    Update the application by cloning the latest repo and replacing files,
    excluding config/history/favorites.
    """
    version_file = os.path.join(dst_dir, "version.json")
    # Remove version file if exists
    if os.path.exists(version_file):
        os.remove(version_file)
        logger.info(f"UPDATE: Deleted : {version_file}")

    # Remove previous update_files directory
    if os.path.isdir(src_dir):
        shutil.rmtree(src_dir, ignore_errors=True)

    # Clone repo to update_files
    porcelain.clone(repo_url, src_dir)

    if not os.path.isdir(src_dir):
        raise FileNotFoundError(
            f"The source file '{src_dir}' is missing after cloning."
        )

    # Remove old folders
    for folder in FOLDERS_TO_REMOVE:
        folder_path = os.path.join(dst_dir, folder)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path, ignore_errors=True)
            logger.info(f"UPDATE: Deleted : {folder_path}")

    # Move new files, skipping excluded ones
    for root, dirs, files in os.walk(src_dir):
        rel_root = os.path.relpath(root, src_dir)
        if rel_root.startswith(".git"):
            continue
        target_root = os.path.join(dst_dir, rel_root)
        os.makedirs(target_root, exist_ok=True)
        for fname in files:
            rel_path = os.path.normpath(os.path.join(rel_root, fname))
            if rel_path in EXCLUDE:
                continue

            src_path = os.path.join(root, fname)
            dst_path = os.path.join(target_root, fname)

            if os.path.exists(dst_path):
                if os.path.isfile(dst_path) or os.path.islink(dst_path):
                    os.remove(dst_path)
                elif os.path.isdir(dst_path):
                    shutil.rmtree(dst_path)

            shutil.move(src_path, dst_path)

    # Clean up update_files
    shutil.rmtree(src_dir, ignore_errors=True)

    logger.info("UPDATE: Update ended.")
    logger.info("UPDATE: Closing...")
    sys.exit()
