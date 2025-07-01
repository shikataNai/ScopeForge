# ScopeForge

## Overview
ScopeForge is a command-line Python utility built to help penetration testers craft precise and usable lists of in-scope targets. Its primary purpose is to take a broad scope of IP addresses (often given as CIDRs or ranges) and remove any explicitly defined exclusions, resulting in a refined, actionable set of assets.

Instead of manually subtracting exclusions from client-provided scope files, ScopeForge automates the process. It parses in-scope and out-of-scope lists, removes excluded addresses, aggregates the remaining targets into the smallest possible set of CIDRs, and can optionally output every individual resolved IP.

This tool is ideal for preparing clean scope files for any assessment. 

---

## Features
- Accepts in-scope and out-of-scope input files in any mix of:
  - Single IPs (e.g., `10.0.0.1`)
  - CIDRs (e.g., `10.0.0.0/24`)
  - IP ranges (e.g., `10.0.0.1-10.0.0.10`)
- Aggregates resulting scope into CIDRs (`scope_cleaned`)
- Optionally outputs every single individual IP (`scope_cleaned_every_ip_listed`)
- Always logs all exclusions (`out_of_scope_addresses`)

---

## Usage

```bash
python3 ScopeForge.py in_scope_file out_scope_file [options]
```

### Positional Arguments:
- `all_addresses`: File containing the original full scope. This file includes all addresses.
- `out_of_scope_all_addresses`: File containing all exclusions to be removed from all_addresses

### Optional Arguments:
- `-o, --output-dir`: Directory to save output files (default: current directory)
- `--all-addresses`: Also output every IP individually to `scope_cleaned_every_ip_listed`

---

## Examples

### Basic usage:
```bash
python3 ScopeForge.py all_addresses out_of_scope_all_addresses
```
Outputs:
- `./scope_cleaned`
- `./out_of_scope_addresses`

### Save output to a custom directory:
```bash
python3 ScopeForge.py all_addresses out_of_scope_all_addresses -o ~/testing/targets/scope_cleaned
```

### Include every resolved IP in output:
```bash
python3 ScopeForge.py all_addresses out_of_scope_all_addresses --all-addresses
```
Outputs:
- `scope_cleaned`
- `scope_cleaned_every_ip_listed`
- `out_of_scope_addresses`

---

## Input File Format
Each input file should be a plain text file with one entry per line. Supported formats include:

### ✅ Valid entries:
- `10.0.0.1` — single IP address
- `10.0.0.0/24` — CIDR notation
- `10.0.0.1-10.0.0.25` — range format

### ❌ Invalid entries (will be ignored):
- Hostnames (e.g., `example.com`)
- Text descriptions or comments
- Malformed IPs (e.g., `10.0.0.999` or `abc.def.ghi.jkl`)

---

## Output Files
- `scope_cleaned`: Contains CIDR-aggregated final scope
- `scope_cleaned_every_ip_listed`: (only if `--all-addresses` is specified) contains every individual IP
- `out_of_scope_addresses`: Always generated to confirm excluded data

---

