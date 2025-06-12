import tkinter as tk
from tkinter import ttk, messagebox
from database import connect_to_db, get_projects, get_cycle_ids, fetch_data

# Function to fetch users for dropdown
def get_users():
    users = fetch_data("SELECT name FROM users")
    return [user[0] for user in users]

# Function to add a user
def add_user(name, role, email):
    conn = connect_to_db()
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,))
        if cursor.fetchone()[0] > 0:
            messagebox.showerror("Error", "This email is already registered!")
            return

        # Insert new user if email is unique
        cursor.execute("INSERT INTO users (name, role, email) VALUES (?, ?, ?)", (name, role, email))
        conn.commit()
        messagebox.showinfo("Success", "User added successfully!")
    
    except Exception as e:
        messagebox.showerror("Error", str(e))
    
    finally:
        conn.close()

# Function to add a task
def add_task(task_name, project_id, cycle_id, start_date, end_date, assigned_to):
    conn = connect_to_db()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (task_name, project_id, cycle_id, start_date, end_date, assigned_to) VALUES (?, ?, ?, ?, ?, ?)",
            (task_name, project_id, cycle_id, start_date, end_date, assigned_to),
        )
        conn.commit()
        messagebox.showinfo("Success", "Task added successfully!")
        refresh_tasks()
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        conn.close()

# UI setup
root = tk.Tk()
root.title("Project Management")
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# Users Tab
user_frame = ttk.Frame(notebook)
notebook.add(user_frame, text="Users")

ttk.Label(user_frame, text="Name:").grid(row=0, column=0)
name_entry = ttk.Entry(user_frame)
name_entry.grid(row=0, column=1)

ttk.Label(user_frame, text="Role:").grid(row=1, column=0)
role_entry = ttk.Entry(user_frame)
role_entry.grid(row=1, column=1)

ttk.Label(user_frame, text="Email:").grid(row=2, column=0)
email_entry = ttk.Entry(user_frame)
email_entry.grid(row=2, column=1)

ttk.Button(user_frame, text="Add User", command=lambda: add_user(name_entry.get(), role_entry.get(), email_entry.get())).grid(row=3, columnspan=2)

# Projects Tab
project_frame = ttk.Frame(notebook)
notebook.add(project_frame, text="Projects")

ttk.Label(project_frame, text="Projects:").pack()
project_tree = ttk.Treeview(project_frame, columns=("ID", "Name"), show="headings")
project_tree.heading("ID", text="ID")
project_tree.heading("Name", text="Project Name")
project_tree.pack(expand=True, fill="both")

# Tasks Tab
task_frame = ttk.Frame(notebook)
notebook.add(task_frame, text="Tasks")

ttk.Label(task_frame, text="Task Name:").grid(row=0, column=0)
task_name_entry = ttk.Entry(task_frame)
task_name_entry.grid(row=0, column=1)

ttk.Label(task_frame, text="Project:").grid(row=1, column=0)
project_var = tk.StringVar()
project_dropdown = ttk.Combobox(task_frame, textvariable=project_var,
                                 values=[f"{p[0]} - {p[1]}" for p in get_projects()])
project_dropdown.grid(row=1, column=1)

ttk.Label(task_frame, text="Cycle:").grid(row=2, column=0)
cycle_var = tk.StringVar()
cycle_dropdown = ttk.Combobox(task_frame, textvariable=cycle_var)
cycle_dropdown.grid(row=2, column=1)

def load_cycles(event=None):
    if " - " not in project_var.get():
        return
    pid = project_var.get().split(" - ")[0]
    cycles = get_cycle_ids(pid)
    cycle_dropdown['values'] = cycles if cycles else ["No Cycles Available"]
    if cycles:
        cycle_dropdown.current(0)
    else:
        cycle_dropdown.set("No Cycles Available")

project_dropdown.bind("<<ComboboxSelected>>", load_cycles)
load_cycles()

ttk.Label(task_frame, text="Start Date:").grid(row=3, column=0)
start_date_entry = ttk.Entry(task_frame)
start_date_entry.grid(row=3, column=1)

ttk.Label(task_frame, text="End Date:").grid(row=4, column=0)
end_date_entry = ttk.Entry(task_frame)
end_date_entry.grid(row=4, column=1)

ttk.Label(task_frame, text="Assigned To:").grid(row=5, column=0)
assigned_to_var = tk.StringVar()
assigned_to_dropdown = ttk.Combobox(task_frame, textvariable=assigned_to_var, values=get_users())
assigned_to_dropdown.grid(row=5, column=1)

ttk.Button(task_frame, text="Add Task", command=lambda: add_task(
    task_name_entry.get(),
    project_var.get().split(" - ")[0] if " - " in project_var.get() else project_var.get(),
    cycle_var.get(),
    start_date_entry.get(),
    end_date_entry.get(),
    assigned_to_var.get(),
)).grid(row=6, columnspan=2)

task_tree = ttk.Treeview(task_frame, columns=("name", "start", "end", "user"), show="headings")
task_tree.heading("name", text="Task")
task_tree.heading("start", text="Start")
task_tree.heading("end", text="End")
task_tree.heading("user", text="Assigned To")
task_tree.grid(row=7, column=0, columnspan=2, pady=5)

def refresh_tasks():
    if " - " not in project_var.get():
        return
    pid = project_var.get().split(" - ")[0]
    cid = cycle_var.get()
    conn = connect_to_db()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT task_name, start_date, end_date, assigned_to FROM tasks WHERE project_id = ? AND cycle_id = ?",
            (pid, cid),
        )
        rows = cursor.fetchall()
        for item in task_tree.get_children():
            task_tree.delete(item)
        for r in rows:
            task_tree.insert("", tk.END, values=r)
    finally:
        conn.close()

project_dropdown.bind("<<ComboboxSelected>>", lambda e: [load_cycles(), refresh_tasks()])
cycle_dropdown.bind("<<ComboboxSelected>>", lambda e: refresh_tasks())
refresh_tasks()

root.mainloop()
