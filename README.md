# ScopeForge

## Overview

ScopeForge is a command-line Python utility built to help penetration testers craft precise and usable lists of in-scope targets. Its primary purpose is to take a broad scope of IP addresses (often given as CIDRs or ranges) and remove any explicitly defined exclusions, resulting in a refined, actionable set of assets.

Instead of manually subtracting exclusions from client-provided scope files, ScopeForge automates the process. It parses in-scope and out-of-scope lists, removes excluded addresses, aggregates the remaining targets into the smallest possible set of CIDRs, and can optionally output every individual resolved IP. It also always outputs exclusions as aggregated CIDRs for clear visibility.

This tool is ideal for preparing clean scope files for any assessment.

---

## Features

* Accepts in-scope and out-of-scope input files in any mix of:
  * Single IPs (e.g., `10.0.0.1`)
  * CIDRs (e.g., `10.0.0.0/24`)
  * IP ranges (e.g., `10.0.0.1-10.0.0.10`)
* Aggregates resulting scope into CIDRs (`scope_cleaned`)
* Optionally outputs every single individual IP (`scope_cleaned_every_ip_listed`)
* Always aggregates exclusions into minimal CIDRs (`out_of_scope_aggregated`)
* **Summary-only** mode (`--summary-only`) to print counts without writing files
* **Fail-on-empty-scope** mode (`--fail-on-empty-scope`) to exit with error if final scope is empty
* **Include network address** (`--include-network`) to include `.0` addresses when expanding CIDRs
* **Include broadcast address** (`--include-broadcast`) to include broadcast (`.255`) when expanding CIDRs

---

## Usage

```bash
python3 ScopeForge.py <in_scope_file> <out_scope_file> [options]
```

### Positional Arguments

* `<in_scope_file>`        File containing all in-scope IPs, CIDRs, or ranges
* `<out_scope_file>`       File containing all exclusions to be removed from in-scope list

### Optional Arguments

* `-h, --help`                   Show help message and exit
* `-o, --output-dir <dir>`       Directory to save output files (default: current directory)
* `--all-addresses`              Also output every individual IP to `scope_cleaned_every_ip_listed`
* `--summary-only`               Only display summary of input, exclusions, and final counts; skip writing output files
* `--fail-on-empty-scope`        Exit with status 2 if the final cleaned scope is empty
* `--include-network`            Include `.0` network addresses when expanding CIDRs
* `--include-broadcast`          Include broadcast addresses when expanding CIDRs

---

## Examples

### Basic usage:

```bash
python3 ScopeForge.py all_addresses out_of_scope_file
```

Outputs in the current directory:

* `scope_cleaned`            — Aggregated final in-scope CIDRs
* `out_of_scope_aggregated`  — Aggregated exclusion CIDRs

### Save output to a custom directory:

```bash
python3 ScopeForge.py all_addresses out_of_scope_file -o ~/testing/targets/scope_cleaned
```

### Include every resolved IP in output

```bash
python3 ScopeForge.py all_addresses out_of_scope_file --all-addresses
```

Outputs additionally:

* `scope_cleaned`
* `scope_cleaned_every_ip_listed`
* `out_of_scope_aggregated`

### Include network and broadcast addresses

```bash
python3 ScopeForge.py all_addresses out_of_scope_file --include-network --include-broadcast
```

### Only show counts, no files

```bash
python3 ScopeForge.py all_addresses out_of_scope_file --summary-only
```

Example output:
```
In-scope entries      : 1024
Excluded entries      : 64
Final cleaned entries : 960
```

### Error on empty result:

```bash
python3 ScopeForge.py all_addresses out_of_scope_file --fail-on-empty-scope
```

Exits with status 2 and prints:
```
Error: Empty final scope, exiting with code 2
```

---

## Input File Format

Each input file should be a plain text file with one entry per line. Supported formats include:

### ✅ Valid entries

* `10.0.0.1` — single IP address
* `10.0.0.0/24` — CIDR notation
* `10.0.0.1-10.0.0.25` — range format

### ❌ Invalid entries (ignored)

* Hostnames (e.g., `example.com`)
* Text descriptions or comments
* Malformed IPs (e.g., `10.0.0.999` or `abc.def.ghi.jkl`)

---

## Output Files

* `scope_cleaned`                  — Contains CIDR-aggregated final scope
* `scope_cleaned_every_ip_listed`  — (only if `--all-addresses`) contains every individual IP
* `out_of_scope_aggregated`        — Contains exclusion CIDRs aggregated automatically

Use `--summary-only` to skip writing these files and `--fail-on-empty-scope` to enforce non-empty output.
