import subprocess
import os

TEST_DIR = os.path.dirname(__file__)
DATA = os.path.join(TEST_DIR, "data")
SCOPEFORGE = os.path.join(os.path.dirname(TEST_DIR), "ScopeForge.py")

def run_scopeforge(in_file, out_file, tmp_path, extra_args=None):
    args = ["python3", SCOPEFORGE, os.path.join(DATA, in_file), os.path.join(DATA, out_file), "-o", str(tmp_path)]
    if extra_args:
        args += extra_args
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result, tmp_path

def check_scope_files(output_dir, expected_ips):
    # Check aggregated scope
    with open(output_dir / "scope_cleaned") as f:
        agg_lines = set(f.read().splitlines())
    assert len(agg_lines) > 0

    # Check all individual IPs
    all_ip_file = output_dir / "scope_cleaned_every_ip_listed"
    assert all_ip_file.exists()
    with open(all_ip_file) as f:
        ips = set(f.read().splitlines())
    assert ips == expected_ips

def test_basic_aggregation(tmp_path):
    result, output_dir = run_scopeforge("in_basic", "out_basic", tmp_path, ["--all-addresses"])
    expected = {"10.0.0.1", "10.0.0.2"}
    check_scope_files(output_dir, expected)

def test_summary_only(tmp_path):
    args = ["--summary-only"]
    result, _ = run_scopeforge("in_basic", "out_basic", tmp_path, extra_args=args)
    assert b"Remaining in-scope after exclusion" in result.stdout

def test_all_addresses_output(tmp_path):
    result, output_dir = run_scopeforge("in_basic", "out_basic", tmp_path, ["--all-addresses"])
    expected = {"10.0.0.1", "10.0.0.2"}
    check_scope_files(output_dir, expected)

def test_range_input(tmp_path):
    result, output_dir = run_scopeforge("in_range_format", "out_range_format", tmp_path, ["--all-addresses"])
    expected = {"10.10.10.1", "10.10.10.2"}
    check_scope_files(output_dir, expected)

def test_full_exclusion_fails(tmp_path):
    result, _ = run_scopeforge("in_all_excluded", "out_all_excluded", tmp_path, ["--fail-on-empty-scope"])
    assert result.returncode == 2
    assert b"Final scope is empty after exclusion" in result.stdout

def test_output_files_exist(tmp_path):
    result, output_dir = run_scopeforge("in_basic", "out_basic", tmp_path)
    assert (output_dir / "scope_cleaned").exists()
    assert (output_dir / "out_of_scope_addresses").exists()

def test_complex_mixed_scope(tmp_path):
    result, output_dir = run_scopeforge("in_complex", "out_complex", tmp_path, ["--all-addresses"])
    expected = {
        *[f"10.0.0.{i}" for i in range(16)],
        "192.168.0.1", "192.168.0.2", "192.168.0.5",
        "8.8.8.8"
    }
    check_scope_files(output_dir, expected)

def test_cidr_exclusion(tmp_path):
    result, output_dir = run_scopeforge("in_cidr", "out_cidr", tmp_path, ["--all-addresses"])
    expected = {
        "10.0.0.0", "10.0.0.1", "10.0.0.3",  # 10.0.0.2 excluded
        *[f"10.1.1.{i}" for i in range(128, 256)]  # 10.1.1.0/25 excluded
    }
    check_scope_files(output_dir, expected)
