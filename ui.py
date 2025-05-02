"""
THIS IS FILE 'ui.py' CONTAINS THE SAME APPLICATION AS 'main.py', BUT WITH UI FOR BETTER VISUALIZATION.
HERE, RATHER THAN MULTIPROCESSING, THREADING IS APPLIED. AS THE GUI APPLICATION NEEDS TO BE HIGHLY COUPLED
WITH THE PROCESSES.

USAGE: AS THE FILE REQUIRES THIRD PARTY PACKAGES, IT IS ADVISED TO USE THE BUILD FILE TO RUN THE APPLICATION
USING 'dist/ui.exe' IN THE TERMINAL.

NOTE: AS BLOCKING SLEEP IS CALLED IN HERE TO VISUALIZE SOME OF THE LOGGING WON'T BE
SHOWN, DUE TO FAST EXECUTIONS AND REAVAILABILITY OF RESOURCES AFTER CALL RESUMPTION.
SET 'time.sleep(0)' OR COMMENT OUT THOSE INSTRUCTION TO OBSERVE THE ACTUAL BEHAVIOR.
"""
from typing import List, Dict, Any
import tkinter as tk
from tkinter import ttk, Tk, messagebox
import threading
import time
import random
from PIL import Image, ImageTk
import pygame

# GLOBAL CONFIGS
CRATE_SIZE = 12
NUM_FRUITS = 60


def fruit_picker(name: int,
                 tree: List[int],
                 ui_object: "FruitPickerGUI",
                 crate: List[str],
                 lock: threading.Lock,
                 loader_event: threading.Event,
                 tree_empty: threading.Event,
                 new_crate_event: threading.Event,
                 shared_state: Dict[str, Any]) -> None:
    """
    Function executed by a fruit picker thread.

    - Picks fruit from the tree if available.
    - Places fruit in the shared crate.
    - If the crate is full, it triggers the loader via an event.
    - Waits while the loader processes the crate.
    - Handles UI updates and synchronization via shared_state and threading primitives.

    Args:
        name (int): Picker ID (1-indexed).
        tree (List[int]): Shared list representing fruit on the tree (1 = present, 0 = picked).
        ui_object (FruitPickerGUI): GUI object to update canvas and draw elements.
        crate (List[str]): Shared crate list to store picked fruits.
        lock (threading.Lock): Lock to synchronize access to shared_state and crate.
        loader_event (threading.Event): Event to signal when the loader should be triggered.
        tree_empty (threading.Event): Event to indicate the tree is empty.
        new_crate_event (threading.Event): Event to wait for a new crate after the old one is full.
        shared_state (Dict[str, Any]): Dictionary storing shared counters and flags.
    """
    picked_item: Any = None
    picker_position: int = ui_object.picker_positions[name - 1]

    while True:
        # Pick the fruit
        if picked_item:
            ui_object.canvas.delete(picked_item)
                            
        with lock:
            if shared_state['last_picked'] >= len(tree):
                ui_object.draw_scene()
                print(f"[Picker-{name}] Tree is Empty. Exiting.")
                break

            index: int = shared_state['last_picked']
            shared_state['last_picked'] += 1

            if tree[index] == 1:
                tree[index] = 0
                picked_item = ui_object.canvas.create_image(
                    picker_position - 20, 435, image=ui_object.fruit_img_med)
                print(f"[Picker-{name}] Picked Fruit-{index + 1}.".title())

        time.sleep(0.2)

        # Put the fruit in the crate
        waiting_for_loader = False
        while True:
            while shared_state['current_crate_filling']:
                with lock:
                    waiting_for_loader = True
                    print(f"[Picker-{name}] Waiting for Loader.".title())
                time.sleep(0.2)

            if waiting_for_loader:
                print(f"[Picker-{name}] New Crate Received.".title())
                waiting_for_loader = False

            with lock:
                if len(crate) < CRATE_SIZE:
                    crate.append(f"Fruit-{index + 1}")
                    shared_state['fruits_picked'] += 1
                    shared_state['fruits_left'] -= 1
                    if picked_item:
                        time.sleep(0.1)
                        ui_object.canvas.delete(picked_item)
                        ui_object.draw_scene()

                    print(f"[Picker-{name}] Put Fruit-{index + 1}. Current Crate Size: {len(crate)}".title())

                    # If this fruit made the crate full and no one has triggered the loader
                    if len(crate) == CRATE_SIZE and not shared_state['current_crate_filling']:
                        shared_state['current_crate_filling'] = True
                        print(f"[Picker-{name}] Maximum Crate Size Reached. Calling the Loader.".title())
                        loader_event.set()
                    break
                else:
                    # Crate is full, check if loader has already been triggered
                    if not shared_state['current_crate_filling']:
                        shared_state['current_crate_filling'] = True
                        print(f"[Picker-{name}] No Space in Crate. Triggering Loader.".title())
                        loader_event.set()

            # Loader Process; Avoid tight loop
            time.sleep(1)


def loader(crate: List[str],
           truck: List[List[str]],
           ui_object: "FruitPickerGUI",
           lock: threading.Lock,
           loader_event: threading.Event,
           new_crate_event: threading.Event,
           tree_empty: threading.Event,
           shared_state: Dict[str, Any]) -> None:
    """
    Function executed by the loader thread.

    - Waits for the crate to be full (triggered by picker via `loader_event`).
    - Transfers the crate contents to the truck.
    - Clears the crate and resets shared state for pickers to use a new crate.
    - Once the tree is marked empty and no fruits remain, it performs a final load (if needed) and exits.

    Args:
        crate (List[str]): Shared crate where pickers deposit fruits.
        truck (List[List[str]]): List representing the truck loaded with multiple full crates.
        ui_object (FruitPickerGUI): GUI object for updating visuals and playing loader sounds.
        lock (threading.Lock): Lock to synchronize access to shared_state, crate, and truck.
        loader_event (threading.Event): Event triggered by pickers when the crate is full.
        new_crate_event (threading.Event): Event set after a new crate is available.
        tree_empty (threading.Event): Event to indicate that no fruits remain on the tree.
        shared_state (Dict[str, Any]): Dictionary storing shared counters and flags.
    """
    final_check_done: bool = False

    while True:
        loader_event.wait()
        loader_event.clear()
        ui_object.play_loader_change_music()

        with lock:
            if len(crate) > 0:
                print(f"[Loader] Loading Crate into the Truck With {len(crate)} Fruits.".title())
                truck.append(crate[:])
                crate.clear()
                shared_state['fruits_picked'] = 0
                shared_state['current_crate_filling'] = False
                new_crate_event.set()

        # Final check and exit condition
        if tree_empty.is_set():
            with lock:
                if not final_check_done and len(crate) > 0:
                    print(f"[Loader] Final Loading Of the Remaining {len(crate)} Fruits.".title())
                    truck.append(crate[:])
                    crate[:] = []
                    new_crate_event.set()
                    final_check_done = True
                else:
                    break


####################
# --- UI Class ---
####################
class FruitPickerGUI:
    def __init__(self, root):
        self.root = root
        self.original_width = 1000
        self.original_height = 650

        self.root.title("🍎 Fruit Picker Tree Simulation")
        self.root.geometry("1000x650")
        self.root.configure(bg="#87CEEB")

        # Styling
        label_style = {
            "font": ("Segoe UI", 12, "bold"),
            "bg": "#f9f9f9",
            "fg": "#333333",
            "padx": 12,
            "pady": 6,
            "bd": 1,
            "relief": "solid"
        }

        button_style = {
            "font": ("Segoe UI", 12, "bold"),
            "bg": "#4CAF50",
            "fg": "white",
            "activebackground": "#45A049",
            "activeforeground": "white",
            "bd": 0,
            "padx": 12,
            "pady": 6,
            "cursor": "hand2"
        }

        small_button_style = {
            "font": ("Segoe UI", 10, "bold"),
            "bg": "#FFC107",
            "fg": "#212121",
            "activebackground": "#FFB300",
            "activeforeground": "#212121",
            "bd": 0,
            "padx": 8,
            "pady": 2,
            "cursor": "hand2"
        }

        self.num_fruits = NUM_FRUITS if 'NUM_FRUITS' in globals() else 30
        self.fruits_left = tk.IntVar(value=self.num_fruits)
        self.crates_filled = tk.IntVar(value=0)
        self.tree_array = [1] * self.num_fruits

        self.canvas = tk.Canvas(root, bg="#87CEEB", highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        self.start_btn = tk.Button(root, text="▶ Start", command=self.start_threads, **button_style)
        self.start_btn.place(x=20, y=20)

        style = ttk.Style()
        style.configure("TEntry", padding=5, font=("Segoe UI", 11))

        self.fruit_entry_label = tk.Label(root, text="Fruits:", font=("Segoe UI", 12, "bold"), bg="#87CEEB", fg="#333")
        self.fruit_entry_label.place(x=20, y=75)

        self.fruit_entry = ttk.Entry(root, width=7)
        self.fruit_entry.place(x=80, y=75)
        self.fruit_entry.insert(0, str(self.num_fruits))
        self.fruit_entry.config(state="disabled")

        # "Edit/Set" Button
        self.toggle_fruits_btn = tk.Button(
            root,
            text="✎ Edit",
            font=("Segoe UI", 11, "bold"),
            bg="#FFC107", 
            activebackground="#FFB300",
            fg="#212121",
            activeforeground="white",
            bd=0,
            padx=10,
            relief="flat",
            cursor="hand2",
            command=self.toggle_edit_set
        )
        self.toggle_fruits_btn.place(x=150, y=75)

        # Fruits and Crates labels
        self.fruits_label = tk.Label(root, text="Fruits Left: -", **label_style)
        self.fruits_label.place(x=700, y=20)

        self.crates_label = tk.Label(root, text="Filled Crates: -", **label_style)
        self.crates_label.place(x=860, y=20)

        self.picker_positions = [700, 550, 400]
        self.current_crate = []
        self.tree_fruit_items = []
        self.crate_fruit_items = []

        pygame.mixer.init()
        self.load_images()
        self.draw_scene()
        self.update_labels()
        self.play_background_music()

    def toggle_edit_set(self):
        if str(self.fruit_entry.cget('state')) == 'disabled':
            # Enable Entry for Editing
            self.fruit_entry.config(state='active')
            self.toggle_fruits_btn.config(text="✔ Set", bg="#2196F3", activebackground="#1976D2", fg="white")
        else:
            try:
                value = int(self.fruit_entry.get())
                if value <= 0:
                    raise ValueError("Must be Positive.")
                global NUM_FRUITS
                NUM_FRUITS = value
                print(f"[GUI] Number of Fruits Set to {value}")
                self.fruit_entry.config(state='disabled')
                self.toggle_fruits_btn.config(text="✎ Edit", bg="#FFC107", activebackground="#FFB300", fg="#212121")
                self.fruits_label.config(text=f"Fruits Left: {NUM_FRUITS}")
            except ValueError:
                messagebox.showerror("Invalid Input", "Please Enter a Positive Integer for Fruits.")


    def load_images(self):
        self.background_image = ImageTk.PhotoImage(
            Image.open("Assets/Images/bg.jpg").resize((1000, 650)))
        self.tree_img = ImageTk.PhotoImage(Image.open(
            "Assets/Images/tree.png").resize((800, 600)))
        self.fruit_img = ImageTk.PhotoImage(Image.open(
            "Assets/Images/fruit.png").resize((20, 20)))
        self.farmer_img = ImageTk.PhotoImage(Image.open(
            "Assets/Images/farmer.png").resize((75, 100)))
        self.crate_img = ImageTk.PhotoImage(Image.open(
            "Assets/Images/box.png").resize((330, 240)))
        self.fruit_img_med = ImageTk.PhotoImage(
            Image.open("Assets/Images/fruit.png").resize((30, 30)))

        self.fruit_img_large = ImageTk.PhotoImage(
            Image.open("Assets/Images/fruit.png").resize((120, 40)))
        self.fruit_positions = [
            (random.randint(280, 680), random.randint(100, 300)) for _ in range(NUM_FRUITS)
        ]
        self.crate_fruits_positions = [
            (800 + 35 * (i % 4), 370 + 35 * (i // 4)) for i in range(12)
        ]
        

    def draw_scene(self):
        if not hasattr(self, 'scene_drawn') or not self.scene_drawn:
            # Draw Assets elements once
            self.canvas.create_image(
                0, 0, image=self.background_image, anchor='nw')
            self.canvas.create_image(460, 250, image=self.tree_img)
            self.canvas.create_image(850, 440, image=self.crate_img)
            for x in self.picker_positions:
                self.canvas.create_image(x - 50, 450, image=self.farmer_img)
            self.scene_drawn = True

        # Update fruits on tree
        if not self.tree_fruit_items:
            for i, (x, y) in enumerate(self.fruit_positions):
                if self.tree_array[i] == 1:
                    item = self.canvas.create_image(x, y, image=self.fruit_img)
                else:
                    item = None
                self.tree_fruit_items.append(item)
        else:
            for i in range(NUM_FRUITS):
                if self.tree_array[i] == 0 and self.tree_fruit_items[i]:
                    self.canvas.delete(self.tree_fruit_items[i])
                    self.tree_fruit_items[i] = None

        # Update crate fruits
        # First, remove existing crate fruit items
        for item in self.crate_fruit_items:
            self.canvas.delete(item)
        self.crate_fruit_items.clear()

        # Then, draw current crate contents
        for i in range(min(len(self.current_crate), CRATE_SIZE)):
            x, y = self.crate_fruits_positions[i]
            item = self.canvas.create_image(x, y, image=self.fruit_img_large)
            self.crate_fruit_items.append(item)

    def update_labels(self):
        self.fruits_label.config(text=f"Fruits Left: {self.fruits_left.get()}")
        self.crates_label.config(
            text=f"Filled Crates: {self.crates_filled.get()}")
        
    def play_background_music(self):
        pygame.mixer.music.load("Assets/Sounds/theme.mp3")
        pygame.mixer.music.set_volume(0.15) 
        pygame.mixer.music.play(loops=-1)
        
        
    def play_loader_change_music(self):
        loader_sound = pygame.mixer.Sound("Assets/Sounds/loader.mp3")
        loader_sound.set_volume(0.35)
        loader_sound.play()
        
    
    def play_simulation_finish_music(self):
        loader_sound = pygame.mixer.Sound("Assets/Sounds/finish.mp3")
        loader_sound.set_volume(0.35)
        loader_sound.play()
        

    def start_threads(self) -> None:
        """
        Starts the fruit picker and loader threads, initializes shared state, and begins
        monitoring updates for the GUI.
        
        This function disables the start button, creates shared resources and threading events,
        spawns picker and loader threads, and continuously updates the UI based on shared state.
        """

        # Disable the Start button to prevent multiple clicks
        self.start_btn.config(state="disabled")

        # Initialize tree with fruits (1 = fruit present)
        self.tree = [1] * NUM_FRUITS
        crate: list[str] = []               # Crate to temporarily store picked fruits
        truck: list[list[str]] = []         # Truck will store full crates

        # Thread synchronization primitives
        lock = threading.Lock()
        loader_event = threading.Event()     # Signals that the crate is full
        new_crate_event = threading.Event()  # Signals that a new crate is available
        tree_empty = threading.Event()       # Signals that tree is empty and picking is done

        # Shared state dictionary for coordination between threads
        shared_state: dict[str, Any] = {
            'fruits_picked': 0,               # Fruits picked in current crate
            'last_picked': 0,                 # Index of last picked fruit
            'current_crate_filling': False,   # Whether crate is currently being handled
            'fruits_left': NUM_FRUITS         # Total fruits left
        }

        # Link instance-level variables for later access
        self.tree = self.tree
        self.truck = truck

        # Create and start picker threads
        pickers = [
            threading.Thread(
                target=fruit_picker,
                args=(i, self.tree, self, crate, lock, loader_event,
                    tree_empty, new_crate_event, shared_state)
            )
            for i in range(1, 4)
        ]

        # Create and start loader thread
        loader_thread = threading.Thread(
            target=loader,
            args=(crate, truck, self, lock, loader_event,
                new_crate_event, tree_empty, shared_state)
        )

        loader_thread.start()
        for p in pickers:
            p.start()

        def poll_state() -> None:
            """Poll shared state and update UI periodically in a daemon thread."""
            while not tree_empty.is_set():
                try:
                    with lock:
                        self.tree_array[:] = self.tree
                        self.fruits_left.set(shared_state['fruits_left'])
                        self.crates_filled.set(len(truck))
                        self.current_crate[:] = crate
                except Exception:
                    break
                self.update_labels()

        # Start background thread to keep updating UI
        threading.Thread(target=poll_state, daemon=True).start()

        def wait_and_join() -> None:
            """Wait for all picker threads to finish and perform cleanup."""
            for p in pickers:
                p.join()
            tree_empty.set()           # Notify loader to do final check and exit
            loader_event.set()         # In case loader is waiting
            loader_thread.join()       # Wait for loader to finish

            # Final UI update and re-enable start button
            self.crates_filled.set(len(truck))
            self.current_crate = []
            self.draw_scene()
            self.update_labels()
            self.play_simulation_finish_music()
            self.start_btn.config(state="active")

            # 🔽 Print Crate Statistics
            print("\n====== Crate Stats ======")
            print(f"Total Crates Filled: {len(truck)}\n")
            for i, crate in enumerate(truck, start=1):
                print(f"Crate-{i} ({len(crate)} fruits): {crate}")
            print("=========================\n")

        # Start thread that waits for all workers to complete and then cleans up
        threading.Thread(target=wait_and_join, daemon=True).start()


if __name__ == "__main__":
    root = Tk()
    app = FruitPickerGUI(root)
    root.mainloop()
