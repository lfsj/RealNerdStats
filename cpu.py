import psutil
import argparse
import time
import os
from colorama import Fore, Back, init
from datetime import datetime
import socket
import csv


def format_bytes(byte_count, is_rate=True):
    """Converts bytes to a human-readable string (KB, MB, GB, TB)."""
    if byte_count is None:
        return "N/A"
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while byte_count >= power and n < len(power_labels) - 1:
        byte_count /= power
        n += 1
    suffix = "B/s" if is_rate else "B"
    return f"{byte_count:.2f}{power_labels[n]}{suffix}"

def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="RealNerdStats: A simple system and process monitor.")
    parser.add_argument("-n", "--number", type=int, default=5, help="Number of top processes to display (default: 5)")
    parser.add_argument("-e", "--export", type=str, help="Export data to a CSV file at the given path.")
    parser.add_argument("--network", action="store_true", help="Show detailed network interface and connection information.")
    parser.add_argument("-i", "--interval", type=float, default=1.0, help="Refresh interval in seconds (default: 1.0)")
    return parser.parse_args()

def setup_csv_export(filename):
    """Opens a CSV file for writing and returns the file and writer objects."""
    if not filename:
        return None, None
    try:
        csv_file = open(filename, 'w', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Timestamp', 'Overall CPU %', 'Overall MEM %', 'Net Sent (B/s)', 'Net Recv (B/s)',
                             'PID', 'Process Name', 'Process CPU %', 'Process MEM %', 'Read (B/s)', 'Write (B/s)'])
        print(f"{Fore.GREEN}Logging data to {filename}...{Fore.RESET}")
        return csv_file, csv_writer
    except IOError as e:
        print(f"{Fore.RED}Error: Could not open file {filename} for writing: {e}{Fore.RESET}")
        return None, None

class RealNerdStats:
    def __init__(self, args):
        self.args = args
        self.last_io_counters = {}
        self.last_net_counters = psutil.net_io_counters()
        self.last_disk_io_counters = psutil.disk_io_counters()
        self.system_stats = {}
        self.top_processes = []
        self.csv_file, self.csv_writer = setup_csv_export(args.export)
        init(autoreset=True)

    def _get_sensor_data(self, sensor_func):
        """Safely get sensor data, handling AttributeError if not supported."""
        try:
            return sensor_func()
        except AttributeError:
            return None

    def _gather_system_stats(self):
        """Gathers and returns system-wide statistics."""
        virtual_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()
        per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        self.system_stats = {
            'overall_cpu': sum(per_cpu) / len(per_cpu),
            'overall_mem': virtual_mem.percent,
            'per_cpu_usage': per_cpu,
            'cpu_cores_physical': psutil.cpu_count(logical=False),
            'cpu_cores_logical': psutil.cpu_count(logical=True),
            'cpu_frequency': psutil.cpu_freq(),
            'virtual_memory': virtual_mem,
            'swap_memory': swap_mem,
            'boot_time': psutil.boot_time(),
            'users': psutil.users(),
            'sensors_temperatures': self._get_sensor_data(lambda: psutil.sensors_temperatures()),
            'sensors_fans': self._get_sensor_data(lambda: psutil.sensors_fans()),
            'sensors_battery': self._get_sensor_data(lambda: psutil.sensors_battery()),
        }

        if self.args.network:
            self.system_stats['net_if_addrs'] = psutil.net_if_addrs()
            self.system_stats['net_if_stats'] = psutil.net_if_stats()
            self.system_stats['net_connections'] = psutil.net_connections()

        current_net = psutil.net_io_counters()
        self.system_stats['net_sent_rate'] = (current_net.bytes_sent - self.last_net_counters.bytes_sent) / self.args.interval
        self.system_stats['net_recv_rate'] = (current_net.bytes_recv - self.last_net_counters.bytes_recv) / self.args.interval
        self.last_net_counters = current_net

        current_disk = psutil.disk_io_counters()
        self.system_stats['disk_read_rate'] = (current_disk.read_bytes - self.last_disk_io_counters.read_bytes) / self.args.interval
        self.system_stats['disk_write_rate'] = (current_disk.write_bytes - self.last_disk_io_counters.write_bytes) / self.args.interval
        self.last_disk_io_counters = current_disk

        self.system_stats['disk_partitions'] = []
        try:
            for part in psutil.disk_partitions():
                usage = psutil.disk_usage(part.mountpoint)
                self.system_stats['disk_partitions'].append({'device': part.device, 'mountpoint': part.mountpoint, 'usage': usage})
        except (PermissionError, FileNotFoundError):
            pass

    def _gather_process_stats(self):
        """Gathers and returns statistics for running processes."""
        processes = []
        current_procs = {p.pid: p for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'io_counters'])}

        for pid, proc in current_procs.items():
            try:
                proc_info = proc.info
                last_io = self.last_io_counters.get(pid)
                if last_io:
                    proc_info['read_rate'] = (proc_info['io_counters'].read_bytes - last_io.read_bytes) / self.args.interval
                    proc_info['write_rate'] = (proc_info['io_counters'].write_bytes - last_io.write_bytes) / self.args.interval
                else:
                    proc_info['read_rate'] = 0.0
                    proc_info['write_rate'] = 0.0
                processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        self.last_io_counters = {p.pid: p.info['io_counters'] for p in current_procs.values() if p.info.get('io_counters')}
        self.top_processes = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)

    def _format_header(self):
        """Formats the main header section."""
        lines = [f"{Fore.YELLOW}{Back.LIGHTBLUE_EX}--- RealNerdStats --- Press Ctrl+C to exit ---{Back.RESET}{Fore.RESET}"]
        s = self.system_stats
        freq_str = f"{s['cpu_frequency'].current:.0f}MHz" if s['cpu_frequency'] else "N/A"
        lines.append(f"{Fore.LIGHTBLUE_EX}Cores:{Fore.RESET} {s['cpu_cores_physical']} Physical, {s['cpu_cores_logical']} Logical | {Fore.LIGHTBLUE_EX}Freq:{Fore.RESET} {freq_str}")
        
        vm, sm = s['virtual_memory'], s['swap_memory']
        lines.append(f"{Fore.LIGHTBLUE_EX}RAM:{Fore.RESET} {format_bytes(vm.used, is_rate=False)}/{format_bytes(vm.total, is_rate=False)} ({vm.percent:.1f}%) | {Fore.LIGHTBLUE_EX}SWAP:{Fore.RESET} {format_bytes(sm.used, is_rate=False)}/{format_bytes(sm.total, is_rate=False)} ({sm.percent:.1f}%)")
        
        lines.append(f"{Fore.LIGHTBLUE_EX}DISK READ:{Fore.RESET} {format_bytes(s['disk_read_rate']):>10} | {Fore.LIGHTBLUE_EX}DISK WRITE:{Fore.RESET} {format_bytes(s['disk_write_rate']):>10}")

        for part in s['disk_partitions']:
            usage = part['usage']
            lines.append(f"{Fore.LIGHTBLUE_EX}Disk ({part['mountpoint']}):{Fore.RESET} {format_bytes(usage.used, is_rate=False)}/{format_bytes(usage.total, is_rate=False)} ({usage.percent:.1f}%)")

        core_strings = [f"{Fore.LIGHTBLUE_EX}Core {i}:{Fore.RESET} {(Fore.RED if usage > 75.0 else '')}{usage:5.2f}%" for i, usage in enumerate(s['per_cpu_usage'])]
        lines.append(f"{Fore.LIGHTBLUE_EX}CPU Total:{Fore.RESET} {s['overall_cpu']:5.2f}% | {Fore.LIGHTBLUE_EX}MEM:{Fore.RESET} {s['overall_mem']:5.2f}% | {Fore.LIGHTBLUE_EX}NET SENT:{Fore.RESET} {format_bytes(s['net_sent_rate']):>10} | {Fore.LIGHTBLUE_EX}NET RECV:{Fore.RESET} {format_bytes(s['net_recv_rate']):>10}")
        lines.append(" | ".join(core_strings))
        return lines

    def _format_processes(self):
        """Formats the process list section."""
        lines = [f"{Back.LIGHTBLUE_EX}{' ' * 80}{Back.RESET}",
                 f"{Fore.LIGHTBLUE_EX}{'PID':>7} {'PROCESS NAME':<35} {'CPU %':>7} {'MEM %':>7} {'READ/s':>10} {'WRITE/s':>10}{Fore.RESET}"]
        
        for i, proc in enumerate(self.top_processes[:self.args.number]):
            read_str = format_bytes(proc.get('read_rate'), is_rate=True)
            write_str = format_bytes(proc.get('write_rate'), is_rate=True)
            cpu_color = Fore.RED if proc['cpu_percent'] > 75.0 else ""
            bg_color = Back.LIGHTBLACK_EX if i % 2 == 0 else Back.RESET
            lines.append(f"{bg_color}{proc['pid']:>7} {proc['name']:<35.35} {cpu_color}{proc['cpu_percent']:>7.2f}{Fore.RESET} {proc['memory_percent']:>7.2f} {read_str:>10} {write_str:>10}{Back.RESET}")
        
        lines.append(f"{Back.LIGHTBLUE_EX}{' ' * 80}{Back.RESET}")
        return lines

    def _format_system_info(self):
        """Formats the 'Other System Information' section."""
        lines = ["--- Other System Information ---"]
        s = self.system_stats

        lines.append(f"{Fore.LIGHTBLUE_EX}Boot Time:{Fore.RESET} {datetime.fromtimestamp(s['boot_time']).strftime('%Y-%m-%d %H:%M:%S')}")

        if s['users']:
            lines.append(f"{Fore.LIGHTBLUE_EX}Users:{Fore.RESET}")
            for user in s['users']:
                lines.append(f"  - {user.name:<15} from {user.host or 'N/A':<15} since {datetime.fromtimestamp(user.started).strftime('%H:%M')}")
        else:
            lines.append(f"{Fore.LIGHTBLUE_EX}Users:{Fore.RESET} No users logged in.")

        for sensor_type in ['temperatures', 'fans', 'battery']:
            sensor_key = f'sensors_{sensor_type}'
            label = sensor_type.capitalize()
            if s[sensor_key]:
                lines.append(f"{Fore.LIGHTBLUE_EX}{label}:{Fore.RESET}")
                if sensor_type == 'temperatures':
                    for name, entries in s[sensor_key].items():
                        lines.append(f"  {name}:")
                        for entry in entries:
                            lines.append(f"    - {entry.label or 'N/A'}: Current={entry.current:.1f}°C, High={entry.high:.1f}°C, Critical={entry.critical:.1f}°C")
                elif sensor_type == 'fans':
                    for name, entries in s[sensor_key].items():
                        lines.append(f"  {name}:")
                        for entry in entries:
                            lines.append(f"    - {entry.label or 'N/A'}: {entry.current} RPM")
                elif sensor_type == 'battery':
                    battery = s[sensor_key]
                    if battery.secsleft == psutil.POWER_TIME_UNLIMITED: secsleft_str = "Unlimited"
                    elif battery.secsleft == psutil.POWER_TIME_UNKNOWN: secsleft_str = "Unknown"
                    else:
                        mins, secs = divmod(battery.secsleft, 60)
                        hours, mins = divmod(mins, 60)
                        secsleft_str = f"{int(hours)}h {int(mins)}m"
                    lines.append(f"  {battery.percent:.1f}% | Time Left: {secsleft_str} | Plugged: {'Yes' if battery.power_plugged else 'No'}")
            else:
                lines.append(f"{Fore.LIGHTBLUE_EX}{label}:{Fore.RESET} N/A (or not supported)")
        return lines

    def _format_network_info(self):
        """Formats the 'Network Details' section if requested."""
        if not self.args.network:
            return []
        
        lines = ["--- Network Details ---"]
        s = self.system_stats
        
        conn_stats = {}
        for conn in s.get('net_connections', []):
            conn_stats[conn.status] = conn_stats.get(conn.status, 0) + 1
        lines.append(f"{Fore.LIGHTBLUE_EX}Connections:{Fore.RESET} {' | '.join([f'{k}:{v}' for k, v in conn_stats.items()])}")

        if_addrs, if_stats = s.get('net_if_addrs', {}), s.get('net_if_stats', {})
        for iface, addrs in if_addrs.items():
            lines.append(f"{Back.LIGHTBLACK_EX}{Fore.WHITE} Interface: {iface} {Back.RESET}")
            for addr in addrs:
                if addr.family == socket.AF_INET: lines.append(f"  {Fore.LIGHTBLUE_EX}IP Address:{Fore.RESET} {addr.address}")
                elif addr.family == psutil.AF_LINK: lines.append(f"  {Fore.LIGHTBLUE_EX}MAC Address:{Fore.RESET} {addr.address}")
            
            if iface in if_stats:
                stats = if_stats[iface]
                status = f"{Fore.GREEN}UP{Fore.RESET}" if stats.isup else f"{Fore.RED}DOWN{Fore.RESET}"
                duplex_map = {psutil.NIC_DUPLEX_FULL: "Full", psutil.NIC_DUPLEX_HALF: "Half", psutil.NIC_DUPLEX_UNKNOWN: "Unknown"}
                lines.append(f"  {Fore.LIGHTBLUE_EX}Stats:{Fore.RESET} Status: {status}, Speed: {stats.speed}Mb, Duplex: {duplex_map[stats.duplex]}")
        return lines

    def _log_to_csv(self, timestamp):
        """Writes the current data to the CSV file."""
        if not self.csv_writer:
            return
        s = self.system_stats
        for proc in self.top_processes[:self.args.number]:
            self.csv_writer.writerow([
                timestamp, s['overall_cpu'], s['overall_mem'], s['net_sent_rate'], s['net_recv_rate'],
                proc['pid'], proc['name'], proc['cpu_percent'], proc['memory_percent'],
                proc.get('read_rate', 0.0), proc.get('write_rate', 0.0)
            ])

    def run(self):
        """Main application loop."""
        try:
            while True:
                loop_start_time = time.time()

                self._gather_system_stats()
                self._gather_process_stats()

                output_lines = []
                output_lines.extend(self._format_header())
                output_lines.extend(self._format_processes())
                output_lines.extend(self._format_system_info())
                output_lines.extend(self._format_network_info())

                self._log_to_csv(loop_start_time)

                os.system('cls' if os.name == 'nt' else 'clear')
                print("\n".join(output_lines))

                work_duration = time.time() - loop_start_time
                sleep_time = max(0, self.args.interval - work_duration)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\nExiting RealNerdStats.")
        finally:
            if self.csv_file:
                self.csv_file.close()
                print(f"{Fore.GREEN}Successfully saved log to {self.args.export}{Fore.RESET}")

def main():
    """Main entry point for the script."""
    args = parse_arguments()
    monitor = RealNerdStats(args)
    monitor.run()

if __name__ == "__main__":
    main()
