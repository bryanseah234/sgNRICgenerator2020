import barcode
from barcode.writer import ImageWriter
from barcode.codex import Code39
import os
import sys
import string
import re
import json
import logging
from tqdm import tqdm
import time
from pathlib import Path

from download_path_manager import prompt_for_download_path
from utils import is_nric_valid


# --- Configuration ---
LOG_FILE = 'barcode_generator.log'
CHECKPOINT_FILE = 'barcode_progress.json'
# BARCODE_DIR is now exclusively for the output barcodes, not for logs.
# It will be set by user input.

# Determine the script's own directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 1. Logging Setup ---
def setup_logging():
    """Configures the logging for the script, saving the log file to the script's directory."""
    log_path = os.path.join(SCRIPT_DIR, LOG_FILE) # Log file path is now relative to script location

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(log_path), # Log file always goes here
                            logging.StreamHandler()
                        ])
    logging.info("Barcode generation script started.")

# --- 2. Checkpointing Functions ---
# Checkpoint file will also be saved in the script's directory for consistency
def save_checkpoint(last_prefix_number, last_suffix_char_index, year_double_digit):
    """Saves the current progress to a JSON checkpoint file in the script's directory."""
    checkpoint_data = {
        'year_double_digit': year_double_digit,
        'last_prefix_number': last_prefix_number,
        'last_suffix_char_index': last_suffix_char_index,
        'timestamp': time.time()
    }
    checkpoint_path = Path(SCRIPT_DIR) / CHECKPOINT_FILE # Checkpoint path is now relative to script location
    try:
        with open(str(checkpoint_path), 'w') as f:
            json.dump(checkpoint_data, f, indent=4)
        logging.debug(f"Checkpoint saved: Number={last_prefix_number}, Suffix Index={last_suffix_char_index}")
    except IOError as e:
        logging.error(f"Failed to save checkpoint to {checkpoint_path}: {e}")

def load_checkpoint(year_double_digit):
    """Loads previous progress from the checkpoint file in the script's directory."""
    checkpoint_path = os.path.join(SCRIPT_DIR, CHECKPOINT_FILE) # Checkpoint path is now relative to script location
    if os.path.exists(checkpoint_path):
        try:
            with open(str(checkpoint_path), 'r') as f:
                checkpoint_data = json.load(f)
            # Validate if the checkpoint is for the same year
            if checkpoint_data.get('year_double_digit') == year_double_digit:
                logging.info(f"Checkpoint loaded: Last number processed = {checkpoint_data.get('last_prefix_number')}, "
                             f"Last suffix index = {checkpoint_data.get('last_suffix_char_index')}")
                return checkpoint_data.get('last_prefix_number', 0), checkpoint_data.get('last_suffix_char_index', 0)
            else:
                logging.warning("Checkpoint found for a different year. Starting from scratch.")
                return 0, 0
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error loading checkpoint file {checkpoint_path}: {e}. Starting from scratch.")
            return 0, 0
    logging.info("No checkpoint found. Starting from scratch.")
    return 0, 0

# --- NRIC Validation is imported from utils.py ---

# --- Modified NRIC Generation with Progress and Checkpointing ---
def generate_nric_barcodes(year_double_digit, save_path):
    """
    Generates valid NRIC barcodes with progress tracking and resume capability.
    :param year_double_digit: The two-digit year for the NRIC prefix (e.g., '01' for 2001).
    :param save_path: The directory to save the barcodes.
    :return: A list of valid NRICs generated.
    """
    setup_logging() # Logging is now initialized using SCRIPT_DIR

    valid_only = []
    prefix_base = f"T{year_double_digit}"
    suffix_chars = string.ascii_uppercase
    total_suffix_chars = len(suffix_chars)
    total_numbers = 100000 # 0 to 99999

    # Load starting points from checkpoint file in SCRIPT_DIR
    start_number, start_suffix_char_index = load_checkpoint(year_double_digit)

    # Calculate total iterations for tqdm
    total_iterations = (total_numbers * total_suffix_chars)
    initial_progress = (start_number * total_suffix_chars) + start_suffix_char_index

    logging.info(f"Starting NRIC barcode generation for year {year_double_digit}. Total potential iterations: {total_iterations}")
    logging.info(f"Resuming from number: {start_number}, suffix index: {start_suffix_char_index}")

    # Using tqdm for progress tracking
    with tqdm(initial=initial_progress, total=total_iterations, unit="barcode",
              desc="Generating Barcodes") as pbar:

        for i in range(start_number, total_numbers):
            numbers = str(i).zfill(5)
            # Determine starting suffix index for current 'i'
            current_suffix_start_index = start_suffix_char_index if i == start_number else 0

            for s_idx in range(current_suffix_start_index, total_suffix_chars):
                s = suffix_chars[s_idx]
                temp_nric = prefix_base + numbers + s

                try:
                    if is_nric_valid(temp_nric):
                        code39 = Code39(temp_nric, writer=ImageWriter(), add_checksum=False)

                        # Sanitize filename: remove problematic characters
                        sanitized_temp = re.sub(r'[^\w.-]', '_', temp_nric).strip()
                        filename_base = Path(save_path) / sanitized_temp # Without extension
                        filename_to_save = filename_base.with_suffix(".png")  # still a Path object
                        
                        # Check if file already exists before saving to avoid re-generating
                        if not filename_to_save.exists():
                            code39.save(str(filename_base))
                            valid_only.append(temp_nric)
                            logging.debug(f"Generated barcode for: {temp_nric}")
                        else:
                            logging.debug(f"Barcode for {temp_nric} already exists. Skipping.")
                            valid_only.append(temp_nric) # Still add to list if already generated

                except Exception as e:
                    logging.error(f"Error processing NRIC {temp_nric}: {e}", exc_info=True)
                    pbar.set_postfix_str(f"Error at {temp_nric}")

                finally:
                    # Update progress bar
                    pbar.update(1)

                    # Save checkpoint periodically
                    # Example: Save every 1000 iterations or at the end of each number block
                    if (pbar.n % 1000 == 0) or \
                       (s_idx == total_suffix_chars - 1 and i == total_numbers - 1): # Last iteration
                        save_checkpoint(i, s_idx, year_double_digit)
                        logging.debug(f"Checkpoint saved at NRIC: {temp_nric}")

            # Reset start_suffix_char_index after the first iteration of 'i'
            if i == start_number:
                start_suffix_char_index = 0

    logging.info("Barcode generation complete.")
    # Clean up checkpoint file on successful completion
    checkpoint_path = os.path.join(SCRIPT_DIR, CHECKPOINT_FILE) # Referencing SCRIPT_DIR
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        logging.info("Checkpoint file removed upon successful completion.")

    return valid_only




# --- Main execution ---
def main():
    print("=========================================")
    print("   Singapore NRIC Barcode Generator      ")
    print("=========================================")
    print("1. Generate for a specific NRIC")
    print("2. Generate for a specific Year (e.g., 2000)")
    print("3. Generate for a Range of Years (e.g., 2000-2020)")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice not in ['1', '2', '3']:
        print("Invalid choice. Exiting.")
        sys.exit(1)
        
    if choice == '1':
        specific_nric = input("Enter the NRIC (e.g., T0123456A): ").strip().upper()
        if not is_nric_valid(specific_nric):
            print("Invalid NRIC format or checksum. Exiting.")
            sys.exit(1)
            
        path_str = prompt_for_download_path(context="NRIC barcodes", out_path=None)
        save_dir = Path(path_str).resolve()
        save_dir.mkdir(parents=True, exist_ok=True)
        
        setup_logging()
        
        try:
            code39 = Code39(specific_nric, writer=ImageWriter(), add_checksum=False)
            sanitized_temp = re.sub(r'[^\w.-]', '_', specific_nric).strip()
            filename_base = save_dir / sanitized_temp
            code39.save(str(filename_base))
            print(f"✅ Successfully generated barcode for {specific_nric} at {filename_base}.png")
        except Exception as e:
            print(f"❌ Error generating barcode: {e}")
            
    elif choice == '2':
        year = input("Enter the 4-digit year (e.g., 2001): ").strip()
        if len(year) != 4 or not year.isdigit():
            print("Invalid year format. Exiting.")
            sys.exit(1)
            
        path_str = prompt_for_download_path(context=f"NRIC barcodes for {year}", out_path=None)
        save_dir = Path(path_str).resolve()
        save_dir.mkdir(parents=True, exist_ok=True)
        
        year_double_digit = year[-2:]
        generate_nric_barcodes(year_double_digit, save_dir)
        
    elif choice == '3':
        year_range = input("Enter the year range (e.g., 2000-2020): ").strip()
        try:
            start_year, end_year = map(int, year_range.split('-'))
        except ValueError:
            print("Invalid range format. Use YYYY-YYYY. Exiting.")
            sys.exit(1)
            
        if start_year > end_year:
            print("Start year cannot be greater than end year. Exiting.")
            sys.exit(1)
            
        path_str = prompt_for_download_path(context=f"NRIC barcodes for {start_year}-{end_year}", out_path=None)
        save_dir = Path(path_str).resolve()
        save_dir.mkdir(parents=True, exist_ok=True)
        
        for yr in range(start_year, end_year + 1):
            year_str = str(yr)
            year_double_digit = year_str[-2:]
            generate_nric_barcodes(year_double_digit, save_dir)

if __name__ == "__main__":
    main()