import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, Menu, ttk # Import ttk for Treeview
import os
import re
from PIL import Image, ImageTk # Import Pillow for image handling
import datetime # For status bar time
import shutil # For deleting non-empty directories

class CodeEditor:
    def __init__(self, master):
        self.master = master
        master.title("TkCode - Editor de Código")
        master.geometry("1200x800") # Increased height for bottom panel

        self.current_file = None
        self.project_root = None # To track the root of the open folder
        self.icons = {} # Dictionary to hold PhotoImage objects to prevent garbage collection

        # --- Main Layout Frames ---
        self.main_frame = tk.Frame(master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Icon Bar (Left Vertical Bar) ---
        self.icon_bar_frame = tk.Frame(self.main_frame, width=50, bg='#333333')
        self.icon_bar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.create_icon_bar()

        # --- Content Area Frame (holds sidebar, editor, and bottom panel) ---
        self.content_area_frame = tk.Frame(self.main_frame, bg='#21252b')
        self.content_area_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- Sidebar Frame (for File Explorer) ---
        self.sidebar_frame = tk.Frame(self.content_area_frame, width=250, bg='#282c34')
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1)) # Small gap
        self.sidebar_visible = True
        self.create_file_explorer()

        # --- Editor and Bottom Panel Wrapper ---
        self.editor_bottom_wrapper = tk.Frame(self.content_area_frame, bg='#21252b')
        self.editor_bottom_wrapper.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- Line Numbers Frame ---
        self.line_numbers_frame = tk.Frame(self.editor_bottom_wrapper, width=30, bg='#282c34')
        self.line_numbers_frame.pack(side=tk.LEFT, fill=tk.Y)

        # --- Editor Frame ---
        self.editor_area_frame = tk.Frame(self.editor_bottom_wrapper)
        self.editor_area_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # --- Área de texto (editor) ---
        self.text_area = scrolledtext.ScrolledText(
            self.editor_area_frame,
            wrap='none',
            bg='#21252b',
            fg='#abb2bf',
            insertbackground='#528bff',
            selectbackground='#3a3f4a',
            font=("Consolas", 12),
            undo=True,
            autoseparators=True,
            maxundo=-1
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)

        # --- Barras de desplazamiento (conectadas al área de texto) ---
        self.text_area.vbar.config(command=self.on_vertical_scroll)

        # --- Números de línea ---
        self.line_numbers_canvas = tk.Canvas(
            self.line_numbers_frame,
            width=30,
            bg='#282c34',
            highlightthickness=0
        )
        self.line_numbers_canvas.pack(side=tk.LEFT, fill=tk.Y)

        # --- Resaltado de Sintaxis (ejemplo para Python) ---
        self.text_area.tag_configure("keyword", foreground="#c678dd")
        self.text_area.tag_configure("string", foreground="#98c379")
        self.text_area.tag_configure("comment", foreground="#5c6370")
        self.text_area.tag_configure("function", foreground="#61afef")
        self.text_area.tag_configure("number", foreground="#d19a66")
        self.text_area.tag_configure("operator", foreground="#c678dd")

        self.keywords = ["import", "from", "def", "class", "return", "if", "else", "elif",
                         "for", "while", "break", "continue", "try", "except", "finally",
                         "with", "as", "True", "False", "None", "and", "or", "not", "in", "is"]

        # --- Eventos para actualizar números de línea y resaltar sintaxis ---
        self.text_area.bind("<KeyRelease>", self.on_key_release)
        self.text_area.bind("<MouseWheel>", self.on_vertical_scroll)
        self.text_area.bind("<Configure>", self.update_line_numbers)

        # --- Bottom Panel (Terminal, Problems, Output) ---
        self.bottom_panel_frame = tk.Frame(self.editor_bottom_wrapper, height=200, bg='#1e1e1e')
        self.bottom_panel_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.bottom_panel_visible = True
        self.create_bottom_panel()

        # --- Menú Superior ---
        self.create_menu()

        # --- Barra de estado (bottom bar like VS Code) ---
        self.status_bar = tk.Frame(master, bd=1, relief=tk.SUNKEN, bg='#007acc') # VS Code blue
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.create_status_bar()

        self.master.after(100, self.update_line_numbers) # Initial call after UI is fully packed and rendered
        self.master.after(100, self.update_status_bar) # Initial status bar update

    def load_icon(self, icon_name, size=(24, 24)):
        """Loads an icon image and returns a PhotoImage object."""
        try:
            image_path = os.path.join(os.path.dirname(__file__), "icons", f"{icon_name}.png") # Assumes 'icons' subfolder
            if not os.path.exists(image_path): # Fallback to root if not in subfolder
                 image_path = os.path.join(os.path.dirname(__file__), f"{icon_name}.png")

            img = Image.open(image_path)
            img = img.resize(size, Image.Resampling.LANCZOS)
            photo_img = ImageTk.PhotoImage(img)
            self.icons[icon_name] = photo_img # Store reference to prevent garbage collection
            return photo_img
        except FileNotFoundError:
            print(f"Advertencia: El icono '{icon_name}.png' no se encontró en 'icons/' ni en la carpeta raíz. Asegúrate de que existe.")
            # Return a blank image to avoid crashes if an icon is missing
            return ImageTk.PhotoImage(Image.new('RGBA', size, (0, 0, 0, 0)))
        except Exception as e:
            print(f"Error al cargar el icono '{icon_name}.png': {e}")
            return ImageTk.PhotoImage(Image.new('RGBA', size, (0, 0, 0, 0)))

    def create_icon_bar(self):
        """Creates the icon bar with placeholder buttons."""
        # It's recommended to put your icons in an 'icons' subfolder for better organization.
        # e.g., your_script_folder/icons/files.png

        # Files icon
        files_icon = self.load_icon("files")
        btn_files = tk.Button(self.icon_bar_frame, image=files_icon, command=self.toggle_sidebar,
                              bg='#333333', activebackground='#444444', bd=0, relief=tk.FLAT)
        btn_files.pack(pady=5, padx=5)

        # Search icon
        search_icon = self.load_icon("search")
        btn_search = tk.Button(self.icon_bar_frame, image=search_icon, command=lambda: self.show_message("Buscar"),
                               bg='#333333', activebackground='#444444', bd=0, relief=tk.FLAT)
        btn_search.pack(pady=5, padx=5)

        # Git icon
        git_icon = self.load_icon("git")
        btn_git = tk.Button(self.icon_bar_frame, image=git_icon, command=lambda: self.show_message("Control de Versiones"),
                            bg='#333333', activebackground='#444444', bd=0, relief=tk.FLAT)
        btn_git.pack(pady=5, padx=5)

        # Debug icon
        debug_icon = self.load_icon("debug")
        btn_debug = tk.Button(self.icon_bar_frame, image=debug_icon, command=lambda: self.show_message("Depurar"),
                              bg='#333333', activebackground='#444444', bd=0, relief=tk.FLAT)
        btn_debug.pack(pady=5, padx=5)

        # Extensions icon
        extensions_icon = self.load_icon("extensions")
        btn_extensions = tk.Button(self.icon_bar_frame, image=extensions_icon, command=lambda: self.show_message("Extensiones"),
                                  bg='#333333', activebackground='#444444', bd=0, relief=tk.FLAT)
        btn_extensions.pack(pady=5, padx=5)

        # Terminal icon (at bottom of icon bar)
        terminal_icon = self.load_icon("terminal")
        btn_terminal = tk.Button(self.icon_bar_frame, image=terminal_icon, command=self.toggle_bottom_panel,
                                  bg='#333333', activebackground='#444444', bd=0, relief=tk.FLAT)
        btn_terminal.pack(side=tk.BOTTOM, pady=5, padx=5)


    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_frame.pack_forget()
        else:
            self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1))
        self.sidebar_visible = not self.sidebar_visible
        self.master.after(10, self.update_line_numbers) # Update line numbers after layout change

    def create_file_explorer(self):
        """Creates the file explorer treeview and context menu."""
        file_explorer_header = tk.Label(self.sidebar_frame, text="EXPLORADOR", bg='#282c34', fg='#abb2bf', font=("Segoe UI", 9, "bold"), anchor=tk.W, padx=5)
        file_explorer_header.pack(fill=tk.X, pady=(0, 5))

        # Buttons for New File/Folder at the top of the explorer
        explorer_buttons_frame = tk.Frame(self.sidebar_frame, bg='#282c34')
        explorer_buttons_frame.pack(fill=tk.X, pady=(0, 5))

        new_file_icon = self.load_icon("new_file", size=(16,16)) # You'll need these icons
        new_folder_icon = self.load_icon("new_folder", size=(16,16))

        tk.Button(explorer_buttons_frame, image=new_file_icon, command=self.create_new_file, bd=0, bg='#282c34', activebackground='#3e4451', relief=tk.FLAT, width=20, height=20).pack(side=tk.LEFT, padx=2)
        tk.Button(explorer_buttons_frame, image=new_folder_icon, command=self.create_new_folder, bd=0, bg='#282c34', activebackground='#3e4451', relief=tk.FLAT, width=20, height=20).pack(side=tk.LEFT, padx=2)


        # Define style for dark theme for ttk.Treeview
        style = ttk.Style()
        style.theme_use("clam") # 'clam' or 'alt' or 'default' work well for customization

        style.configure("Treeview",
                        background="#282c34",        # Background of the treeview widget
                        foreground="#abb2bf",        # Text color
                        fieldbackground="#282c34",   # Background of the actual list area
                        borderwidth=0,
                        rowheight=22) # Adjust row height for better spacing

        style.map('Treeview',
                  background=[('selected', '#007acc')], # Background when selected
                  foreground=[('selected', 'white')])  # Text color when selected

        style.configure("Treeview.Heading",
                        background="#21252b",
                        foreground="#abb2bf",
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview.Heading",
                  background=[('active', '#3e4451')])


        self.tree = ttk.Treeview(self.sidebar_frame, show='tree', selectmode='browse',
                                 height=20) # No specific style name needed here as we configured "Treeview" directly
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Context menu for file explorer (right-click)
        self.explorer_context_menu = Menu(self.master, tearoff=0)
        self.explorer_context_menu.add_command(label="Nuevo archivo", command=self.create_new_file)
        self.explorer_context_menu.add_command(label="Nueva carpeta", command=self.create_new_folder)
        self.explorer_context_menu.add_separator()
        self.explorer_context_menu.add_command(label="Eliminar", command=self.delete_explorer_item)

        self.tree.bind("<Button-3>", self.show_explorer_context_menu) # Right-click
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.open_file_from_explorer) # Double-click to open

        # Load an initial directory (e.g., current working directory)
        self.open_folder(os.getcwd())


    def open_folder(self, path):
        if not path: # Handle cancel dialog
            return
        self.project_root = path
        self.master.title(f"TkCode - {os.path.basename(path)}")
        self.populate_tree(self.project_root)
        self.status_bar_file_info_label.config(text=f"Carpeta: {os.path.basename(path)}")

    def populate_tree(self, root_path):
        """Populates the Treeview with files and folders."""
        for iid in self.tree.get_children():
            self.tree.delete(iid) # Clear existing items

        # root node for the project folder
        folder_name = os.path.basename(root_path)
        root_node = self.tree.insert('', 'end', text=folder_name, open=True, values=[root_path])
        self._populate_tree_recursive(root_node, root_path)

    def _populate_tree_recursive(self, parent_node, path):
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                folder_node = self.tree.insert(parent_node, 'end', text=item, open=False, values=[item_path, 'folder'])
                # Add a dummy child to enable the folder expansion icon
                self.tree.insert(folder_node, 'end', text="dummy")
                self.tree.item(folder_node, tags=('folder',)) # Tag for styling or context
            elif os.path.isfile(item_path):
                file_node = self.tree.insert(parent_node, 'end', text=item, values=[item_path, 'file'])
                self.tree.item(file_node, tags=('file',)) # Tag for styling or context
        self.tree.bind('<<TreeviewOpen>>', self.on_folder_open)

    def on_folder_open(self, event):
        """Dynamically loads subfolders when a folder is expanded."""
        item_id = self.tree.focus()
        item_data = self.tree.item(item_id, "values")
        if not item_data or item_data[1] != 'folder':
            return

        folder_path = item_data[0]
        # Remove dummy child
        if self.tree.get_children(item_id) and self.tree.item(self.tree.get_children(item_id)[0])['text'] == "dummy":
            self.tree.delete(self.tree.get_children(item_id)[0])
        else:
            return # Already loaded or no dummy child

        # Load actual children
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                new_folder_node = self.tree.insert(item_id, 'end', text=item, open=False, values=[item_path, 'folder'])
                self.tree.insert(new_folder_node, 'end', text="dummy") # Add new dummy for its children
                self.tree.item(new_folder_node, tags=('folder',))
            elif os.path.isfile(item_path):
                new_file_node = self.tree.insert(item_id, 'end', text=item, values=[item_path, 'file'])
                self.tree.item(new_file_node, tags=('file',))

    def show_explorer_context_menu(self, event):
        """Displays the context menu for the file explorer."""
        # Identify the item under the cursor, so context menu actions apply to it
        self.tree.identify_row(event.y)
        try:
            self.explorer_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.explorer_context_menu.grab_release()

    def create_new_file(self):
        selected_item = self.tree.focus()
        base_path = self.project_root # Default to project root if nothing is selected

        if selected_item:
            item_data = self.tree.item(selected_item, "values")
            if item_data:
                if item_data[1] == 'file': # If a file is selected, use its parent directory
                    base_path = os.path.dirname(item_data[0])
                else: # If a folder is selected, use that folder
                    base_path = item_data[0]
        
        if not base_path or not os.path.isdir(base_path):
            messagebox.showwarning("Advertencia", "No se puede crear un archivo. Por favor, abre una carpeta o selecciona una carpeta válida en el explorador.")
            return

        new_file_name = tk.simpledialog.askstring("Nuevo Archivo", "Nombre del nuevo archivo:", parent=self.master)
        if new_file_name:
            new_file_path = os.path.join(base_path, new_file_name)
            try:
                with open(new_file_path, 'w') as f:
                    f.write("") # Create empty file
                self.populate_tree(self.project_root) # Refresh tree
                self.status_bar_file_info_label.config(text=f"Archivo '{new_file_name}' creado.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear el archivo: {e}")

    def create_new_folder(self):
        selected_item = self.tree.focus()
        base_path = self.project_root # Default to project root if nothing is selected

        if selected_item:
            item_data = self.tree.item(selected_item, "values")
            if item_data:
                if item_data[1] == 'file': # If a file is selected, use its parent directory
                    base_path = os.path.dirname(item_data[0])
                else: # If a folder is selected, use that folder
                    base_path = item_data[0]

        if not base_path or not os.path.isdir(base_path):
            messagebox.showwarning("Advertencia", "No se puede crear una carpeta. Por favor, abre una carpeta o selecciona una carpeta válida en el explorador.")
            return

        new_folder_name = tk.simpledialog.askstring("Nueva Carpeta", "Nombre de la nueva carpeta:", parent=self.master)
        if new_folder_name:
            new_folder_path = os.path.join(base_path, new_folder_name)
            try:
                os.makedirs(new_folder_path)
                self.populate_tree(self.project_root) # Refresh tree
                self.status_bar_file_info_label.config(text=f"Carpeta '{new_folder_name}' creada.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear la carpeta: {e}")

    def delete_explorer_item(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showinfo("Eliminar", "Selecciona un archivo o carpeta para eliminar.")
            return

        item_data = self.tree.item(selected_item, "values")
        if not item_data: # If selected item is the root of the treeview (e.g. "my_project_folder")
            messagebox.showwarning("Advertencia", "No puedes eliminar la raíz del proyecto directamente.")
            return

        item_path = item_data[0]
        item_type = item_data[1]
        item_name = os.path.basename(item_path)

        if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar '{item_name}' ({item_type})? Esta acción es irreversible."):
            try:
                if item_type == 'file':
                    os.remove(item_path)
                elif item_type == 'folder':
                    # Use shutil.rmtree for non-empty directories, be cautious!
                    shutil.rmtree(item_path)
                self.populate_tree(self.project_root) # Refresh tree
                self.status_bar_file_info_label.config(text=f"'{item_name}' eliminado.")
            except OSError as e:
                messagebox.showerror("Error de Eliminación", f"No se pudo eliminar '{item_name}': {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error inesperado al eliminar: {e}")


    def on_tree_select(self, event):
        selected_item = self.tree.focus()
        if selected_item:
            item_data = self.tree.item(selected_item, "values")
            if item_data:
                # Update status bar or show info about selected item
                # No need to update status bar on select, only on opening
                pass


    def open_file_from_explorer(self, event):
        selected_item = self.tree.focus()
        if not selected_item:
            return

        item_data = self.tree.item(selected_item, "values")
        if item_data and item_data[1] == 'file':
            filepath = item_data[0]
            if os.path.exists(filepath) and os.path.isfile(filepath):
                self.open_file_by_path(filepath)
            else:
                messagebox.showerror("Error", "El archivo no existe o no es un archivo válido.")

    def open_file_by_path(self, filepath):
        self.text_area.delete(1.0, tk.END)
        try:
            with open(filepath, "r", encoding="utf-8") as input_file:
                text = input_file.read()
                self.text_area.insert(tk.END, text)
            self.current_file = filepath
            self.master.title(f"TkCode - {os.path.basename(filepath)}")
            self.status_bar_file_info_label.config(text=f"Archivo: {os.path.basename(filepath)}") # Update file info on status bar
            self.update_status_bar() # Update other status bar elements
            self.update_line_numbers()
            self.highlight_syntax()
        except Exception as e:
            messagebox.showerror("Error al abrir archivo", f"No se pudo abrir el archivo:\n{e}")

    def create_bottom_panel(self):
        """Creates the bottom panel with tabs for Terminal, Problems, Output."""
        # Tab control for the bottom panel
        self.bottom_notebook = ttk.Notebook(self.bottom_panel_frame)
        self.bottom_notebook.pack(fill=tk.BOTH, expand=True)

        # Apply dark theme to notebook tabs
        style = ttk.Style()
        style.configure("TNotebook", background="#1e1e1e", borderwidth=0)
        style.configure("TNotebook.Tab", background="#3e4451", foreground="#abb2bf", borderwidth=0, padding=[5,2])
        style.map("TNotebook.Tab", background=[("selected", "#1e1e1e")], foreground=[("selected", "white")])


        # Terminal Tab
        self.terminal_frame = tk.Frame(self.bottom_notebook, bg='#1e1e1e')
        self.bottom_notebook.add(self.terminal_frame, text="Terminal")
        self.create_terminal()

        # Problems Tab (placeholder)
        self.problems_frame = tk.Frame(self.bottom_notebook, bg='#1e1e1e')
        self.bottom_notebook.add(self.problems_frame, text="Problemas")
        tk.Label(self.problems_frame, text="No hay problemas detectados (por ahora)", bg='#1e1e1e', fg='white').pack(pady=20)

        # Output Tab (placeholder)
        self.output_frame = tk.Frame(self.bottom_notebook, bg='#1e1e1e')
        self.bottom_notebook.add(self.output_frame, text="Salida")
        tk.Label(self.output_frame, text="Aquí se mostrará la salida del programa (futura característica)", bg='#1e1e1e', fg='white').pack(pady=20)

    def create_terminal(self):
        """Creates a simple text-based terminal."""
        self.terminal_output = scrolledtext.ScrolledText(
            self.terminal_frame,
            wrap='word',
            bg='#1e1e1e',
            fg='#d4d4d4', # Light grey for terminal text
            insertbackground='#d4d4d4',
            selectbackground='#007acc',
            font=("Consolas", 10),
            state='disabled', # Start as disabled to prevent direct typing
            bd=0, # No border
            relief=tk.FLAT # No relief
        )
        self.terminal_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.terminal_output.tag_configure("info", foreground="yellow")
        self.terminal_output.tag_configure("error", foreground="red")
        self.terminal_output.tag_configure("user_input", foreground="#528bff") # Blue for user input

        terminal_input_frame = tk.Frame(self.terminal_frame, bg='#1e1e1e')
        terminal_input_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        tk.Label(terminal_input_frame, text=">", bg='#1e1e1e', fg='#d4d4d4').pack(side=tk.LEFT)
        self.terminal_input = tk.Entry(
            terminal_input_frame,
            bg='#3c3c3c',
            fg='#d4d4d4',
            insertbackground='#d4d4d4',
            font=("Consolas", 10),
            bd=0
        )
        self.terminal_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.terminal_input.bind("<Return>", self.execute_terminal_command)

        self.print_to_terminal("Bienvenido a TkCode Terminal. Escribe 'ayuda' para ver comandos.", tag="info")

    def print_to_terminal(self, message, tag=None):
        """Appends a message to the terminal output."""
        self.terminal_output.config(state='normal') # Enable editing
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
        if tag:
            self.terminal_output.insert(tk.END, timestamp + message + "\n", tag)
        else:
            self.terminal_output.insert(tk.END, timestamp + message + "\n")
        self.terminal_output.see(tk.END) # Scroll to end
        self.terminal_output.config(state='disabled') # Disable editing

    def execute_terminal_command(self, event=None):
        command = self.terminal_input.get().strip()
        self.print_to_terminal(f"> {command}", tag="user_input") # Tag user input
        self.terminal_input.delete(0, tk.END) # Clear input

        if command.lower() == "ayuda":
            self.print_to_terminal("Comandos disponibles:\n - ayuda: Muestra esta ayuda.\n - hola: Saluda.\n - clear: Limpia la terminal.\n - info: Muestra info del editor.\n - ls: Lista archivos (simulado).")
        elif command.lower() == "hola":
            self.print_to_terminal("¡Hola desde TkCode!")
        elif command.lower() == "clear":
            self.terminal_output.config(state='normal')
            self.terminal_output.delete(1.0, tk.END)
            self.terminal_output.config(state='disabled')
            self.print_to_terminal("Terminal limpiada.", tag="info")
        elif command.lower() == "info":
            self.print_to_terminal("TkCode v0.1 - Editor de código simple con Tkinter.")
            self.print_to_terminal("Creado por tu asistente IA.")
        elif command.lower() == "ls":
            if self.project_root and os.path.isdir(self.project_root):
                self.print_to_terminal(f"Contenido de '{os.path.basename(self.project_root)}':")
                for item in sorted(os.listdir(self.project_root)): # Sort for readability
                    item_path = os.path.join(self.project_root, item)
                    if os.path.isdir(item_path):
                        self.print_to_terminal(f" - {item}/", tag="info") # Indicate folders
                    else:
                        self.print_to_terminal(f" - {item}")
            else:
                self.print_to_terminal("No hay una carpeta abierta para listar.", tag="error")
        else:
            self.print_to_terminal(f"Comando no reconocido: '{command}'", tag="error")


    def toggle_bottom_panel(self):
        if self.bottom_panel_visible:
            self.bottom_panel_frame.pack_forget()
        else:
            self.bottom_panel_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.bottom_panel_visible = not self.bottom_panel_visible
        self.master.after(10, self.update_line_numbers) # Update line numbers after layout change


    def create_status_bar(self):
        """Creates the detailed status bar at the bottom."""
        # Left section (File info)
        self.status_bar_file_info_label = tk.Label(self.status_bar, text="Listo", bg='#007acc', fg='white', padx=10)
        self.status_bar_file_info_label.pack(side=tk.LEFT, padx=(5, 0))

        # Git status (placeholder)
        git_icon = self.load_icon("git", size=(16,16)) # Smaller git icon for status bar
        self.status_bar_git_label = tk.Label(self.status_bar, image=git_icon, text=" main*", compound=tk.LEFT, bg='#007acc', fg='white', padx=5)
        self.status_bar_git_label.image = git_icon # Keep reference
        self.status_bar_git_label.pack(side=tk.LEFT, padx=(10, 0))

        # Problems/Errors (placeholder)
        info_icon = self.load_icon("info", size=(16,16)) # Using a generic info icon
        self.status_bar_problems_label = tk.Label(self.status_bar, image=info_icon, text=" 0 problemas", compound=tk.LEFT, bg='#007acc', fg='white', padx=5)
        self.status_bar_problems_label.image = info_icon # Keep reference
        self.status_bar_problems_label.pack(side=tk.LEFT, padx=(10, 0))


        # Right section (Language, Indentation, Encoding)
        self.status_bar_encoding_label = tk.Label(self.status_bar, text="UTF-8", bg='#007acc', fg='white', padx=10)
        self.status_bar_encoding_label.pack(side=tk.RIGHT, padx=(0, 5))

        self.status_bar_indent_label = tk.Label(self.status_bar, text="Espacios: 4", bg='#007acc', fg='white', padx=10)
        self.status_bar_indent_label.pack(side=tk.RIGHT, padx=(0, 5))

        self.status_bar_lang_label = tk.Label(self.status_bar, text="Texto Plano", bg='#007acc', fg='white', padx=10)
        self.status_bar_lang_label.pack(side=tk.RIGHT, padx=(0, 5))

        self.text_area.bind("<KeyRelease>", self.update_status_bar) # Bind to key release
        self.text_area.bind("<<Modified>>", self.update_status_bar_modified_flag) # Bind to text modification

    def update_status_bar_modified_flag(self, event=None):
        # This function exists solely to clear the Tkinter modified flag
        # We also call update_status_bar on KeyRelease for full updates
        self.text_area.edit_modified(False)


    def update_status_bar(self, event=None):
        # Update Line and Column
        cursor_pos = self.text_area.index(tk.INSERT)
        line, col = map(int, cursor_pos.split('.'))
        self.status_bar_file_info_label.config(text=f"Ln {line}, Col {col}")

        # Update Language (basic, could be improved based on file extension)
        if self.current_file:
            ext = os.path.splitext(self.current_file)[1].lower()
            lang = "Texto Plano"
            if ext == ".py": lang = "Python"
            elif ext == ".js": lang = "JavaScript"
            elif ext == ".html": lang = "HTML"
            elif ext == ".css": lang = "CSS"
            elif ext == ".json": lang = "JSON"
            elif ext == ".xml": lang = "XML"
            self.status_bar_lang_label.config(text=lang)
        else:
            self.status_bar_lang_label.config(text="Texto Plano")

        # You would implement actual Git status, problem counting here
        # For now, they remain static.


    def create_menu(self):
        menubar = Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Nuevo Archivo", command=self.new_file)
        file_menu.add_command(label="Nueva Carpeta", command=self.create_new_folder) # Added to menu
        file_menu.add_separator()
        file_menu.add_command(label="Abrir Archivo...", command=self.open_file)
        file_menu.add_command(label="Abrir Carpeta...", command=lambda: self.open_folder(filedialog.askdirectory()))
        file_menu.add_separator()
        file_menu.add_command(label="Guardar", command=self.save_file)
        file_menu.add_command(label="Guardar como...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.master.quit)

        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Editar", menu=edit_menu)
        edit_menu.add_command(label="Deshacer", command=self.text_area.edit_undo)
        edit_menu.add_command(label="Rehacer", command=self.text_area.edit_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cortar", command=lambda: self.text_area.event_generate("<<Cut>>"))
        edit_menu.add_command(label="Copiar", command=lambda: self.text_area.event_generate("<<Copy>>"))
        edit_menu.add_command(label="Pegar", command=lambda: self.text_area.event_generate("<<Paste>>"))

        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ver", menu=view_menu)
        view_menu.add_command(label="Mostrar/Ocultar Barra Lateral", command=self.toggle_sidebar)
        view_menu.add_command(label="Mostrar/Ocultar Panel Inferior", command=self.toggle_bottom_panel)


    def new_file(self):
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.master.title("TkCode - Sin título")
        self.update_status_bar() # Update all status bar info
        self.update_line_numbers()

    def open_file(self):
        filepath = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"),
                       ("Archivos de Python", "*.py"),
                       ("Archivos de JavaScript", "*.js"),
                       ("Archivos CSS", "*.css"),
                       ("Archivos HTML", "*.html"),
                       ("Todos los archivos", "*.*")]
        )
        if not filepath:
            return
        self.open_file_by_path(filepath)


    def save_file(self):
        if self.current_file:
            try:
                with open(self.current_file, "w", encoding="utf-8") as output_file:
                    text = self.text_area.get(1.0, tk.END)
                    output_file.write(text)
                self.status_bar_file_info_label.config(text=f"Guardado: {os.path.basename(self.current_file)}")
                self.update_status_bar() # Update new status bar
            except Exception as e:
                messagebox.showerror("Error al guardar archivo", f"No se pudo guardar el archivo:\n{e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"),
                       ("Archivos de Python", "*.py"),
                       ("Archivos de JavaScript", "*.js"),
                       ("Archivos CSS", "*.css"),
                       ("Archivos HTML", "*.html"),
                       ("Todos los archivos", "*.*")]
        )
        if not filepath:
            return
        self.current_file = filepath
        self.save_file()
        self.master.title(f"TkCode - {os.path.basename(filepath)}")


    def on_key_release(self, event=None):
        self.update_line_numbers()
        self.highlight_syntax()
        self.update_status_bar() # Update status bar on key release


    def on_vertical_scroll(self, *args):
        self.line_numbers_canvas.yview_moveto(args[0])
        self.update_line_numbers()


    def update_line_numbers(self, event=None):
        self.line_numbers_canvas.delete("all")

        first_visible_char_index = self.text_area.index("@0,0")
        # Ensure winfo_height() is available; if not, use a default
        editor_height = self.text_area.winfo_height()
        if editor_height <= 1: # If widget not yet rendered or too small
            editor_height = 20 # Assume a minimum height for initial calculation

        last_visible_char_index = self.text_area.index("@0,%d" % editor_height)

        try:
            first_line_num = int(float(first_visible_char_index))
        except ValueError:
            first_line_num = 1

        try:
            last_line_num = int(float(last_visible_char_index))
        except ValueError:
            last_line_num = first_line_num

        if self.text_area.compare("end-1c", "==", "1.0"):
             first_line_num = 1
             last_line_num = 1

        y_offset_info = self.text_area.dlineinfo(f"{first_line_num}.0")
        if y_offset_info:
            y_offset = y_offset_info[1]
        else:
            y_offset = 0

        for i in range(first_line_num, last_line_num + 3): # Draw a few extra lines for smooth scrolling
            current_line_index = f"{i}.0"
            dline_info = self.text_area.dlineinfo(current_line_index)

            if dline_info is None:
                break

            y_coord = dline_info[1] - y_offset
            self.line_numbers_canvas.create_text(
                5, y_coord, anchor="nw",
                text=str(i),
                fill="#6a737d",
                font=("Consolas", 10)
            )

        self.line_numbers_canvas.yview_moveto(self.text_area.yview()[0])


    def highlight_syntax(self, event=None):
        self.text_area.edit_separator()

        for tag in self.text_area.tag_names():
            # Exclude internal Tkinter tags and our custom terminal tags
            if tag not in ["sel", "undo", "redo", "mark", "info", "error", "user_input"]:
                self.text_area.tag_remove(tag, "1.0", tk.END)

        text = self.text_area.get("1.0", tk.END)
        lines = text.splitlines()

        for i, line in enumerate(lines):
            line_num = i + 1

            for match in re.finditer(r"(#.*)", line):
                start = f"{line_num}.{match.start(1)}"
                end = f"{line_num}.{match.end(1)}"
                self.text_area.tag_add("comment", start, end)

            for match in re.finditer(r"(\".*?\"|\'.*?\')", line):
                start = f"{line_num}.{match.start(1)}"
                end = f"{line_num}.{match.end(1)}"
                self.text_area.tag_add("string", start, end)

            for match in re.finditer(r"\b\d+\b", line):
                start = f"{line_num}.{match.start(0)}"
                end = f"{line_num}.{match.end(0)}"
                self.text_area.tag_add("number", start, end)

            for match in re.finditer(r"(\+|\-|\*|\/|=|\!|\<|\>|&|\||\^|%|\~|\.|\:|\,)", line):
                 start = f"{line_num}.{match.start(1)}"
                 end = f"{line_num}.{match.end(1)}"
                 self.text_area.tag_add("operator", start, end)

            for keyword in self.keywords:
                for match in re.finditer(r"\b" + re.escape(keyword) + r"\b", line):
                    start = f"{line_num}.{match.start(0)}"
                    end = f"{line_num}.{match.end(0)}"
                    self.text_area.tag_add("keyword", start, end)

            for match in re.finditer(r"\bdef\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", line):
                func_name_start = match.start(1)
                func_name_end = match.end(1)
                start = f"{line_num}.{func_name_start}"
                end = f"{line_num}.{func_name_end}"
                self.text_area.tag_add("function", start, end)

        self.text_area.edit_separator()

    def show_message(self, feature_name):
        """Placeholder function to show message when an icon is clicked."""
        self.status_bar_file_info_label.config(text=f"Icono clickeado: {feature_name} (funcionalidad no implementada)")
        messagebox.showinfo("Característica", f"Has clickeado el icono de {feature_name}. La funcionalidad completa no está implementada en esta versión básica.")


# --- Ejecutar la aplicación ---
if __name__ == "__main__":
    root = tk.Tk()
    editor = CodeEditor(root)
    root.mainloop()