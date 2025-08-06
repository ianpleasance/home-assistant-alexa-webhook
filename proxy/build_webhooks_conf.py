import csv
import json
import sys
from pathlib import Path

INPUT_CSV = "webhooks.csv"
CONF_FILE = "webhooks.conf"
JSON_FILE = "webhooks.json"
LUA_PAYLOAD_FILE = "webhook_payloads.lua"

HA_BASE_URL = "https://192.168.0.123:8123"

INCLUDE_AWS_ONLY = len(sys.argv) > 1 and sys.argv[1].lower() == "aws_only"
INCLUDE_BASIC_AUTH = len(sys.argv) > 1 and sys.argv[1].lower() == "basic_auth"


def load_webhooks(csv_file):
    webhooks = []
    with open(csv_file, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 4:
                continue
            name, method, path, message = map(str.strip, row)
            webhooks.append({
                "name": name,
                "method": method.upper(),
                "path": path,
                "message": message
            })
    return webhooks


def write_json(webhooks):
    entries = [{"name": w["name"], "method": w["method"], "path": w["path"]} for w in webhooks]
    with open(JSON_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def write_lua_payload_table(webhooks):
    with open(LUA_PAYLOAD_FILE, "w") as f:
        f.write("return {\n")
        for w in webhooks:
            key = w["name"]
            val = w["message"].replace('"', '\\"')
            f.write(f'  ["{key}"] = "{val}",\n')
        f.write("}\n")


def write_nginx_conf(webhooks):
    with open(CONF_FILE, "w") as f:
        # Static JSON listing route
        f.write(f"""location /hass_webhooks.json {{\n""")
        if INCLUDE_BASIC_AUTH:
                f.write("    auth_basic \"Restricted\";\n")
                f.write("    auth_basic_user_file /etc/nginx/.htpasswd;\n")
        f.write(f"""    default_type application/json;
    root /usr/share/nginx/html;
    try_files /{Path(JSON_FILE).name} =404;
}}\n\n""")

        for w in webhooks:
            f.write(f"""location {w["path"]} {{
    limit_except {w["method"]} {{
        deny all;
    }}\n""")

            if INCLUDE_AWS_ONLY:
                f.write("    include /etc/nginx/aws_lambda_ips.conf;\n")
            if INCLUDE_BASIC_AUTH:
                f.write("    auth_basic \"Restricted\";\n")
                f.write("    auth_basic_user_file /etc/nginx/.htpasswd;\n")

            f.write(f"""    set $webhook_name {w["name"]};

    access_by_lua_file /etc/nginx/webhook_access.lua;
    header_filter_by_lua_file /etc/nginx/webhook_header_filter.lua;
    body_filter_by_lua_file /etc/nginx/webhook_body_filter.lua;

    proxy_pass_request_body on;
    proxy_set_header Content-Type $http_content_type;
    proxy_pass {HA_BASE_URL}{w["path"]};
}}\n\n""")


def build_all():
    webhooks = load_webhooks(INPUT_CSV)
    write_json(webhooks)
    write_lua_payload_table(webhooks)
    write_nginx_conf(webhooks)

    print("Generated:")
    print(f"  - {CONF_FILE}")
    print(f"  - {JSON_FILE}")
    print(f"  - {LUA_PAYLOAD_FILE}")
    if INCLUDE_AWS_ONLY:
        print("🔐 AWS IP restriction: ENABLED (using aws_lambda_ips.conf)")


if __name__ == "__main__":
    build_all()

