# 🍎 Fruit Picking Simulation

This project simulates a fruit-picking process involving workers (pickers), a crate loader, and a truck. It demonstrates two different concurrency approaches in Python: **multiprocessing** (for CPU-bound operations) and **multithreading** (for GUI integration). The core idea is to model real-world coordination between multiple workers sharing resources.

---

## 🧠 Problem Description

A number of pickers work together to pick fruits from a tree. Each fruit picked is placed into a crate. Once the crate is full, a loader moves the crate into a truck. The challenge lies in properly synchronizing access to shared resources (fruits, crates, truck) between multiple concurrent workers.

---

## ⚙️ Approaches

### 1. `main.py` – Multiprocessing Approach

-   **Type**: CLI-based, no UI
-   **Concurrency**: Uses Python's `multiprocessing` module
-   **Use Case**: Suitable for CPU-bound simulation where process isolation improves performance and avoids GIL-related issues.
-   **Execution**:
    ```bash
    python main.py
    ```
-   **Requirements**: Only Python standard library. No additional dependencies required.
-   **NOTE**: This file does not contain any UI. The UI version should be preferred for visualization.

### 2. `ui.py` – Multithreading + UI Approach

-   **Type**: GUI-based application
-   **Concurrency**: Uses `threading` for tightly coupled UI logic
-   **Use Case**: Suitable for user-friendly visualization, where GUI responsiveness is crucial.
-   **Execution** (using the built binary):
    ```bash
    ./dist/ui.exe
    ```
-   **Requirements**: Third-party packages (pygame, pillow, etc.)
-   **NOTE**: This is the GUI version. Threading is used instead of multiprocessing to keep the UI responsive.

---

## 🧪 Development Setup

To run or modify the GUI version locally, follow these steps:

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/iNsoM22/OS-Fruit-Picker-Simulation
    cd OS-Fruit-Picker-Simulation/
    ```
2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate    # Windows
    ```
3.  **Install Requirements**
    ```bash
    pip install -r requirements.txt
    ```
---

## 🚀 Usage

### CLI Version (Multiprocessing)

```bash
python main.py
```

### GUI Version (Multithreading)

```bash
./dist/ui.exe
```

Or run directly from source (after installing dependencies):

```bash
python ui.py
```

---

## 📌 Notes

-   `main.py` is the pure multiprocessing version and is self-contained with no UI. It uses only standard Python libraries.
-   `ui.py` is the GUI version using multithreading, which allows for interactive visualization and better responsiveness.
-   The GUI version should be preferred for demonstration or educational purposes.

---

## 🧼 Clean Exit and Synchronization

-   Multiprocessing implementation ensures safe access to shared memory using `Lock`, `Event`, and `Manager` objects.
-   The loader and pickers coordinate via event signaling and shared values to prevent race conditions or deadlocks.

---

## 📂 Directory Structure

```bash
.
├── main.py         # CLI - multiprocessing version
├── ui.py           # GUI - multithreading version
├── requirements.txt # Optional dependencies for GUI
├── dist/
│   └── ui.exe      # Compiled GUI executable
└── README.md       # Readme File
```
