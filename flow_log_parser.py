import csv
import os
import ipaddress
import logging
import argparse
from datetime import datetime

# Set up logging configuration
logging.basicConfig(level=logging.INFO,  # Set to DEBUG for detailed logs; use INFO for less verbosity
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("program_log.txt"),
                              logging.StreamHandler()])

current_folder = os.path.dirname(os.path.abspath(__file__))

# Initialize an empty dictionary to store the port-protocol pairs
port_protocol_dict = {}

# Function to read the CSV and create the port-protocol dictionary
def build_port_protocol_dict(filename):
    with open(filename, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            decimal = row['Decimal'].strip()
            keyword = row['Keyword'].strip()

            if '-' in decimal:
                print(f"Skipping row with port range: {decimal}")
                continue  # Skip this row
            try:
                key = int(decimal)  # Convert the decimal (port) to an integer
                value = keyword.lower()  # Convert the keyword (protocol) to lowercase
                port_protocol_dict[key] = value
            except ValueError:
                print(f"Skipping row with invalid decimal: {decimal}")

    return port_protocol_dict

# Load the lookup table from CSV file with case normalization and error logging
def load_lookup_table(filename):
    logging.info("Loading lookup table...")
    lookup_table = {}

    with open(filename, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header
        for line_num, row in enumerate(reader, start=2):  # Start at line 2 to account for header
            if len(row) != 3:
                logging.warning(f"Lookup table error at line {line_num}: Incorrect number of columns - {row}")
                continue

            try:
                dstport = int(row[0].strip())
                protocol = row[1].strip().lower()
                tag = row[2].strip().lower()

                if not (0 <= dstport <= 65535):
                    logging.warning(f"Lookup table error at line {line_num}: Invalid port number - {row}")
                    continue

                lookup_table[(dstport, protocol)] = tag
                logging.debug(f"Added entry to lookup table: {(dstport, protocol)} -> {tag}")
            except ValueError as e:
                logging.error(f"Lookup table parsing error at line {line_num}: Error parsing row - {row}. Error: {e}")

    logging.info("Lookup table loaded successfully.")
    return lookup_table

# Validate flow log entry
def validate_flow_log_entry(entry):
    try:
        fields = entry.strip().split()
        if len(fields) != 14:
            return False, "Incorrect number of fields"

        version, account_id, interface_id, srcaddr, dstaddr, srcport, dstport, protocol, packets, bytes_, start, end, action, log_status = fields

        if version != '2':
            return False, "Invalid version"
        if not (account_id.isdigit() and len(account_id) == 12):
            return False, "Invalid account ID"
        if not (interface_id.startswith('eni-') and len(interface_id) == 12):
            return False, "Invalid interface ID"
        try:
            ipaddress.ip_address(srcaddr)
            ipaddress.ip_address(dstaddr)
        except ValueError:
            return False, "Invalid IP address"
        if not (0 <= int(srcport) <= 65535) or not (0 <= int(dstport) <= 65535):
            return False, "Invalid port number"
        if int(protocol) not in port_protocol_dict:  # Check protocol in the built dictionary
            return False, "Invalid protocol"
        if int(packets) < 0 or int(bytes_) < 0:
            return False, "Invalid packets or bytes count"
        if not (start.isdigit() and end.isdigit() and int(end) >= int(start)):
            return False, "Invalid timestamps"
        if action not in {"ACCEPT", "REJECT"}:
            return False, "Invalid action"
        if log_status not in {"OK", "NODATA", "SKIPDATA"}:
            return False, "Invalid log status"

        return True, "Valid entry"
    except Exception as e:
        return False, f"Error in flow log validation: {e}"

# Process flow logs to generate tag counts
def process_flow_logs(lookup_table, flow_log_file):
    tag_counts = {}
    port_protocol_counts = {}

    with open(flow_log_file, 'r') as file:
        for line_num, line in enumerate(file, start=1):
            is_valid, message = validate_flow_log_entry(line)
            
            if not is_valid:
                logging.warning(f"Flow log error on line {line_num}: {message}")
                continue
            
            parts = line.split()
            dstport = int(parts[6])
            protocol_number = int(parts[7])
            protocol = port_protocol_dict.get(protocol_number, 'unknown').lower()
            tag = lookup_table.get((dstport, protocol), 'untagged')
            # Update tag counts
            if tag in tag_counts:
                tag_counts[tag] += 1
            else:
                tag_counts[tag] = 1

            port_protocol_key = (dstport, protocol)
            port_protocol_counts[port_protocol_key] = port_protocol_counts.get(port_protocol_key, 0) + 1

    # Generate output file name
    output_file = f"output_results_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

    # Write the output to a file
    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file)

        # Write Tag Counts section
        writer.writerow(['Tag Counts: '])
        writer.writerow(['Tag', 'Count'])
        writer.writerows(tag_counts.items())

        # Blank row for separation
        writer.writerow([])

        # Write Port/Protocol Counts section
        writer.writerow(['Port/Protocol Combination Counts: '])
        writer.writerow(['Port', 'Protocol', 'Count'])
        writer.writerows([(port, protocol, count) for (port, protocol), count in port_protocol_counts.items()])

    logging.info(f"Tag counts and port/protocol counts written to {output_file}")


def main():
    # Set up argparse for handling command-line arguments
    parser = argparse.ArgumentParser(description='Process flow logs with a custom lookup table and flow logs.')
    build_port_protocol_dict('input_files/protocol_numbers.csv')

    # Add arguments
    parser.add_argument('--lookuptable', type=str, default=os.path.join(current_folder, 'input_files/lookup_table.csv'),
                        help='Path to the lookup table CSV file (default: "lookup_table.csv" in the current folder)')
    parser.add_argument('--flowlogs', type=str, default=os.path.join(current_folder, 'input_files/flow_logs.txt'),
                        help='Path to the flow logs file (default: "default_flow_logs.txt" in the current folder)')

    # Parse arguments
    args = parser.parse_args()

    # Build port-protocol dictionary
    lookup_table = load_lookup_table(args.lookuptable)
    process_flow_logs(lookup_table, args.flowlogs)
    logging.info("Program finished execution")


if __name__ == "__main__":
    main()
