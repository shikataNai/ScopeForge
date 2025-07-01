import ipaddress
import argparse
import os
import sys
import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )


def parse_ip_line(ip_entry_line):
    ip_entry_line = ip_entry_line.strip()
    if not ip_entry_line or ip_entry_line.startswith('#') or ip_entry_line.startswith('//'):
        return []

    if '-' in ip_entry_line:
        try:
            start_ip, end_ip = ip_entry_line.split('-')
            start_ip_obj = ipaddress.IPv4Address(start_ip.strip())
            end_ip_obj = ipaddress.IPv4Address(end_ip.strip())
            return [ipaddress.IPv4Address(ip) for ip in range(int(start_ip_obj), int(end_ip_obj) + 1)]
        except Exception as e:
            logging.warning(f"Failed to parse IP range '{ip_entry_line}': {e}")
            return []

    try:
        network = ipaddress.ip_network(ip_entry_line.strip(), strict=False)
        # Include all addresses including network and broadcast
        return list(network)
    except ValueError:
        try:
            return [ipaddress.IPv4Address(ip_entry_line.strip())]
        except ValueError as e:
            logging.warning(f"Failed to parse IP '{ip_entry_line}': {e}")
            return []


def collect_ip_set_from_file(filepath):
    all_ips = set()
    try:
        with open(filepath, 'r') as ip_file:
            for line in ip_file:
                all_ips.update(parse_ip_line(line))
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading file '{filepath}': {e}")
        sys.exit(1)
    return all_ips


def write_aggregated_scope_file(ip_set, output_path):
    try:
        aggregated_networks = list(ipaddress.collapse_addresses(sorted(ip_set, key=int)))
        with open(output_path, 'w') as f:
            for network in aggregated_networks:
                f.write(str(network) + '\n')
        logging.info(f"Aggregated scope written to: {output_path}")
    except Exception as e:
        logging.error(f"Failed to write aggregated scope: {e}")
        sys.exit(1)


def write_individual_ip_file(ip_set, output_path):
    try:
        with open(output_path, 'w') as f:
            for ip in sorted(ip_set, key=lambda ip: int(ip)):
                f.write(str(ip) + '\n')
        logging.info(f"All individual IPs written to: {output_path}")
    except Exception as e:
        logging.error(f"Failed to write individual IPs: {e}")
        sys.exit(1)


def build_argument_parser():
    parser = argparse.ArgumentParser(
        description="Create a refined scope by removing out-of-scope addresses from in-scope lists."
    )
    parser.add_argument("in_scope_file", help="File containing all in-scope IPs, CIDRs, or ranges")
    parser.add_argument("out_scope_file", help="File containing out-of-scope IPs, CIDRs, or ranges")
    parser.add_argument("-o", "--output-dir", default=".", help="Directory to write output files (default: current dir)")
    parser.add_argument("--all-addresses", action="store_true", help="Also output every individual IP to a separate file")
    parser.add_argument("--summary-only", action="store_true", help="Only display summary of in/out/final counts, no files written")
    parser.add_argument("--fail-on-empty-scope", action="store_true", help="Fail if final scope is empty after exclusion")
    return parser


def main():
    setup_logging()
    arg_parser = build_argument_parser()
    arguments = arg_parser.parse_args()

    resolved_output_directory = os.path.abspath(os.path.expanduser(arguments.output_dir))
    if not arguments.summary_only:
        os.makedirs(resolved_output_directory, exist_ok=True)

    all_in_scope_ips = collect_ip_set_from_file(arguments.in_scope_file)
    excluded_ips = collect_ip_set_from_file(arguments.out_scope_file)
    final_scope_ips = all_in_scope_ips - excluded_ips

    logging.info(f"In-scope addresses parsed: {len(all_in_scope_ips)}")
    logging.info(f"Out-of-scope addresses parsed: {len(excluded_ips)}")
    logging.info(f"Remaining in-scope after exclusion: {len(final_scope_ips)}")

    if arguments.fail_on_empty_scope and not final_scope_ips:
        logging.error("Final scope is empty after exclusion and --fail-on-empty-scope is set. Exiting.")
        sys.exit(2)

    if arguments.summary_only:
        return

    cleaned_scope_output = os.path.join(resolved_output_directory, "scope_cleaned")
    write_aggregated_scope_file(final_scope_ips, cleaned_scope_output)

    if arguments.all_addresses:
        every_ip_output = os.path.join(resolved_output_directory, "scope_cleaned_every_ip_listed")
        write_individual_ip_file(final_scope_ips, every_ip_output)

    exclusions_output = os.path.join(resolved_output_directory, "out_of_scope_addresses")
    write_individual_ip_file(excluded_ips, exclusions_output)


if __name__ == "__main__":
    main()
