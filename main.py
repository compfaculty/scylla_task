import argparse
import statistics
import string
import subprocess
import threading
from datetime import timedelta
from timeit import default_timer as timer
from typing import List, Dict

from pyparsing import Word, nums, Suppress, restOfLine, alphanums

lock = threading.RLock()
aggregated_summary = []


def parse_output(output: str) -> Dict:
    """ parse container output
    :param output: stress tool output
    :return:
    """
    test_data = {}

    # Define pyparsing elements
    colon = Suppress(":")
    value = Word(nums + "," + ".")
    label = Word(alphanums + string.whitespace + '.', excludeChars=":")
    line = label + colon + value + restOfLine

    # Skip lines until "Results:" line is encountered
    lines = output.strip().split("\n")
    i = 0
    for i, l in enumerate(lines):
        if "Results:" in l.strip():
            break
    result_table = "\n".join(lines[i + 1:])
    # Parse lines after "Results:"
    for line_match in line.searchString(result_table):
        key = line_match[0].strip()
        value = line_match[1].strip().replace(',', '.')
        test_data[key] = value
    return test_data


def run_stress_command(node_ip: str, duration: int = 10, threads: int = 10):
    """ run stress command
    :param node_ip: docker node IP
    :param duration: duration of test , sec
    :param threads: number of threads
    :return:
    """
    command = f"docker exec some-scylla cassandra-stress write duration={duration}s " \
              f"-rate threads={threads} -node {node_ip}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    data = parse_output(result.stdout)

    with lock:
        aggregated_summary.append(data)


def run_threads(node_ip: str, durations: List[int], threads_number: int = 10):
    """
    create and start the test threads
    :return:
    """
    threads = []
    for duration in durations:
        thread = threading.Thread(target=run_stress_command, kwargs={
            "node_ip": node_ip,
            "duration": duration,
            "threads": threads_number
        })
        thread.start()
        threads.append(thread)
    # Wait for all threads to finish
    for thread in threads:
        thread.join()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="The Analysis program")
    parser.add_argument(
        "--threads_number",
        type=int,
        default=10,
        help="Number of threads (default: 10)",
    )
    parser.add_argument(
        "--duration",
        nargs="+",
        type=int,
        required=True,
        help="List of durations for each thread",
    )
    parser.add_argument(
        "--node_ip",
        type=str,
        required=True,
        help="IP address of the node",
    )
    args = parser.parse_args()
    if len(args.duration) != args.threads_number:
        parser.error("The number of durations should be equal to the number of threads")

    op_rate_sum = 0.0
    latency_max = []
    latency_mean = []
    latency99_mean = []

    start = timer()

    run_threads(node_ip=args.node_ip, durations=args.duration, threads_number=args.threads_number)

    for ret in aggregated_summary:
        if not ret:
            continue
        op_rate_sum += float(ret["Op rate"])
        latency_mean.append(float(ret["Latency mean"]))
        latency99_mean.append(float(ret["Latency 99th percentile"]))
        latency_max.append(float(ret["Latency max"]))

    print(f"Number of threads: {len(args.duration)}")
    print(f"Op rate sum: {round(op_rate_sum, 2)} op/s")
    print(f"Latency max std dev: {round(statistics.stdev(latency_max), 2)} ms")
    print(f"Latency mean:  {statistics.mean(latency_mean)} ms")
    print(f"Latency 99 mean:  {statistics.mean(latency99_mean)} ms")
    print(f"Elapsed : {timedelta(seconds=timer() - start)} sec")
