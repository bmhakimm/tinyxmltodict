import os
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
try:
    import production_management as pm
except ImportError:
    pm=None
try:
    import extended_management as em
except ImportError:
    em=None

class ProductionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Production Management Utility")
        self.geometry("620x360")
        self.resizable(False,False)
        self.xml_path=tk.StringVar(); self.excel_path=tk.StringVar(); self.db_path=tk.StringVar()
        self.build_ui()
    def build_ui(self):
        labels=["SWOOD XML file:","Piece list Excel file:","Inventory DB file:"]
        vars=[self.xml_path,self.excel_path,self.db_path]
        browse_fns=[self.browse_xml,self.browse_excel,self.browse_db]
        for i,(lab,var,fn) in enumerate(zip(labels,vars,browse_fns)):
            tk.Label(self,text=lab).grid(row=i,column=0,padx=10,pady=10,sticky='e')
            tk.Entry(self,textvariable=var,width=50).grid(row=i,column=1,padx=5,pady=10)
            tk.Button(self,text="Browse",command=fn).grid(row=i,column=2,padx=5,pady=10)
        tk.Button(self,text="Run (Summary & Homag)",command=self.run_processing,width=25).grid(row=3,column=1,pady=10)
        tk.Button(self,text="Generate Cut Lists",command=self.generate_cut_lists,width=20).grid(row=4,column=0,padx=5,pady=10)
        tk.Button(self,text="Init Inventory DB",command=self.init_inventory,width=20).grid(row=4,column=1,padx=5,pady=10)
        tk.Button(self,text="Update Inventory",command=self.update_inventory,width=20).grid(row=5,column=0,padx=5,pady=5)
        tk.Button(self,text="View Inventory",command=self.view_inventory,width=20).grid(row=5,column=1,padx=5,pady=5)
    def browse_xml(self):
        f=filedialog.askopenfilename(title="Select XML file",filetypes=[("XML files","*.xml"),("All files","*.*")])
        if f: self.xml_path.set(f)
    def browse_excel(self):
        f=filedialog.askopenfilename(title="Select Excel file",filetypes=[("Excel files","*.xlsx;*.xls"),("All files","*.*")])
        if f: self.excel_path.set(f)
    def browse_db(self):
        f=filedialog.askopenfilename(title="Select Inventory DB file",filetypes=[("SQLite DB","*.db"),("All files","*.*")])
        if f: self.db_path.set(f)
    def run_processing(self):
        if pm is None:
            messagebox.showerror("Error","production_management module not found."); return
        xml_file=self.xml_path.get(); excel_file=self.excel_path.get()
        out_dir=os.path.dirname(xml_file) if xml_file else os.path.dirname(excel_file)
        msgs=[]
        try:
            if xml_file and os.path.exists(xml_file):
                mdf=pm.parse_material_stock_from_xml(xml_file)
                if not mdf.empty:
                    out_path=os.path.join(out_dir,'material_stock_summary.xlsx')
                    pm.export_to_excel(mdf,out_path)
                    msgs.append(f"Material summary saved to {out_path}")
                else: msgs.append("No material stock information found in XML.")
            if excel_file and os.path.exists(excel_file):
                df=pm.load_piece_list_from_excel(excel_file)
                if not df.empty:
                    homag_df=pm.filter_homag_pieces(df)
                    out_path=os.path.join(out_dir,'homag_pieces.xlsx')
                    pm.export_to_excel(homag_df,out_path)
                    msgs.append(f"Homag pieces list saved to {out_path}")
                else: msgs.append("Excel file is empty.")
            if msgs:
                messagebox.showinfo("Processing complete","\n".join(msgs))
            else:
                messagebox.showwarning("No action","Please select at least one file to process.")
        except Exception as exc:
            messagebox.showerror("Error",str(exc))
    def generate_cut_lists(self):
        if em is None:
            messagebox.showerror("Error","extended_management module not found."); return
        excel_file=self.excel_path.get()
        if not excel_file or not os.path.exists(excel_file):
            messagebox.showwarning("Missing file","Please select a valid Excel file first."); return
        try:
            df=pm.load_piece_list_from_excel(excel_file) if pm else pd.read_excel(excel_file)
            if df.empty:
                messagebox.showwarning("Empty file","The selected Excel file is empty."); return
            cut_lists=em.generate_cut_lists(df)
            if not cut_lists:
                messagebox.showinfo("No cut lists","No cut lists could be generated."); return
            out_dir=filedialog.askdirectory(title="Select output directory for cut lists",initialdir=os.path.dirname(excel_file)) or os.path.dirname(excel_file)
            files=[]
            for (mat,thick),grp in cut_lists.items():
                safe="".join(c if c.isalnum() or c in (' ','_','-') else '_' for c in mat).strip().replace(' ','_')
                fname=f"cutlist_{safe}_{thick:g}mm.xlsx"; path=os.path.join(out_dir,fname)
                if pm: pm.export_to_excel(grp,path)
                else: grp.to_excel(path,index=False)
                files.append(fname)
            messagebox.showinfo("Cut lists generated",f"Generated {len(files)} file(s):\n" + "\n".join(files))
        except Exception as exc:
            messagebox.showerror("Error",str(exc))
    def init_inventory(self):
        if em is None:
            messagebox.showerror("Error","extended_management module not found."); return
        db_file=self.db_path.get()
        if not db_file:
            db_file=filedialog.asksaveasfilename(title="Select path for new inventory DB",defaultextension=".db",filetypes=[("SQLite DB","*.db"),("All files","*.*")])
            if not db_file: return
        try:
            em.init_inventory_db(db_file)
            self.db_path.set(db_file)
            messagebox.showinfo("Inventory initialised",f"Inventory database initialised at {db_file}")
        except Exception as exc:
            messagebox.showerror("Error",str(exc))
    def update_inventory(self):
        if em is None:
            messagebox.showerror("Error","extended_management module not found."); return
        db_file=self.db_path.get(); excel_file=self.excel_path.get()
        if not db_file:
            messagebox.showwarning("Missing DB","Please select or initialise an inventory database file."); return
        if not excel_file or not os.path.exists(excel_file):
            messagebox.showwarning("Missing file","Please select a valid Excel file first."); return
        try:
            df=pm.load_piece_list_from_excel(excel_file) if pm else pd.read_excel(excel_file)
            if df.empty:
                messagebox.showwarning("Empty file","The selected Excel file is empty."); return
            em.update_inventory_from_pieces(db_file,df)
            messagebox.showinfo("Inventory updated","Inventory has been updated based on the piece list.")
        except Exception as exc:
            messagebox.showerror("Error",str(exc))
    def view_inventory(self):
        if em is None:
            messagebox.showerror("Error","extended_management module not found."); return
        db_file=self.db_path.get()
        if not db_file:
            messagebox.showwarning("Missing DB","Please select or initialise an inventory database file."); return
        try:
            inv_df=em.get_inventory(db_file)
            if inv_df.empty:
                messagebox.showinfo("Inventory","No inventory records found."); return
            win=tk.Toplevel(self); win.title(f"Inventory: {os.path.basename(db_file)}"); win.geometry("500x300")
            text=tk.Text(win,wrap='none'); text.insert('1.0',inv_df.to_string(index=False)); text.configure(state='disabled')
            y=tk.Scrollbar(win,orient='vertical',command=text.yview); x=tk.Scrollbar(win,orient='horizontal',command=text.xview)
            text.configure(yscrollcommand=y.set,xscrollcommand=x.set)
            y.pack(side='right',fill='y'); x.pack(side='bottom',fill='x'); text.pack(side='left',fill='both',expand=True)
        except Exception as exc:
            messagebox.showerror("Error",str(exc))

def main():
    app=ProductionApp(); app.mainloop()
if __name__=="__main__": main()
