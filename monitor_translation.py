#!/usr/bin/env python3
"""
Monitor the translation process in real-time.
"""

import os
import time
import json
from pathlib import Path
import datetime

def monitor_translation():
    """Monitor the progress of the translation process."""
    
    input_file = "data/raw/senate_processes_20230201_to_20250521.json"
    output_file = "data/processed/senate_processes_20230201_to_20250521_es.json"
    temp_output_file = output_file + ".temp"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found.")
        return
    
    # Get total items in the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
            total_items = len(input_data)
            print(f"Input file has {total_items} items to translate.")
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    print("Starting monitoring...")
    print("Press Ctrl+C to stop monitoring.")
    
    try:
        while True:
            now = datetime.datetime.now().strftime("%H:%M:%S")
            
            # Check if final output file exists and is complete
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                file_size_mb = file_size / (1024 * 1024)
                
                # Check if file is complete
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        output_data = json.load(f)
                        items_translated = len(output_data)
                        progress = (items_translated / total_items) * 100
                        
                        print(f"[{now}] COMPLETED: {progress:.2f}% - {items_translated}/{total_items} items translated. File size: {file_size_mb:.2f} MB")
                        if items_translated >= total_items:
                            print("\n✅ Translation completed successfully!")
                            break
                except Exception as e:
                    # File might be being written to, just show file size
                    print(f"[{now}] File exists but cannot be read completely yet. File size: {file_size_mb:.2f} MB | Error: {e}")
            
            # Check if temp file exists (incremental progress)
            elif os.path.exists(temp_output_file):
                temp_file_size = os.path.getsize(temp_output_file)
                temp_file_size_mb = temp_file_size / (1024 * 1024)
                
                try:
                    with open(temp_output_file, 'r', encoding='utf-8') as f:
                        temp_data = json.load(f)
                        items_translated = len(temp_data)
                        progress = (items_translated / total_items) * 100
                        
                        # Get the latest log to show progress messages
                        log_message = get_latest_log_message()
                        
                        print(f"[{now}] IN PROGRESS: {progress:.2f}% - {items_translated}/{total_items} items translated.")
                        if log_message:
                            print(f"  > {log_message}")
                except Exception:
                    # Temp file might be being written to
                    print(f"[{now}] Translation in progress. Temp file size: {temp_file_size_mb:.2f} MB")
            else:
                # Check the logs directory for the latest log file
                log_message = get_latest_log_message()
                log_files = sorted(Path("logs").glob("*translation*.log"), key=os.path.getmtime)
                if log_files:
                    latest_log = log_files[-1]
                    log_size = os.path.getsize(latest_log)
                    print(f"[{now}] Translation in progress. Latest log: {latest_log.name} ({log_size/1024:.2f} KB)")
                    if log_message:
                        print(f"  > {log_message}")
                else:
                    print(f"[{now}] Waiting for translation to start...")
            
            time.sleep(5)  # Update every 5 seconds
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
        return
    except Exception as e:
        print(f"\nMonitoring error: {e}")
        return

def get_latest_log_message():
    """Get the latest translation log message about progress."""
    log_files = sorted(Path("logs").glob("*translation*.log"), key=os.path.getmtime)
    if not log_files:
        return None
    
    latest_log = log_files[-1]
    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Look for progress lines from the end
            for line in reversed(lines):
                if "Progress:" in line or "Saved progress:" in line or "item" in line:
                    return line.strip()
            # If no progress line found, return the last line
            return lines[-1].strip() if lines else None
    except Exception:
        return None
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    monitor_translation()
