"""
THIS FILE 'main.py' IS THE MULTIPROCESSING APPROCH TO THE GIVEN PROBLEM.
THIS DOESNOT CONTAIN ANY UI, ALSO THE UI VERSION SHOULD BE PREFFERED.
USAGE: 'python main.py'
NOTE: ONLY REQUIRES PYTHON WITH BUILT-IN PACKAGES.
"""
import time
import multiprocessing
from multiprocessing import Process, Lock, Event, Value, Manager


def initialize_tree(tree, fruit_count=50):
    """
    Initializes the tree with a specified number of fruits.

    Args:
        tree (list): Shared list representing fruits on the tree.
        fruit_count (int): Number of fruits to initialize on the tree.
    """
    tree.extend([1] * fruit_count)


def fruit_picker(tree, crate, lock, loader_event, new_crate_event, truck, fruits_picked,
                 last_picked, current_crate_filling, CRATE_SIZE, total_fruits):
    """
    Represents a worker that picks fruits from the tree and puts them in a shared crate.

    Args:
        tree (list): Shared list where 1 indicates a fruit and 0 means empty.
        crate (list): Shared list representing the crate being filled.
        lock (Lock): Synchronization primitive to avoid race conditions.
        loader_event (Event): Event used to signal the loader when the crate is full.
        new_crate_event (Event): Event to notify pickers a new crate is available.
        truck (list): Shared list storing full crates (each crate is a list).
        fruits_picked (Value): Counter for fruits picked (not used for logic here).
        last_picked (Value): Index of the last fruit picked from the tree.
        current_crate_filling (Value): Flag indicating whether a crate is being loaded.
        CRATE_SIZE (int): Maximum number of fruits per crate.
        total_fruits (int): Total number of fruits initially on the tree.
    """
    while True:
        with lock:
            # Exit if no Fruits
            if last_picked.value >= total_fruits:
                print(f"[{multiprocessing.current_process().name}] Tree is empty. Exiting Picker.")
                break

            # Pick a Fruit
            index: int = last_picked.value
            last_picked.value += 1
            if tree[index] == 0:
                continue
            tree[index] = 0
            fruit = f"Fruit-{index + 1}"
            print(f"[{multiprocessing.current_process().name}] Picked {fruit}.")

        waiting_for_loader = False
        while True:
            # Check if the Loader is working.
            while True:
                with lock:
                    if current_crate_filling.value == 0:
                        break
                    waiting_for_loader = True
                    print(f"[{multiprocessing.current_process().name}] Waiting for Loader.".title())
                time.sleep(0.2)
                
            if waiting_for_loader:
                print(f"[{multiprocessing.current_process().name}] New Crate Received.".title())
                waiting_for_loader = False
                
            # Crate is Available
            with lock:
                if len(crate) < CRATE_SIZE:
                    crate.append(f"Fruit-{index + 1}")
                    print(f"[{multiprocessing.current_process().name}] Put Fruit-{index + 1} in Crate:{len(truck) + 1}.")

                    # If this fruit made the crate full and no one has triggered the loader
                    if len(crate) == CRATE_SIZE and current_crate_filling.value == 0:
                        current_crate_filling.value = 1
                        print(f"[{multiprocessing.current_process().name}] Maximum Crate Size Reached. Calling the Loader.".title())
                        loader_event.set()
                    break
                else:
                    # Crate is full, check if loader has already been triggered
                    if current_crate_filling.value == 0:
                        current_crate_filling.value = 1
                        print(f"[{multiprocessing.current_process().name}] No Space in Crate. Triggering Loader.".title())
                        loader_event.set()                


def loader(crate, truck, lock, loader_event, new_crate_event, 
           tree_empty, fruits_picked, current_crate_filling):
    """
    Represents the loader process which loads crates onto the truck.

    Args:
        crate (list): Shared list representing the crate being filled.
        truck (list): Shared list of full crates.
        lock (Lock): Synchronization primitive.
        loader_event (Event): Event that triggers the loader when a crate is ready.
        new_crate_event (Event): Event used to notify pickers a new crate is ready.
        tree_empty (Event): Event to indicate that no fruits are left on the tree.
        fruits_picked (Value): Counter for fruits picked in the current crate.
        current_crate_filling (Value): Flag indicating whether a crate is being loaded.
    """
    
    final_check_done: bool = False
    while True:
        loader_event.wait()
        loader_event.clear()

        with lock:
            if len(crate) > 0:
                print(f"[Loader] Loading Crate into the Truck With {len(crate)} Fruits.".title())
                truck.append(crate[:])
                crate[:] = []
                fruits_picked.value = 0
                current_crate_filling.value = 0
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
    print("[Loader] Exiting.")


def simulate_fruit_picking(num_fruits=50):
    """
    Starts the entire fruit-picking simulation with multiple picker processes and a loader.

    Args:
        num_fruits (int): Number of fruits to place on the tree initially.
    """
    CRATE_SIZE = 12

    manager = Manager()

    # Shared resources
    tree = manager.list()
    crate = manager.list()
    truck = manager.list()

    lock = Lock()
    loader_event = Event()
    new_crate_event = Event()
    tree_empty = Event()

    fruits_picked = Value('i', 0)
    last_picked = Value('i', 0)
    current_crate_filling = Value('i', 0)

    initialize_tree(tree, num_fruits)

    pickers = [
        Process(target=fruit_picker, args=(
            tree, crate, lock, loader_event, new_crate_event, truck,
            fruits_picked, last_picked, current_crate_filling, CRATE_SIZE, num_fruits
        ), name=f"Picker-{i+1}")
        for i in range(3)
    ]

    loader_process = Process(target=loader, args=(
        crate, truck, lock, loader_event, new_crate_event, tree_empty,
        fruits_picked, current_crate_filling
    ))

    loader_process.start()
    for p in pickers:
        p.start()

    for p in pickers:
        p.join()

    tree_empty.set()
    loader_event.set()
    loader_process.join()

    print("\nAll Crates Loaded in Truck:")
    for idx, c in enumerate(truck, 1):
        print(f"Crate {idx}: {c}")


if __name__ == "__main__":
    simulate_fruit_picking(num_fruits=50)
