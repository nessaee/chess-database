import re
import sys

# Regex patterns for extracting metric fields from the metrics block
metrics_pattern = re.compile(
    r'Elapsed Time:\s+(?P<elapsed_time>\S+)\s+seconds.*?'
    r'Files Processed:\s+(?P<files_processed>\d+).*?'
    r'Files Failed:\s+(?P<files_failed>\d+).*?'
    r'Games Processed:\s+(?P<games_processed>\d+).*?'
    r'Games Failed:\s+(?P<games_failed>\d+).*?'
    r'Database Operations:\s+(?P<db_operations>\d+).*?'
    r'Database Retries:\s+(?P<db_retries>\d+).*?'
    r'Average Processing Speed:\s+(?P<avg_speed>\S+)\sgames/second.*?'
    r'Current Processing Rate:\s+(?P<current_rate>\S+)\sgames/second.*?'
    r'Average File Processing Time:\s+(?P<avg_file_time>\S+)\sseconds.*?'
    r'Success Rate:\s+(?P<success_rate>\S+)%', 
    re.DOTALL
)

def parse_metrics_blocks(log_content):
    # Extract all metric blocks
    blocks = [m.groupdict() for m in metrics_pattern.finditer(log_content)]
    return blocks

def compute_overall_metrics(blocks):
    # Aggregate metrics
    total_files_processed = sum(int(b['files_processed']) for b in blocks)
    total_files_failed = sum(int(b['files_failed']) for b in blocks)
    total_games_processed = sum(int(b['games_processed']) for b in blocks)
    total_db_ops = sum(int(b['db_operations']) for b in blocks)
    total_db_retries = sum(int(b['db_retries']) for b in blocks)

    # Compute averages from all blocks
    avg_processing_speed = sum(float(b['avg_speed']) for b in blocks) / len(blocks)
    avg_current_rate = sum(float(b['current_rate']) for b in blocks) / len(blocks)
    avg_file_processing_time = sum(float(b['avg_file_time']) for b in blocks) / len(blocks)
    avg_success_rate = sum(float(b['success_rate']) for b in blocks) / len(blocks)

    return {
        'total_files_processed': total_files_processed,
        'total_files_failed': total_files_failed,
        'total_games_processed': total_games_processed,
        'total_db_operations': total_db_ops,
        'total_db_retries': total_db_retries,
        'avg_processing_speed': avg_processing_speed,
        'avg_current_rate': avg_current_rate,
        'avg_file_processing_time': avg_file_processing_time,
        'avg_success_rate': avg_success_rate
    }

if __name__ == "__main__":
    # Usage: python parse_metrics.py logfile.log
    logfile = sys.argv[1]

    with open(logfile, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = parse_metrics_blocks(content)
    if not blocks:
        print("No Pipeline Metrics blocks found.")
        sys.exit(0)

    overall = compute_overall_metrics(blocks)

    print("Overall Metrics:")
    print("----------------")
    print(f"Total Files Processed: {overall['total_files_processed']}")
    print(f"Total Files Failed: {overall['total_files_failed']}")
    print(f"Total Games Processed: {overall['total_games_processed']}")
    print(f"Total Database Operations: {overall['total_db_operations']}")
    print(f"Total Database Retries: {overall['total_db_retries']}")
    print(f"Average Processing Speed: {overall['avg_processing_speed']:.2f} games/second")
    print(f"Average Current Rate: {overall['avg_current_rate']:.2f} games/second")
    print(f"Average File Processing Time: {overall['avg_file_processing_time']:.2f} seconds")
    print(f"Average Success Rate: {overall['avg_success_rate']:.2f}%")
