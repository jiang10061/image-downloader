import os
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(filename="rename.log", level=logging.INFO, format="%(asctime)s - %(message)s")

def preview_renames(folder_path, prefix="", suffix="", replace="", new_text="", recursive=False):
    """
    预览重命名操作
    """
    preview = []
    for root, _, files in os.walk(folder_path):
        for filename in files:
            if replace and replace in filename:
                new_name = filename.replace(replace, new_text)
            else:
                base, ext = os.path.splitext(filename)
                new_name = f"{prefix}{base}{suffix}{ext}"

            preview.append((os.path.join(root, filename), os.path.join(root, new_name)))
        if not recursive:
            break
    return preview

def rename_files(preview_list):
    """
    执行重命名操作，并记录日志
    """
    for old_path, new_path in preview_list:
        try:
            os.rename(old_path, new_path)
            logging.info(f"Renamed: {old_path} -> {new_path}")
        except Exception as e:
            logging.error(f"Error renaming {old_path}: {e}")

def undo_rename(folder_path):
    """
    回退重命名操作
    """
    with open("rename.log", "r") as log_file:
        lines = log_file.readlines()

    # 从日志中提取重命名操作
    rename_operations = []
    for line in lines:
        if "Renamed:" in line:
            parts = line.split(" -> ")
            old_path = parts[1].strip()
            new_path = parts[0].split(": ")[1].strip()
            rename_operations.append((new_path, old_path))

    # 执行回退操作
    for old_path, new_path in rename_operations:
        try:
            os.rename(old_path, new_path)
            logging.info(f"Undone: {old_path} -> {new_path}")
        except Exception as e:
            logging.error(f"Error undoing {old_path}: {e}")