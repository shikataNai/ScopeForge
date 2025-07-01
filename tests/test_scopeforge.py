import subprocess
import os
import ipaddress

test_dir = os.path.dirname(__file__)
DATA = os.path.join(test_dir, "data")
SCOPEFORGE = os.path.join(os.path.dirname(test_dir), "ScopeForge.py")


def run_scopeforge(in_file, out_file, tmp_path, extra_args=None):
    args = ["python3", SCOPEFORGE,
            os.path.join(DATA, in_file), os.path.join(DATA, out_file),
            "-o", str(tmp_path)]
    if extra_args:
        args += extra_args
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result, tmp_path


def read_file_set(path):
    with open(path) as f:
        return set(f.read().splitlines())


def test_basic_aggregation_and_exclusions(tmp_path):
    result, out = run_scopeforge("in_basic", "out_basic", tmp_path, ["--all-addresses"])
    # Aggregated in-scope
    agg = read_file_set(out / "scope_cleaned")
    assert agg == {"10.0.0.1/32", "10.0.0.2/32"}
    # Individual IPs
    ips = read_file_set(out / "scope_cleaned_every_ip_listed")
    assert ips == {"10.0.0.1", "10.0.0.2"}
    # Aggregated exclusions
    excl = read_file_set(out / "out_of_scope_aggregated")
    assert excl == {"10.0.0.3/32"}


def test_summary_only(tmp_path):
    result, _ = run_scopeforge("in_basic", "out_basic", tmp_path, ["--summary-only"])
    assert b"Final count:" in result.stdout


def test_include_network_and_broadcast(tmp_path):
    result, out = run_scopeforge("in_cidr", "out_cidr", tmp_path,
                                 ["--all-addresses", "--include-network", "--include-broadcast"])
    ips = read_file_set(out / "scope_cleaned_every_ip_listed")
    # 10.0.0.0/30 yields .0,.1,.2,.3; exclude .2 by default
    assert {"10.0.0.0", "10.0.0.1", "10.0.0.3"}.issubset(ips)


def test_range_input(tmp_path):
    result, out = run_scopeforge("in_range_format", "out_range_format", tmp_path,
                                 ["--all-addresses"])
    agg = read_file_set(out / "scope_cleaned")
    assert {"10.10.10.1/32", "10.10.10.2/32"} <= agg


def test_full_exclusion_fails(tmp_path):
    result, _ = run_scopeforge("in_all_excluded", "out_all_excluded", tmp_path,
                                ["--fail-on-empty-scope"])
    assert result.returncode == 2
    assert b"exiting with code 2" in result.stdout


def test_complex_mixed_scope(tmp_path):
    result, out = run_scopeforge("in_complex", "out_complex", tmp_path,
                                 ["--all-addresses"])
    ips = read_file_set(out / "scope_cleaned_every_ip_listed")
    # in_complex: 10.0.0.0/28 expands to hosts .1 through .14 by default
    expected = {f"10.0.0.{i}" for i in range(1, 15)}
    # 192.168.0.1-5 minus .3-4
    expected |= {"192.168.0.1", "192.168.0.2", "192.168.0.5"}
    # 8.8.8.8 should remain
    expected.add("8.8.8.8")
    assert ips == expected


def test_aggregated_exclusions(tmp_path):
    _, out = run_scopeforge("in_complex", "out_complex", tmp_path)
    excl_agg = read_file_set(out / "out_of_scope_aggregated")
    # out_complex excludes 10.0.1.0/30 => hosts 10.0.1.1-10.0.1.2
    assert {"10.0.1.1/32", "10.0.1.2/32"} <= excl_agg
    # range exclusion
    assert {"192.168.0.3/32", "192.168.0.4/32"} <= excl_agg
    # single
    assert "172.16.0.10/32" in excl_agg
