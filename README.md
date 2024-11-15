# Flow Log Tagging Program

## Requirements

- **Python version**: 3.x
- **Libraries**: `csv`, `os`, `ipaddress`, `logging`
- **Input files**:
  - **Flow Log File**: A plain text file (ASCII) containing flow logs (up to 10MB in size).
  - **Lookup Table**: A plain text (ASCII) file containing port/protocol/tag mappings (up to 10,000 mappings). This file should have three columns: destination port, protocol, and tag. Tags can map to multiple port/protocol combinations.
  - **Protocol File**: A `protocol_numbers.csv` file that contains data from the IANA standard for port-protocol mapping.
  
- **Output**: The output will be written to a CSV file (`output_file.csv`) containing:
  - **Tag Counts**: Total count for each tag.
  - **Port/Protocol Counts**: Total count for each port/protocol combination.

## Assumptions

- The **destination port** is chosen for port/protocol combinations in this program.
- The program currently supports **flow log version 2** only. However, scaling for versions 3, 4, and others is not an issue, as we would only need to check the length of the flow log line.
- The program will skip lines that are not in the correct format and log warnings/errors for those, continuing execution.

## How It Works

1. **Flow Log Validation**: The program validates flow log entries to ensure they conform to the expected structure. Invalid entries are logged and skipped.
2. **Lookup Table Processing**: The program processes the lookup table to map port/protocol combinations to tags. Any invalid lookup entries are logged and skipped.
3. **Output Generation**: The program generates counts for tags and port/protocol combinations and writes them to an output CSV file.

## Execution Instructions

1. **Prepare your files**:
   - Place your `flow_logs.txt` and `lookup_table.csv` files in the same directory as the script.
   - Ensure that the `protocol_numbers.csv` file (from the IANA standard) is available.

2. **Run the script**:
   - Execute the Python script by running the following command in your terminal:
     ```bash
     python flow_log_parser.py
     ```

   The program will process the input files and generate the `output_file.csv` in the same directory.

3. **Provide Your Own Files**:
   - To use your own files, simply replace the default `flow_logs.txt` and `lookup_table.csv` with your own versions. Ensure they follow the required format:
     - **Flow Log File**: 14 fields per line, with port and protocol numbers.
     - **Lookup Table File**: Three columns: destination port, protocol, and tag.
   
4. **Output Location**:
   - The program will generate the output file (`output_file.csv`) in the same directory as the script.

## Error Logging and Warnings

- **Invalid Flow Log Entries**: The program will log a warning for any flow log entries that don't conform to the expected format and continue processing the rest.
- **Invalid Lookup Table Entries**: Any entries with incorrect columns or invalid port/protocol/tag mappings will be logged with a warning.

## Example

Assume you have a flow log with port/protocol combinations and you want to map them to tags using a lookup table. For example:

**Flow Log (`flow_logs.txt`)**:
```python
2 1234567890 eni-abcdefg 192.168.1.1 10.0.0.1 12345 80 tcp 10 1000 1634657365 1634657400 ACCEPT OK ...
```

**Lookup Table (`lookup_table.csv`)**:
``` python
80, tcp, sv_P1 443, tcp, sv_P2
```
The output (`output_file.csv`) would contain:
``` python
Tag Counts: 
Tag, Count 
sv_P1, 1 
sv_P2, 0

Port/Protocol Combination Counts: 
Port, Protocol, Count 
80, tcp, 1 443, tcp, 0
```

## Future Scaling

- Scaling to support other versions (3, 4, etc.) would primarily involve adjusting the flow log line length check, which is easy to implement in future versions. Currently, version 2 is fully supported.




