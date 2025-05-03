import argparse
from utils import preview_renames, rename_files, undo_rename

def main():
    parser = argparse.ArgumentParser(description="Batch File Renamer")
    parser.add_argument("--folder", help="Path to the folder containing files")
    parser.add_argument("--prefix", default="", help="Prefix for the new filenames")
    parser.add_argument("--suffix", default="", help="Suffix for the new filenames")
    parser.add_argument("--replace", default="", help="String to replace in filenames")
    parser.add_argument("--new_text", default="", help="New text to replace the specified string")
    parser.add_argument("--recursive", action="store_true", help="Recursively rename files in subfolders")
    parser.add_argument("--preview", action="store_true", help="Preview the rename operations without executing")
    parser.add_argument("--undo", action="store_true", help="Undo the last rename operations")
    args = parser.parse_args()

    if args.undo:
        if args.folder:
            undo_rename(args.folder)
        else:
            print("Please specify the folder path for undo operation.")
    else:
        preview_list = preview_renames(
            folder_path=args.folder,
            prefix=args.prefix,
            suffix=args.suffix,
            replace=args.replace,
            new_text=args.new_text,
            recursive=args.recursive
        )

        if args.preview:
            for old, new in preview_list:
                print(f"{old} -> {new}")
        else:
            rename_files(preview_list)

if __name__ == "__main__":
    main()