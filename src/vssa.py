import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import re
from collections import Counter
import csv
import os

# Shared output content
current_output = ""
current_data = []  # List of dicts: {"Block ID": id, "Block Name": name, "Count": count}
current_file = None

def process_file(file_path):
    global current_output, current_data, current_file
    current_file = file_path
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json_raw = f.read()

        # Extract BlockCodes
        block_codes_match = re.search(r'"BlockCodes"\s*:\s*{([^}]+)}', json_raw)
        block_code_map = {}
        if block_codes_match:
            block_codes_raw = block_codes_match.group(1)
            for line in block_codes_raw.split(','):
                match = re.match(r'"?(\d+)"?\s*:\s*"([^"]+)"', line.strip())
                if match:
                    block_code_map[match.group(1)] = match.group(2)

        # Extract BlockIds
        block_ids_match = re.search(r'"BlockIds"\s*:\s*\[([^\]]+)\]', json_raw)
        block_ids = []
        if block_ids_match:
            block_ids_raw = block_ids_match.group(1)
            block_ids = [id.strip() for id in block_ids_raw.split(',')]

        # Count occurrences
        block_counts = Counter(block_ids)

        # Build output and data
        output_lines = []
        current_data = []
        for block_id, count in block_counts.most_common():
            name = block_code_map.get(block_id, f"UNKNOWN ID: {block_id}")
            output_lines.append(f"There are {count} blocks of {name}.")
            current_data.append({
                "Block ID": block_id,
                "Block Name": name,
                "Count": count
            })

        current_output = "\n".join(output_lines)
        return current_output

    except Exception as e:
        return f"Error processing file: {e}"

def browse_file():
    path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if path:
        show_results(path)

def drop_handler(event):
    path = event.data.strip("{}")
    if os.path.isfile(path) and path.lower().endswith(".json"):
        show_results(path)
    else:
        messagebox.showerror("Invalid File", "Please drop a valid .json schematic file.")

def show_results(path):
    output = process_file(path)
    result_box.delete(1.0, tk.END)
    result_box.insert(tk.END, output)

def export_txt():
    if not current_output:
        messagebox.showwarning("No Data", "Load a schematic first.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text File", "*.txt")])
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(current_output)
        messagebox.showinfo("Exported", f"Results saved to {path}")

def export_csv():
    if not current_data:
        messagebox.showwarning("No Data", "Load a schematic first.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV File", "*.csv")])
    if path:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Block ID", "Block Name", "Count"])
            writer.writeheader()
            writer.writerows(current_data)
        messagebox.showinfo("Exported", f"Results saved to {path}")

# GUI setup
root = TkinterDnD.Tk()
root.title("Vintage Story Schematic Analyzer")
root.geometry("750x550")
root.resizable(False, False)

label = tk.Label(root, text="Drag and drop a .json schematic here or click 'Browse'", font=("Arial", 12))
label.pack(pady=10)

frame = tk.Frame(root)
frame.pack()

browse_button = tk.Button(frame, text="Browse", command=browse_file)
browse_button.grid(row=0, column=0, padx=5)

export_txt_button = tk.Button(frame, text="Export to .txt", command=export_txt)
export_txt_button.grid(row=0, column=1, padx=5)

export_csv_button = tk.Button(frame, text="Export to .csv", command=export_csv)
export_csv_button.grid(row=0, column=2, padx=5)

# Drop target
drop_label = tk.Label(root, text="(Or drop your file here)", relief="groove", height=2)
drop_label.pack(fill="x", padx=10, pady=5)
drop_label.drop_target_register(DND_FILES)
drop_label.dnd_bind("<<Drop>>", drop_handler)

# Result box
result_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Courier New", 10))
result_box.pack(expand=True, fill="both", padx=10, pady=10)

root.mainloop()
