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


def parse_ip_line(ip_entry_line, include_network=False, include_broadcast=False):
    ip_entry_line = ip_entry_line.strip()
    if not ip_entry_line or ip_entry_line.startswith('#') or ip_entry_line.startswith('//'):
        return []

    if '-' in ip_entry_line:
        try:
            start_ip_str, end_ip_str = ip_entry_line.split('-')
            start_ip_obj = ipaddress.IPv4Address(start_ip_str.strip())
            end_ip_obj = ipaddress.IPv4Address(end_ip_str.strip())
            return [ipaddress.IPv4Address(ip) for ip in range(int(start_ip_obj), int(end_ip_obj) + 1)]
        except Exception as e:
            logging.warning(f"Failed to parse IP range '{ip_entry_line}': {e}")
            return []

    try:
        network = ipaddress.ip_network(ip_entry_line.strip(), strict=False)
        if include_network and include_broadcast:
            return list(network)
        hosts = list(network.hosts())
        if include_network:
            hosts.insert(0, network.network_address)
        if include_broadcast:
            hosts.append(network.broadcast_address)
        return hosts
    except ValueError:
        try:
            return [ipaddress.IPv4Address(ip_entry_line.strip())]
        except ValueError as e:
            logging.warning(f"Failed to parse IP '{ip_entry_line}': {e}")
            return []


def collect_ip_set(filepath, include_network=False, include_broadcast=False):
    ip_set = set()
    try:
        with open(filepath, 'r') as f:
            for line in f:
                ip_set.update(parse_ip_line(line, include_network, include_broadcast))
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading {filepath}: {e}")
        sys.exit(1)
    return ip_set


def aggregate_ip_set(ip_set):
    """Collapse a set of IPs to minimal CIDR blocks."""
    return list(ipaddress.collapse_addresses(sorted(ip_set, key=int)))


def write_list(file_path, entries):
    try:
        with open(file_path, 'w') as f:
            for entry in entries:
                f.write(str(entry) + '\n')
        logging.info(f"Written file: {file_path}")
    except Exception as e:
        logging.error(f"Failed writing {file_path}: {e}")
        sys.exit(1)


def build_argument_parser():
    parser = argparse.ArgumentParser(
        prog="ScopeForge",
        description="Build and refine in-scope and out-of-scope lists for pentesting."
    )
    parser.add_argument("in_scope_file", help="File of in-scope IPs/CIDRs/ranges")
    parser.add_argument("out_scope_file", help="File of out-of-scope IPs/CIDRs/ranges")
    parser.add_argument("-o", "--output-dir", default=".", help="Output directory")
    parser.add_argument("--all-addresses", action="store_true",
                        help="Dump every final IP individually")
    parser.add_argument("--summary-only", action="store_true",
                        help="Show counts only, no files")
    parser.add_argument("--fail-on-empty-scope", action="store_true",
                        help="Exit code 2 if final scope empty")
    parser.add_argument("--include-network", action="store_true",
                        help="Include .0 network addresses when expanding CIDRs")
    parser.add_argument("--include-broadcast", action="store_true",
                        help="Include broadcast addresses when expanding CIDRs")
    return parser


def main():
    setup_logging()
    args = build_argument_parser().parse_args()

    output_dir = os.path.abspath(os.path.expanduser(args.output_dir))
    if not args.summary_only:
        os.makedirs(output_dir, exist_ok=True)

    in_ips = collect_ip_set(args.in_scope_file, args.include_network, args.include_broadcast)
    out_ips = collect_ip_set(args.out_scope_file, args.include_network, args.include_broadcast)

    final_ips = in_ips - out_ips

    logging.info(f"In-scope count: {len(in_ips)}")
    logging.info(f"Excluded count: {len(out_ips)}")
    logging.info(f"Final count: {len(final_ips)}")

    if args.fail_on_empty_scope and not final_ips:
        logging.error("Empty final scope, exiting with code 2")
        sys.exit(2)

    if args.summary_only:
        return

    # Write aggregated in-scope
    cleaned_cidrs = aggregate_ip_set(final_ips)
    write_list(os.path.join(output_dir, "scope_cleaned"), cleaned_cidrs)

    # Optionally dump individual
    if args.all_addresses:
        write_list(os.path.join(output_dir, "scope_cleaned_every_ip_listed"), sorted(final_ips, key=int))

    # Always write aggregated exclusions
    aggregated_out = aggregate_ip_set(out_ips)
    write_list(os.path.join(output_dir, "out_of_scope_aggregated"), aggregated_out)


if __name__ == "__main__":
    main()
