"""
Simple Tkinter-based GUI for the production management utility.

This GUI allows the user to select a SWOOD ReportLists XML file and an Excel
file containing piece details, parse them using the functions from
production_management.py, and generate summary Excel files for material
stock and pieces requiring Homag processing.

Note: This is an initial prototype and can be extended with inventory
management, advanced reporting, and data visualization.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

import pandas as pd

# Import functions from production_management (assuming it is in the same
# directory or installed as a module)
try:
    import production_management as pm
except ImportError:
    pm = None


class ProductionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Production Management Utility")
        self.geometry("600x300")
        self.resizable(False, False)

        self.xml_path = tk.StringVar()
        self.excel_path = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="SWOOD XML file:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
        tk.Entry(self, textvariable=self.xml_path, width=50).grid(row=0, column=1, padx=5, pady=10)
        tk.Button(self, text="Browse", command=self.browse_xml).grid(row=0, column=2, padx=5, pady=10)

        tk.Label(self, text="Piece list Excel file:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
        tk.Entry(self, textvariable=self.excel_path, width=50).grid(row=1, column=1, padx=5, pady=10)
        tk.Button(self, text="Browse", command=self.browse_excel).grid(row=1, column=2, padx=5, pady=10)

        tk.Button(self, text="Run", command=self.run_processing, width=20).grid(row=2, column=1, pady=20)

    def browse_xml(self):
        filename = filedialog.askopenfilename(title="Select XML file", filetypes=[("XML files", "*.xml"), ("All files", "*.*")])
        if filename:
            self.xml_path.set(filename)

    def browse_excel(self):
        filename = filedialog.askopenfilename(title="Select Excel file", filetypes=[("Excel files", "*.xlsx;*.xls"), ("All files", "*.*")])
        if filename:
            self.excel_path.set(filename)

    def run_processing(self):
        if pm is None:
            messagebox.showerror("Error", "production_management module not found.")
            return
        xml_file = self.xml_path.get()
        excel_file = self.excel_path.get()
        out_dir = os.path.dirname(xml_file) if xml_file else os.path.dirname(excel_file)
        messages = []
        try:
            if xml_file and os.path.exists(xml_file):
                mdf = pm.parse_material_stock_from_xml(xml_file)
                if not mdf.empty:
                    out_path = os.path.join(out_dir, 'material_stock_summary.xlsx')
                    pm.export_to_excel(mdf, out_path)
                    messages.append(f"Material summary saved to {out_path}")
                else:
                    messages.append("No material stock information found in XML.")
            if excel_file and os.path.exists(excel_file):
                df = pm.load_piece_list_from_excel(excel_file)
                if not df.empty:
                    homag_df = pm.filter_homag_pieces(df)
                    out_path = os.path.join(out_dir, 'homag_pieces.xlsx')
                    pm.export_to_excel(homag_df, out_path)
                    messages.append(f"Homag pieces list saved to {out_path}")
                else:
                    messages.append("Excel file is empty.")
            if messages:
                messagebox.showinfo("Processing complete", "\n".join(messages))
            else:
                messagebox.showwarning("No action", "Please select at least one file to process.")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))


def main():
    app = ProductionApp()
    app.mainloop()


if __name__ == '__main__':
    main()
