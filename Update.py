import os
import shutil
from dulwich import porcelain

directory = os.path.dirname(__file__)
src_dir = os.path.join(directory, "update_files")
dst_dir = directory
repo_url = "https://github.com/cedzeedev/cedzeebrowser.git"

EXCLUDE = {
    os.path.join("resources", "config.json"),
    os.path.join("resources", "config", "history.csv"),
    os.path.join("resources", "saves", "favorites.json"),
}

def update_all():
    if os.path.isdir(src_dir):
        shutil.rmtree(src_dir, ignore_errors=True)
    porcelain.clone(repo_url, src_dir)

    if not os.path.isdir(src_dir):
        raise FileNotFoundError(f"Le dossier source '{src_dir}' est introuvable après clonage.")
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

    shutil.rmtree(src_dir, ignore_errors=True)

    print("[update] Mise à jour terminée avec succès.")
