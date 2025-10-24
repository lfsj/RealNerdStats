import psutil
import argparse
import time
import os
from colorama import Fore, Back, init


def format_bytes(byte_count):
    """Converts bytes to a human-readable string (KB, MB, GB)."""
    if byte_count is None:
        return "N/A"
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while byte_count >= power and n < len(power_labels) -1 :
        byte_count /= power
        n += 1
    return f"{byte_count:.2f}{power_labels[n]}B/s"

last_io_counters = {}
last_net_counters = psutil.net_io_counters()
INTERVAL = 1.0

# Initialize colorama
init(autoreset=True)

parser = argparse.ArgumentParser(description="RealNerdStats: A simple system and process monitor.")
parser.add_argument("-n", "--number", type=int, default=5, help="Number of top processes to display (default: 5)")
args = parser.parse_args()

try:
    while True:
        loop_start_time = time.time()
        output_lines = []
        
        # 1. Gather all data first
        overall_cpu = psutil.cpu_percent(interval=0.1)
        overall_mem = psutil.virtual_memory().percent
        per_cpu_usage = psutil.cpu_percent(interval=0.1, percpu=True)

        # Calculate system-wide network I/O
        current_net_counters = psutil.net_io_counters()
        net_sent_rate = (current_net_counters.bytes_sent - last_net_counters.bytes_sent) / INTERVAL
        net_recv_rate = (current_net_counters.bytes_recv - last_net_counters.bytes_recv) / INTERVAL
        last_net_counters = current_net_counters
        
        processes = []
        current_procs = {p.pid: p for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'io_counters'])}

        for pid, proc in current_procs.items():
            try:
                proc_info = proc.info
                # Calculate I/O rates
                last_io = last_io_counters.get(pid)
                if last_io:
                    proc_info['read_rate'] = (proc_info['io_counters'].read_bytes - last_io.read_bytes) / INTERVAL
                    proc_info['write_rate'] = (proc_info['io_counters'].write_bytes - last_io.write_bytes) / INTERVAL
                else:
                    proc_info['read_rate'] = 0.0
                    proc_info['write_rate'] = 0.0
                processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        last_io_counters = {p.pid: p.info['io_counters'] for p in current_procs.values() if p.info['io_counters']}
        
        sorted_processes = sorted(processes, key=lambda proc: proc['cpu_percent'], reverse=True)

        # 2. Prepare all output lines before printing
        output_lines.append(f"--- RealNerdStats --- Press Ctrl+C to exit ---")
        output_lines.append(f"{Fore.LIGHTBLUE_EX}CPU Total:{Fore.RESET} {overall_cpu:5.2f}% | {Fore.LIGHTBLUE_EX}MEM:{Fore.RESET} {overall_mem:5.2f}% | {Fore.LIGHTBLUE_EX}NET SENT:{Fore.RESET} {format_bytes(net_sent_rate):>10} | {Fore.LIGHTBLUE_EX}NET RECV:{Fore.RESET} {format_bytes(net_recv_rate):>10}")
        
        core_strings = []
        for i, usage in enumerate(per_cpu_usage):
            color = Fore.RED if usage > 75.0 else ""
            core_strings.append(f"{Fore.LIGHTBLUE_EX}Core {i}:{Fore.RESET} {color}{usage:5.2f}%")
        core_usage_str = " | ".join(core_strings)
        output_lines.append(core_usage_str)

        output_lines.append(f"{Back.LIGHTBLUE_EX}{' ' * 80}{Back.RESET}")
        output_lines.append(f"{Fore.LIGHTBLUE_EX}{'PID':>7} {'PROCESS NAME':<35} {'CPU %':>7} {'MEM %':>7} {'READ/s':>10} {'WRITE/s':>10}{Fore.RESET}")
        for i, proc in enumerate(sorted_processes[:args.number]):
            read_str = format_bytes(proc.get('read_rate'))
            write_str = format_bytes(proc.get('write_rate'))
            cpu_color = Fore.RED if proc['cpu_percent'] > 75.0 else ""

            bg_color = Back.LIGHTBLACK_EX if i % 2 == 0 else Back.RESET # Alternate background
            output_lines.append(f"{bg_color}{proc['pid']:>7} {proc['name']:<35.35} {cpu_color}{proc['cpu_percent']:>7.2f}{Fore.RESET} {proc['memory_percent']:>7.2f} {read_str:>10} {write_str:>10}{Back.RESET}")
        output_lines.append(f"{Back.LIGHTBLUE_EX}{' ' * 80}{Back.RESET}")

        # 3. Clear screen and print everything at once
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n".join(output_lines))

        # 4. Sleep for the remainder of the interval to give reading time
        work_duration = time.time() - loop_start_time
        sleep_time = max(0, INTERVAL - work_duration)
        time.sleep(sleep_time)
except KeyboardInterrupt:
    print("\nExiting RealNerdStats.")
 
