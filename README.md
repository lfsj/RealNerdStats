# RealNerdStats

A simple, colorful, and continuously updating system and process monitor for your terminal, written in Python.

 <!-- You can replace this with a real screenshot -->

## Features

*   **Live Dashboard**: Continuously updates system and process information in the terminal.
*   **Comprehensive System Header**:
    *   CPU core counts (physical and logical) and current frequency.
    *   Detailed RAM and SWAP memory usage (used, total, and percentage).
    *   System-wide disk I/O rates (Read/s and Write/s).
    *   Usage information for each mounted disk partition.
    *   Overall CPU and Memory percentage, and total network I/O rates.
*   **Per-Core Utilization**: Shows a detailed breakdown of the usage for each individual CPU core.
*   **Top Process List**: Lists the top N processes, sorted by CPU usage.
*   **Detailed Process Info**: For each process, it shows:
    *   PID (Process ID)
    *   Process Name
    *   CPU Usage % (can exceed 100% on multi-core systems)
    *   Memory Usage %
    *   Process-specific Disk Read/s and Write/s per second.
*   **Detailed System Info**:
    *   System boot time, logged-in users.
    *   Hardware sensor data for temperatures, fans, and battery status (where available).
*   **Optional Network Details**: A detailed view of network interfaces and connection statuses.
*   **Colorful & Readable Output**:
    *   Uses colors to distinguish labels from data.
    *   Highlights high CPU usage (>75%) in red for easy identification.
    *   Features colored separators and alternating background colors for the process list to improve readability.
*   **CSV Export**: Log all collected data to a CSV file for later analysis.
*   **Customizable**: Use command-line arguments to control the display and refresh rate.

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
