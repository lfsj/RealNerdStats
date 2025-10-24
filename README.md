# RealNerdStats

A simple, colorful, and continuously updating system and process monitor for your terminal, written in Python.

  <!-- You can replace this with a real screenshot -->

## Features

*   **Live Dashboard**: Continuously updates system and process information in the terminal.
*   **Overall System Stats**: Displays total CPU and Memory utilization, along with system-wide Network I/O (Sent/Received per second).
*   **Per-Core Utilization**: Shows a detailed breakdown of the usage for each individual CPU core.
*   **Top Process List**: Lists the top N processes, sorted by CPU usage.
*   **Detailed Process Info**: For each process, it shows:
    *   PID (Process ID)
    *   Process Name
    *   CPU Usage % (can exceed 100% on multi-core systems)
    *   Memory Usage %
    *   Disk Read/s and Write/s
*   **Colorful & Readable Output**:
    *   Uses colors to distinguish labels from data.
    *   Highlights high CPU usage (>75%) in red for easy identification.
    *   Features colored separators and alternating background colors for the process list to improve readability.
*   **Customizable**: Use command-line arguments to change the number of processes displayed.

## Requirements

*   Python 3.x
*   `psutil`
*   `colorama`

## Installation

1.  Clone this repository or download the `cpu.py` file.

2.  Install the required Python packages using pip:
    ```bash
    pip install psutil colorama
    ```

## Usage

Navigate to the project directory in your terminal and run the script.

#### Basic Usage

To run the monitor with the default setting (displaying the top 5 processes):
```bash
python cpu.py
```

#### Customizing the Number of Processes

Use the `-n` or `--number` argument to specify how many top processes you want to see.

To show the top 10 processes:
```bash
python cpu.py -n 10
```

To show the top 3 processes:
```bash
python cpu.py --number 3
```

#### Exiting the Monitor

Press `Ctrl+C` at any time to gracefully exit the application.
