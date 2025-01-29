import json
import customtkinter as ctk
from tkinter import ttk, messagebox

# Load initial blacklist from file
BLACKLIST_FILE = "blacklist.db"
with open(BLACKLIST_FILE, "r") as file:
    blacklist = json.load(file)

class BanManagementTool(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ban Management Tool")
        self.geometry("700x500")

        # Tabs
        self.tab_control = ttk.Notebook(self)
        self.tab_view = ttk.Frame(self.tab_control)
        self.tab_add_remove = ttk.Frame(self.tab_control)

        self.tab_control.add(self.tab_view, text="View Bans")
        self.tab_control.add(self.tab_add_remove, text="Add/Remove Bans")
        self.tab_control.pack(expand=1, fill="both")

        # View Bans Tab
        self.create_view_tab()

        # Add/Remove Bans Tab
        self.create_add_remove_tab()

    def create_view_tab(self):
        self.tree = ttk.Treeview(self.tab_view, columns=("Type", "ID", "Value"), show="headings")
        self.tree.heading("Type", text="Type")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Value", text="Value")
        self.tree.pack(expand=1, fill="both", padx=10, pady=10)

        self.refresh_view()

    def create_add_remove_tab(self):
        # Add ban panel
        ctk.CTkLabel(self.tab_add_remove, text="Ban Type:").grid(row=0, column=0, pady=5, padx=5)
        self.ban_type_var = ctk.CTkComboBox(self.tab_add_remove, values=["PlayStation account IDs", "Discord user IDs"])
        self.ban_type_var.grid(row=0, column=1, pady=5, padx=5)

        ctk.CTkLabel(self.tab_add_remove, text="Ban ID:").grid(row=1, column=0, pady=5, padx=5)
        self.ban_id_entry = ctk.CTkEntry(self.tab_add_remove)
        self.ban_id_entry.grid(row=1, column=1, pady=5, padx=5)

        ctk.CTkLabel(self.tab_add_remove, text="Ban Value:").grid(row=2, column=0, pady=5, padx=5)
        self.ban_value_entry = ctk.CTkEntry(self.tab_add_remove)
        self.ban_value_entry.grid(row=2, column=1, pady=5, padx=5)

        ctk.CTkButton(self.tab_add_remove, text="Add Ban", command=self.add_ban).grid(row=3, column=0, pady=10, padx=5)
        ctk.CTkButton(self.tab_add_remove, text="Remove Ban", command=self.remove_ban).grid(row=3, column=1, pady=10, padx=5)

    def refresh_view(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for ban_type, items in blacklist.items():
            for item in items:
                for ban_id, ban_value in item.items():
                    self.tree.insert("", "end", values=(ban_type, ban_id, ban_value))

    def add_ban(self):
        ban_type = self.ban_type_var.get()
        ban_id = self.ban_id_entry.get()
        ban_value = self.ban_value_entry.get()

        if not ban_type or not ban_id or not ban_value:
            messagebox.showerror("Error", "All fields must be filled out.")
            return

        new_ban = {ban_id: ban_value}
        if ban_type in blacklist:
            blacklist[ban_type].append(new_ban)
        else:
            blacklist[ban_type] = [new_ban]

        self.save_blacklist()
        self.refresh_view()
        messagebox.showinfo("Success", "Ban added successfully.")

    def remove_ban(self):
        ban_type = self.ban_type_var.get()
        ban_id = self.ban_id_entry.get()

        if not ban_type or not ban_id:
            messagebox.showerror("Error", "Ban type and ID must be filled out to remove a ban.")
            return

        if ban_type in blacklist:
            for item in blacklist[ban_type]:
                if ban_id in item:
                    blacklist[ban_type].remove(item)
                    self.save_blacklist()
                    self.refresh_view()
                    messagebox.showinfo("Success", "Ban removed successfully.")
                    return

        messagebox.showerror("Error", "Ban not found.")

    def save_blacklist(self):
        with open(BLACKLIST_FILE, "w") as file:
            json.dump(blacklist, file, indent=4)

if __name__ == "__main__":
    app = BanManagementTool()
    app.mainloop()
