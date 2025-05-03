import sys
from cli import main as cli_main
from gui import BatchFileRenamerGUI

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        cli_main()
    else:
        import tkinter as tk
        root = tk.Tk()
        app = BatchFileRenamerGUI(root)
        root.mainloop()

if __name__ == "__main__":
    main()