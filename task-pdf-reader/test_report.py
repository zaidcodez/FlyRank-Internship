import json
from report import get_report_data

if __name__ == "__main__":
    print(json.dumps(get_report_data(), indent=2))
