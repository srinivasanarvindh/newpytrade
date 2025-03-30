import os
import shutil
from pathlib import Path

# Define project paths
PROJECT_ROOT = Path("c:/Users/Arvindh/Downloads/PyTradeAnalytics/PyTradeAnalytics")
ATTACHED_ASSETS = PROJECT_ROOT / "attached_assets"

# Helper function to find all Python files
def find_python_files(directory):
    return [f for f in directory.rglob("*.py")]

# Helper function to check if a file is used
def is_file_used(file_path, all_files):
    try:
        with open(file_path, "r", encoding="utf-8") as f:  # Specify utf-8 encoding
            content = f.read()
        return any(other_file.stem in content for other_file in all_files if other_file != file_path)
    except UnicodeDecodeError:
        print(f"Skipping file due to encoding issues: {file_path}")
        return False

# Main cleanup function
def cleanup_project():
    all_files = find_python_files(PROJECT_ROOT)
    used_files = set()

    # Identify used files
    for file in all_files:
        if is_file_used(file, all_files):
            used_files.add(file)

    # Move used files to attached_assets
    for file in used_files:
        relative_path = file.relative_to(PROJECT_ROOT)
        target_path = ATTACHED_ASSETS / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file), str(target_path))

    # Remove unused files and empty folders
    for file in all_files:
        if file not in used_files:
            file.unlink()
    for folder in PROJECT_ROOT.rglob("*"):
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()

if __name__ == "__main__":
    cleanup_project()
