# Batch File Renamer

## Project Introduction
Batch File Renamer is a simple yet powerful tool for renaming multiple files in a folder. It supports various naming rules, such as renaming by sequence, adding prefixes/suffixes, replacing strings, and more. Additionally, it provides features like file type filtering, recursive processing of subfolders, preview functionality, and error handling. The tool also includes an **Undo** feature that allows users to revert the file names back to their original state after renaming.

## Features
- **Multiple Naming Rules**: Supports renaming by sequence, adding prefixes/suffixes, replacing strings, and renaming by date.
- **File Type Filtering**: Select specific file extensions to rename.
- **Recursive Processing**: Option to recursively rename files in subfolders.
- **Preview Functionality**: Preview the renamed file names before execution.
- **Error Handling**: Logs operations and error messages for troubleshooting.
- **Undo Functionality**: Revert the last renaming operations to restore original file names.
- **User-Friendly**: Provides both Command-Line Interface (CLI) and Graphical User Interface (GUI) options.

## Installation
### Command-Line Interface (CLI)
1. Ensure Python is installed (Python 3.6 or higher is recommended).
2. Clone the project repository:
   ```bash
   git clone https://github.com/jiang10061/BatchFileRenamer.git
3. Navigate to the project directory:
  ```bash
  cd BatchFileRenamer
  ```
4. Run the CLI mode:
  ```bash
  python main.py --cli
  ```
### Graphical User Interface (GUI)
1. Ensure Python is installed (Python 3.6 or higher is recommended).
2. Clone the project repository:
  ```bash
  git clone https://github.com/jiang10061/BatchFileRenamer.git
  ```
3. Navigate to the project directory:
  ```bash
  cd BatchFileRenamer
  ```
4. Run the GUI mode:
  ```bash
  python main.py
  ```
## Usage
### Command-Line Interface (CLI)
- Basic Usage:
  ```bash
  python main.py --cli --folder "path/to/folder" --prefix "new_" --suffix "_file" --replace "old" --new_text "new" --recursive
  ```
- Preview Renaming Operations:
  ```bash
  python main.py --cli --folder "path/to/folder" --prefix "new_" --suffix "_file" --replace "old" --new_text "new" --recursive --preview
  ```
- Undo Renaming Operations:
  ```bash
  python main.py --cli --folder "path/to/folder" --undo
  ```
### Graphical User Interface (GUI)
1. Launch the GUI:
  ```bash
  python main.py
  ```
2. Select the folder path in the GUI.
3. Enter prefixes, suffixes, replacement strings, and other parameters.
4. Click the "Preview" button to preview the renaming operations.
5. Click the "Rename Files" button to execute the renaming.
6. To undo the renaming operations, click the "Undo Rename" button.
## Project Structure
  ```
  BatchFileRenamer/
├── main.py                # Main script entry point
├── cli.py                 # Command-Line Interface logic
├── gui.py                 # Graphical User Interface logic
├── utils.py               # Core functionality implementation
├── README.md              # Project documentation
└── rename.log             # Log file
  ```
## Logging
All renaming operations and error messages are logged in the rename.log file. You can review this file to track operation history and troubleshoot issues.