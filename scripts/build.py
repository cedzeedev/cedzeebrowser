import PyInstaller.__main__
import os
import platform
import shutil

directory = os.path.dirname(os.path.abspath(__file__))
separator = ";" if platform.system() == "Windows" else ":"

resources = [
    ("resources", "resources"),
    ("theme", "theme"),
    ("web", "web"),
    ("offline", "offline"),
    ("version.json", "."),
    ("src", "src"),
]

args = [
    "main.py",
    "--name=main",
    "--noconfirm",
    "--windowed",
    "--clean",
    "--distpath=build_win",
    "--workpath=build/build",
    "--specpath=build/specs",
]

for src, dest in resources:
    full_src = os.path.abspath(src)
    args.append(f"--add-data={full_src}{separator}{dest}")

build_cache_dir = os.path.abspath("build")

if os.path.exists(build_cache_dir):
    print(f"Deleting the cache folder {build_cache_dir}...")
    shutil.rmtree(build_cache_dir)

PyInstaller.__main__.run(args)
