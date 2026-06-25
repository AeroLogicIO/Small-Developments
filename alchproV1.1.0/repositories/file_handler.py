# alchPRO/repositories/file_handler.py
import os
import csv

class FileHandler:
    @staticmethod
    def get_root_dir():
        # Goes up one level from 'repositories' to 'alchPRO'
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def load_profiles():
        profiles = []
        file_path = os.path.join(FileHandler.get_root_dir(), 'alch_profiles.txt')
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        name = line.strip()
                        if name and name not in profiles:
                             profiles.append(name)
            except Exception as err:
                print(f"Error loading profiles: {err}")
        return profiles

    @staticmethod
    def save_profiles(profiles):
        file_path = os.path.join(FileHandler.get_root_dir(), 'alch_profiles.txt')
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for p in profiles:
                    f.write(f"{p}\n")
        except Exception as err:
            print(f"Error saving profiles: {err}")

    @staticmethod
    def load_history(profiles):
        history_logs = []
        file_path = os.path.join(FileHandler.get_root_dir(), 'alch_history.csv')
        if not os.path.exists(file_path):
            return history_logs

        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                if not reader.fieldnames:
                    return history_logs

                for row in reader:
                    try:
                        qty_val = int(row.get('qty', 0))
                        cost_val = int(row.get('cost_paid', 0))
                        nat_val = int(row.get('nat_cost', 0))
                        profit_val = int(row.get('batch_profit', 0))
                    except ValueError:
                        continue

                    prof_flags = {}
                    for p in profiles:
                        val = row.get(p, "0")
                        prof_flags[p] = (val == "1")

                    history_logs.append({
                        'time': row.get('time', ''),
                        'name': row.get('name', 'Unknown'),
                        'qty': qty_val,
                        'cost_paid': cost_val,
                        'nat_cost': nat_val,
                        'batch_profit': profit_val,
                        'profiles': prof_flags
                    })
        except Exception as err:
             print(f"Error reading history: {err}")
             
        return history_logs

    @staticmethod
    def save_history(history_logs, profiles):
        file_path = os.path.join(FileHandler.get_root_dir(), 'alch_history.csv')
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['time', 'name', 'qty', 'cost_paid', 'nat_cost', 'batch_profit'] + profiles
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for log in history_logs:
                    row_data = {
                        'time': log['time'],
                        'name': log['name'],
                        'qty': log['qty'],
                        'cost_paid': log['cost_paid'],
                        'nat_cost': log.get('nat_cost', 0),
                        'batch_profit': log['batch_profit']
                    }
                    for p in profiles:
                        row_data[p] = "1" if log['profiles'].get(p, False) else "0"
                    
                    writer.writerow(row_data)
        except Exception as err:
            print(f"Error saving history: {err}")

    @staticmethod
    def purge_history_file():
        file_path = os.path.join(FileHandler.get_root_dir(), 'alch_history.csv')
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as err:
                print(f"Error purging local history file: {err}")