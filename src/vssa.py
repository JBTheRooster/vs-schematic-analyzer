import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import re
from collections import Counter
import csv
import os
import json5

import sys

# Load localization data from same directory as .exe or .py
def load_display_names():
    possible_paths = []

    if getattr(sys, 'frozen', False):
        # Running from .exe
        possible_paths.append(os.path.dirname(sys.executable))
    else:
        # Running from source
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, ".."))
        possible_paths.extend([
            project_root,              # e.g., project root
            os.path.join(project_root, "dist"),  # dev testing
            os.getcwd()                # wherever terminal is launched from
        ])

    for path in possible_paths:
        lang_path = os.path.join(path, "en.json")
        if os.path.exists(lang_path):
            try:
                with open(lang_path, "r", encoding="utf-8") as f:
                    return json5.load(f)
            except Exception as e:
                print(f"Error loading en.json from {lang_path}: {e}")
                return {}

    print("Warning: en.json not found. Display names will fall back to block codes.")
    return {}

lang_data = load_display_names()

def get_display_name(block_code):
    try:
        if not lang_data:
            return block_code

        parts = block_code.split(":")
        if len(parts) == 2:
            namespace, code = parts
        else:
            namespace = "game"
            code = parts[0]

        possible_keys = [
            f"block-{code}",
            f"item-{code}",
            f"{namespace}:{code}",
            code
        ]

        for key in possible_keys:
            if key in lang_data:
                return lang_data[key]

        return fallback_format(code)

    except Exception:
        return block_code

def fallback_format(code):
    suffixes = [
        "-north", "-south", "-east", "-west",
        "-up", "-down", "-left", "-right",
        "-free", "-normal", "-p0", "-p1", "-p2", "-pl", "-pr",
        "-we", "-ud"
    ]
    for suffix in suffixes:
        if code.endswith(suffix):
            code = code.removesuffix(suffix)
    code = code.replace("-", " ").strip()
    return code.title()

# Global state
current_data = []
filtered_data = []
selected_file_path = ""
sort_mode = "Count ↓"

def process_file(file_path):
    global current_data
    current_data = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json_raw = f.read()

        block_codes_match = re.search(r'"BlockCodes"\s*:\s*{([^}]+)}', json_raw)
        block_code_map = {}
        if block_codes_match:
            block_codes_raw = block_codes_match.group(1)
            for line in block_codes_raw.split(','):
                match = re.match(r'"?(\d+)"?\s*:\s*"([^"]+)"', line.strip())
                if match:
                    block_code_map[match.group(1)] = match.group(2)

        block_ids_match = re.search(r'"BlockIds"\s*:\s*\[([^\]]+)\]', json_raw)
        block_ids = []
        if block_ids_match:
            block_ids_raw = block_ids_match.group(1)
            block_ids = [id.strip() for id in block_ids_raw.split(',')]

        block_counts = Counter(block_ids)

        for block_id, count in block_counts.items():
            raw_code = block_code_map.get(block_id, f"UNKNOWN ID: {block_id}")
            name = get_display_name(raw_code)
            current_data.append({
                "Block ID": block_id,
                "Block Name": name,
                "Count": count
            })

    except Exception as e:
        messagebox.showerror("Error", f"Failed to process file: {e}")

def browse_file():
    global selected_file_path
    path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if path:
        selected_file_path = path
        file_label_var.set(f"Loaded file: {os.path.basename(path)}")

def drop_handler(event):
    global selected_file_path
    path = event.data.strip("{}")
    if os.path.isfile(path) and path.lower().endswith(".json"):
        selected_file_path = path
        file_label_var.set(f"Loaded file: {os.path.basename(path)}")
    else:
        messagebox.showerror("Invalid File", "Please drop a valid .json schematic file.")

def apply_sort_and_filter():
    global filtered_data
    search = filter_entry.get().lower()
    filtered_data = [entry for entry in current_data if search in entry["Block Name"].lower()]
    if sort_mode == "Count ↓":
        filtered_data.sort(key=lambda x: x["Count"], reverse=True)
    elif sort_mode == "Count ↑":
        filtered_data.sort(key=lambda x: x["Count"])
    elif sort_mode == "Name A–Z":
        filtered_data.sort(key=lambda x: x["Block Name"])
    display_results()

def display_results():
    result_box.delete(1.0, tk.END)
    for entry in filtered_data:
        result_box.insert(tk.END, f"There are {entry['Count']} blocks of {entry['Block Name']}.\n")

def analyze_file():
    if not selected_file_path:
        messagebox.showwarning("No File", "Please select or drop a schematic file first.")
        return
    process_file(selected_file_path)
    apply_sort_and_filter()

def reset_filter():
    filter_entry.delete(0, tk.END)
    apply_sort_and_filter()

def update_sort(*args):
    global sort_mode
    sort_mode = sort_var.get()
    apply_sort_and_filter()

def export_txt():
    if not filtered_data:
        messagebox.showwarning("No Data", "Analyze a schematic first.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text File", "*.txt")])
    if path:
        with open(path, "w", encoding="utf-8") as f:
            for entry in filtered_data:
                f.write(f"There are {entry['Count']} blocks of {entry['Block Name']}.\n")
        messagebox.showinfo("Exported", f"Results saved to {path}")

def export_csv():
    if not filtered_data:
        messagebox.showwarning("No Data", "Analyze a schematic first.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV File", "*.csv")])
    if path:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Block ID", "Block Name", "Count"])
            writer.writeheader()
            writer.writerows(filtered_data)
        messagebox.showinfo("Exported", f"Results saved to {path}")

# GUI Setup
root = TkinterDnD.Tk()
root.title("Vintage Story Schematic Analyzer")
root.geometry("800x650")
root.resizable(True, True)

file_label_var = tk.StringVar()
file_label_var.set("No file loaded.")

label = tk.Label(root, text="Click 'Browse' to locate your .json schematic or drag and drop it in the box below.", font=("Arial", 12))
label.pack(pady=10)

frame = tk.Frame(root)
frame.pack()

browse_button = tk.Button(frame, text="Browse", command=browse_file)
browse_button.grid(row=0, column=0, padx=5)

file_label = tk.Label(root, textvariable=file_label_var, fg="gray")
file_label.pack(pady=5)

drop_label = tk.Label(root, text="(Drop .json file here)", relief="groove", height=6, bd=2, font=("Arial", 11), bg="#f8f8f8")
drop_label.pack(fill="x", padx=10, pady=10)
drop_label.drop_target_register(DND_FILES)
drop_label.dnd_bind("<<Drop>>", drop_handler)

analyze_button = tk.Button(root, text="Analyze Blocks", font=("Arial", 11, "bold"), command=analyze_file)
analyze_button.pack(pady=10)

# Filter and Sort Controls
control_frame = tk.Frame(root)
control_frame.pack(pady=5)

tk.Label(control_frame, text="Filter:").grid(row=0, column=0, padx=5)
filter_entry = tk.Entry(control_frame)
filter_entry.grid(row=0, column=1, padx=5)
reset_button = tk.Button(control_frame, text="Reset Filter", command=reset_filter)
reset_button.grid(row=0, column=2, padx=5)

tk.Label(control_frame, text="Sort by:").grid(row=0, column=3, padx=5)
sort_var = tk.StringVar(value="Count ↓")
sort_dropdown = ttk.Combobox(control_frame, textvariable=sort_var, values=["Count ↓", "Count ↑", "Name A–Z"], state="readonly")
sort_dropdown.grid(row=0, column=4, padx=5)
sort_dropdown.bind("<<ComboboxSelected>>", update_sort)

result_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Courier New", 10))
result_box.pack(expand=True, fill="both", padx=10, pady=10)

export_frame = tk.Frame(root)
export_frame.pack(pady=5)

export_txt_button = tk.Button(export_frame, text="Export to .txt", command=export_txt)
export_txt_button.pack(side=tk.LEFT, padx=5)

export_csv_button = tk.Button(export_frame, text="Export to .csv", command=export_csv)
export_csv_button.pack(side=tk.LEFT, padx=5)

root.mainloop()

# This script provides a GUI for analyzing Vintage Story schematic files, counting block occurrences, and exporting results.