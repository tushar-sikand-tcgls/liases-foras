import argparse
import time
import re
from datetime import datetime

def parse_log_file(log_file_path, last_position):
    """
    Parses the log file for Python traceback errors since the last read position.
    """
    errors = []
    try:
        with open(log_file_path, 'r') as f:
            f.seek(last_position)
            new_content = f.read()
            last_position = f.tell()

            # This regex is designed to find multi-line blocks that look like Python tracebacks.
            # It looks for one or more '  File "..."' lines followed by a final 'Error: ...' line.
            error_pattern = re.compile(
                r"((?:^  File \".+\"\n(?:    .+\n)?)+^[a-zA-Z_].*?Error:.*$)",
                re.MULTILINE
            )
            
            for match in error_pattern.finditer(new_content):
                full_traceback = match.group(1).strip()
                
                # The error message is the last line of the traceback block
                error_message = full_traceback.split('\n')[-1]
                
                errors.append({
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "error_code": "N/A",
                    "error_message": error_message,
                    "stack_trace": full_traceback,
                    "recommended_solution": "Pending Analysis",
                    "confidence": "N/A"
                })

    except FileNotFoundError:
        print(f"Error: Log file not found at {log_file_path}")
        return [], 0
    except Exception as e:
        print(f"An error occurred while reading the log file: {e}")
        return [], last_position

    return errors, last_position

def format_as_ascii_table(headers, data, existing_content=""):
    """
    Formats data into a simple ASCII table.
    Appends to existing content if provided.
    """
    # Don't re-render headers if content already exists
    is_new_file = not existing_content.strip()
    
    # Calculate column widths from headers and new data
    col_widths = [len(h) for h in headers]
    for row in data:
        # Truncate long stack traces for display purposes
        row[3] = (row[3][:200] + '...') if len(row[3]) > 200 else row[3]
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    def create_row(items, widths):
        return " | ".join(str(item).ljust(width) for item, width in zip(items, widths))

    def create_separator(widths):
        return "-+-".join("-" * width for width in widths)

    output_lines = []
    if is_new_file:
        output_lines.append(create_row(headers, col_widths))
        output_lines.append(create_separator(col_widths))

    for row in data:
        output_lines.append(create_row(row, col_widths))
        
    # Adjust table lines to match new widths if file is not new
    if not is_new_file:
        # This is a simplified append. A more complex implementation would
        # re-render the entire table to ensure perfect alignment if column
        # widths change dramatically. For this use case, appending is sufficient.
        pass

    return "\n".join(output_lines) + "\n" if output_lines else ""


def main(log_file, output_file):
    """
    Main function to poll the log file and write errors to the output file.
    """
    # Use a dictionary to track the last known size/position to handle log rotation if needed.
    # For this script, we'll just track position.
    last_position = 0
    
    print(f"Monitoring log file: {log_file}")
    print(f"Writing errors to: {output_file}")

    try:
        while True:
            # On first run, check from the start. On subsequent runs, from the last position.
            errors, new_position = parse_log_file(log_file, last_position)
            last_position = new_position

            if errors:
                print(f"Found {len(errors)} new error(s) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                try:
                    with open(output_file, 'r') as f:
                        existing_content = f.read()
                except FileNotFoundError:
                    existing_content = ""

                headers = ["Timestamp", "Error Code", "Error Message", "Stack Trace", "Recommended Solution", "Confidence"]
                
                data_rows = [
                    [
                        e["timestamp"],
                        e["error_code"],
                        e["error_message"],
                        e["stack_trace"].replace('\n', ' '),
                        e["recommended_solution"],
                        e["confidence"]
                    ] for e in errors
                ]

                table_chunk = format_as_ascii_table(headers, data_rows, existing_content)

                with open(output_file, 'a') as f:
                    f.write(table_chunk)
            
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor a log file for Python tracebacks and log them to a file.")
    parser.add_argument("--log-file", required=True, help="The path to the log file to monitor.")
    parser.add_argument("--output-file", required=True, help="The path to the file to write the error table.")
    
    args = parser.parse_args()
    
    main(args.log_file, args.output_file)