import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from utils import preview_renames, rename_files, undo_rename

class BatchFileRenamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch File Renamer")

        tk.Label(root, text="Folder Path:").grid(row=0, column=0, padx=10, pady=10)
        self.folder_path = tk.Entry(root, width=50)
        self.folder_path.grid(row=0, column=1, padx=10, pady=10)
        tk.Button(root, text="Browse", command=self.browse_folder).grid(row=0, column=2, padx=10, pady=10)

        tk.Label(root, text="Prefix:").grid(row=1, column=0, padx=10, pady=10)
        self.prefix = tk.Entry(root)
        self.prefix.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(root, text="Suffix:").grid(row=2, column=0, padx=10, pady=10)
        self.suffix = tk.Entry(root)
        self.suffix.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(root, text="Replace:").grid(row=3, column=0, padx=10, pady=10)
        self.replace = tk.Entry(root)
        self.replace.grid(row=3, column=1, padx=10, pady=10)

        tk.Label(root, text="New Text:").grid(row=4, column=0, padx=10, pady=10)
        self.new_text = tk.Entry(root)
        self.new_text.grid(row=4, column=1, padx=10, pady=10)

        self.recursive = tk.BooleanVar()
        tk.Checkbutton(root, text="Recursive", variable=self.recursive).grid(row=5, column=1, padx=10, pady=10)

        tk.Button(root, text="Preview", command=self.preview_renames).grid(row=6, column=1, padx=10, pady=10)
        tk.Button(root, text="Rename Files", command=self.rename_files).grid(row=7, column=1, padx=10, pady=10)
        tk.Button(root, text="Undo Rename", command=self.undo_rename).grid(row=8, column=1, padx=10, pady=10)

        self.preview_text = scrolledtext.ScrolledText(root, width=70, height=10)
        self.preview_text.grid(row=9, column=0, columnspan=3, padx=10, pady=10)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        self.folder_path.delete(0, tk.END)
        self.folder_path.insert(0, folder_path)

    def preview_renames(self):
        folder_path = self.folder_path.get()
        prefix = self.prefix.get()
        suffix = self.suffix.get()
        replace = self.replace.get()
        new_text = self.new_text.get()
        recursive = self.recursive.get()

        if not folder_path:
            messagebox.showerror("Error", "Please select a folder")
            return

        preview_list = preview_renames(folder_path, prefix, suffix, replace, new_text, recursive)
        self.preview_text.delete(1.0, tk.END)
        for old, new in preview_list:
            self.preview_text.insert(tk.END, f"{old} -> {new}\n")

    def rename_files(self):
        folder_path = self.folder_path.get()
        prefix = self.prefix.get()
        suffix = self.suffix.get()
        replace = self.replace.get()
        new_text = self.new_text.get()
        recursive = self.recursive.get()

        if not folder_path:
            messagebox.showerror("Error", "Please select a folder")
            return

        preview_list = preview_renames(folder_path, prefix, suffix, replace, new_text, recursive)
        rename_files(preview_list)
        messagebox.showinfo("Success", "Files renamed successfully")

    def undo_rename(self):
        folder_path = self.folder_path.get()
        if not folder_path:
            messagebox.showerror("Error", "Please select a folder")
            return

        undo_rename(folder_path)
        messagebox.showinfo("Success", "Rename operations undone successfully")

if __name__ == "__main__":
    root = tk.Tk()
    app = BatchFileRenamerGUI(root)
    root.mainloop()