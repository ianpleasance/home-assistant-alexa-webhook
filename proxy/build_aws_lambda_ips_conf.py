import requests

LAMBDA_REGION = "eu-west-1"  # change to your Lambda region
OUTFILE = "aws_lambda_ips.conf"

url = "https://ip-ranges.amazonaws.com/ip-ranges.json"
data = requests.get(url).json()

with open(OUTFILE, "w") as f:
    # Add test IP (example only)
    f.write("allow 203.0.113.10;\n")

    for prefix in data["prefixes"]:
        if prefix["service"] == "LAMBDA" and prefix["region"] == LAMBDA_REGION:
            f.write(f"allow {prefix['ip_prefix']};\n")
        if prefix["service"] == "AMAZON" and prefix["region"] == LAMBDA_REGION:
            f.write(f"allow {prefix['ip_prefix']};\n")

    f.write("deny all;\n")

print(f"Wrote Lambda IP ranges to {OUTFILE}")

