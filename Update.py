import os
import sys
import shutil
import zipfile
from dulwich import porcelain
from pathlib import Path
import requests
import subprocess

directory = os.path.dirname(__file__)
path_dir = Path(directory)
src_dir = os.path.join(directory, "update_files")
dst_dir = directory
repo = "cedzeedev/cedzeebrowser"
repo_url = f"https://github.com/{repo}.git"
token = None
headers = {"Authorization": f"token {token}"} if token else {}

EXCLUDE = {
    os.path.normpath(os.path.join("resources", "config.json")),
    os.path.normpath(os.path.join("resources", "config", "history.csv")),
    os.path.normpath(os.path.join("resources", "saves", "favorites.json")),
}

def is_internal_folder():
    if dst_dir.endswith("_internal"):
        return True
    else:
        return False

def restart_program():
    try:
        subprocess.Popen([sys.executable] + sys.argv, close_fds=True)
    except Exception as e:
        print(f"[update] Redémarrage via sys.executable échoué : {e}")
        fallback_path = os.path.abspath(os.path.join("..", "main.exe"))
        if os.path.isfile(fallback_path):
            print(f"[update] Tentative de redémarrage via {fallback_path}")
            subprocess.Popen([fallback_path], close_fds=True)
        else:
            print("[update] Échec du redémarrage : main.exe introuvable.")
    finally:
        sys.exit(0)

def update_all():
    if not is_internal_folder():
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

    else:
        print("L'auto-update n'est pas disponible sur application")
        ## Requit un token et c'est pas top
        #artifacts_url = f"https://api.github.com/repos/{repo}/actions/artifacts"
        #response = requests.get(artifacts_url, headers=headers)
        #data = response.json()

        #if "artifacts" not in data or len(data["artifacts"]) == 0:
        #    print("[update] Aucun artifact trouvé.")
        #else:
        #    latest_artifact = sorted(data["artifacts"], key=lambda x: x["created_at"], reverse=True)[0]
        #    artifact_id = latest_artifact["id"]
        #    name = latest_artifact["name"]
        #    zip_path = Path(f"../{name}.zip")
        #    extract_to = Path("../tmp")
        #    download_url = f"https://api.github.com/repos/{repo}/actions/artifacts/{artifact_id}/zip"
        #    download_response = requests.get(download_url, headers=headers, stream=True)
        #    if download_response.status_code == 200:
        #        with open(zip_path, "wb") as f:
        #            for chunk in download_response.iter_content(chunk_size=8192):
        #                f.write(chunk)
        #        print(f"Artifact téléchargé dans {zip_path}")
        #    else:
        #        print("Erreur lors du téléchargement :", download_response.status_code)
        #        print("Response Headers:", download_response.headers)
        #        print("Response Text:", download_response.text)
        #
        #        return

         #   extract_to.mkdir(parents=True, exist_ok=True)
        #   with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        #       zip_ref.extractall(extract_to)
        #
        #   internal_dir = extract_to / "__internal"
        #
        #   def is_excluded(path: Path):
        #        if internal_dir not in path.parents:
        #            return False
        #        rel_path = path.relative_to(internal_dir)
        #       return os.path.normpath(rel_path) in EXCLUDE
        #
        #   for item in extract_to.rglob("*"):
        #       if item.is_file():
        #           if is_excluded(item):
        #               print(f"[update] Fichier exclu : {item.relative_to(extract_to)}")
        #               continue
        #
        #           rel_path = item.relative_to(extract_to)
        #           target_path = path_dir / rel_path
        #           target_path.parent.mkdir(parents=True, exist_ok=True)
        #
        #           if target_path.exists():
        #               if target_path.is_file() or target_path.is_symlink():
        #                   target_path.unlink()
        #               elif target_path.is_dir():
        #                   shutil.rmtree(target_path)

        #           shutil.move(str(item), str(target_path))
        #           print(f"[update] Déplacé : {rel_path}")

#            if zip_path.exists():
#                zip_path.unlink()
#           shutil.rmtree(extract_to, ignore_errors=True)

    # print("[update] Update ended.")
    # print("[update] Rebooting...")
    # restart_program()


if __name__ == "__main__":
    print("[error] : you can't start this lib")
