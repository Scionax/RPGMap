import os
import tkinter as tk
from tkinter import filedialog, messagebox

from .layer import Layer
from .brush import BrushItem


class FileMenu:
    """Tkinter menu bar handling file and session actions."""

    def __init__(self, app, tk_root: tk.Tk):
        self.app = app
        self.tk_root = tk_root
        self.menubar = tk.Menu(tk_root)
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.update_file_menu()
        self.menubar.add_cascade(label='File', menu=self.file_menu)

        mode_menu = tk.Menu(self.menubar, tearoff=0)
        mode_menu.add_command(label='Layer 1', command=lambda: app.set_mode(1))
        mode_menu.add_command(label='Layer 2', command=lambda: app.set_mode(2))
        mode_menu.add_command(label='Layer 3', command=lambda: app.set_mode(3))
        mode_menu.add_command(label='Play', command=lambda: app.set_mode(4))
        self.menubar.add_cascade(label='Mode', menu=mode_menu)

        map_menu = tk.Menu(self.menubar, tearoff=0)
        map_menu.add_command(label='Preferences', command=self.open_preferences_dialog)
        map_menu.add_command(label='Save Map', command=self.open_save_map_dialog)
        map_menu.add_command(label='Load Map', command=self.open_load_map_dialog)
        map_menu.add_command(label='Clear Map', command=self.clear_map_prompt)
        self.menubar.add_cascade(label='Map', menu=map_menu)

        session_menu = tk.Menu(self.menubar, tearoff=0)
        session_menu.add_command(label='Save State', command=self.open_save_state_dialog)
        session_menu.add_command(label='Load State', command=self.open_load_state_dialog)
        session_menu.add_command(label='Clear State', command=self.clear_state_prompt)
        self.menubar.add_cascade(label='Session', menu=session_menu)

        tk_root.config(menu=self.menubar)

    # ---------------- Menu update -----------------
    def update_file_menu(self) -> None:
        self.file_menu.delete(0, tk.END)
        label = 'Hide UI' if self.app.show_ui else 'Show UI'
        self.file_menu.add_command(label=label, command=self.app.toggle_ui)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Exit', command=self.app.exit_program)

    # ---------------- Menu callbacks -----------------
    def open_preferences_dialog(self) -> None:
        dlg = tk.Toplevel(self.tk_root)
        dlg.title('Preferences')
        dlg.grab_set()

        tk.Label(dlg, text='Zoom:').grid(row=0, column=0, sticky='e')
        zoom_var = tk.DoubleVar(value=self.app.zoom)
        tk.Entry(dlg, textvariable=zoom_var).grid(row=0, column=1)

        tk.Label(dlg, text='Pan speed:').grid(row=1, column=0, sticky='e')
        pan_var = tk.IntVar(value=self.app.pan_speed)
        tk.Entry(dlg, textvariable=pan_var).grid(row=1, column=1)

        tk.Label(dlg, text='Map width:').grid(row=2, column=0, sticky='e')
        width_var = tk.IntVar(value=self.app.map_tiles_x * self.app.grid_size)
        tk.Entry(dlg, textvariable=width_var).grid(row=2, column=1)

        tk.Label(dlg, text='Map height:').grid(row=3, column=0, sticky='e')
        height_var = tk.IntVar(value=self.app.map_tiles_y * self.app.grid_size)
        tk.Entry(dlg, textvariable=height_var).grid(row=3, column=1)

        def apply():
            self.app.zoom = zoom_var.get()
            self.app.pan_speed = pan_var.get()
            width = width_var.get()
            height = height_var.get()
            if width and height:
                self.app.map_tiles_x = width // self.app.grid_size
                self.app.map_tiles_y = height // self.app.grid_size
                self.app.layers = [Layer(self.app.map_tiles_x, self.app.map_tiles_y) for _ in range(3)]
                self.app.camera = [0, 0]
                self.app.unsaved_map = False
            self.app.clamp_camera()
            dlg.destroy()

        tk.Button(dlg, text='OK', command=apply).grid(row=4, column=0, columnspan=2, pady=5)
        self.app.center_window(dlg)

    def open_save_map_dialog(self) -> None:
        os.makedirs('maps', exist_ok=True)
        dlg = tk.Toplevel(self.tk_root)
        dlg.title('Save Map')
        dlg.grab_set()

        tk.Label(dlg, text='Filename:').pack()
        name_var = tk.StringVar(value='map.json')
        entry = tk.Entry(dlg, textvariable=name_var)
        entry.pack(fill=tk.X, padx=5)

        listbox = tk.Listbox(dlg, height=10)
        for fn in sorted(f for f in os.listdir('maps') if f.endswith('.json')):
            listbox.insert(tk.END, fn)
        listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def on_select(event=None):
            sel = listbox.curselection()
            if sel:
                name_var.set(listbox.get(sel[0]))
        listbox.bind('<<ListboxSelect>>', on_select)

        def save_action():
            fname = name_var.get()
            if not fname.endswith('.json'):
                fname += '.json'
            path = os.path.join('maps', fname)
            self.app.save_map(path)
            dlg.destroy()

        tk.Button(dlg, text='Save', command=save_action).pack(pady=5)
        self.app.center_window(dlg)

    def open_load_map_dialog(self) -> None:
        os.makedirs('maps', exist_ok=True)
        dlg = tk.Toplevel(self.tk_root)
        dlg.title('Load Map')
        dlg.grab_set()

        listbox = tk.Listbox(dlg, height=10)
        for fn in sorted(f for f in os.listdir('maps') if f.endswith('.json')):
            listbox.insert(tk.END, fn)
        listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def load_action():
            sel = listbox.curselection()
            if sel:
                path = os.path.join('maps', listbox.get(sel[0]))
                self.app.load_map(path)
            dlg.destroy()

        tk.Button(dlg, text='Load', command=load_action).pack(pady=5)
        self.app.center_window(dlg)

    def clear_map_prompt(self) -> None:
        if self.app.unsaved_map:
            if messagebox.askyesno('Clear Map?', 'Unsaved changes! Clear anyway?', parent=self.tk_root):
                self.app.clear_map()
        else:
            self.app.clear_map()

    def open_save_state_dialog(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension='.json', filetypes=[('JSON', '*.json')],
            initialdir='map-states', initialfile='state.json', parent=self.tk_root
        )
        if path:
            self.app.save_state(path)

    def open_load_state_dialog(self) -> None:
        path = filedialog.askopenfilename(
            defaultextension='.json', filetypes=[('JSON', '*.json')],
            initialdir='map-states', parent=self.tk_root
        )
        if path:
            self.app.load_state(path)

    def clear_state_prompt(self) -> None:
        if self.app.unsaved_state:
            if messagebox.askyesno('Clear State?', 'Unsaved changes! Clear anyway?', parent=self.tk_root):
                self.app.clear_state()
        else:
            self.app.clear_state()
