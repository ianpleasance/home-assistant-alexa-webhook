#!/bin/bash

NAME='nginxproxy'
DETACHED='-d'
CONTAINER_TAG='openresty/openresty:1.21.4.1-0-alpine'
HOMEDIR='/home/nginxproxy'
LOGSDIR='/logs/nginxproxy'

VOLS="-v ${HOMEDIR}/nginx.conf:/etc/nginx/conf.d/default.conf:ro"
VOLS="${VOLS} -v ${HOMEDIR}/index.html:/usr/share/nginx/html/index.html"
VOLS="${VOLS} -v ${HOMEDIR}/aws_lambda_ips.conf:/etc/nginx/aws_lambda_ips.conf"
VOLS="${VOLS} -v ${HOMEDIR}/webhooks.conf:/etc/nginx/webhooks.conf"
VOLS="${VOLS} -v ${HOMEDIR}/webhook_access.lua:/etc/nginx/webhook_access.lua"
VOLS="${VOLS} -v ${HOMEDIR}/webhook_header_filter.lua:/etc/nginx/webhook_header_filter.lua"
VOLS="${VOLS} -v ${HOMEDIR}/webhook_body_filter.lua:/etc/nginx/webhook_body_filter.lua"
VOLS="${VOLS} -v ${HOMEDIR}/webhook_payloads.lua:/etc/nginx/webhook_payloads.lua"
VOLS="${VOLS} -v ${HOMEDIR}/webhooks.json:/usr/share/nginx/html/webhooks.json"
VOLS="${VOLS} -v ${HOMEDIR}/openresty.conf:/usr/local/openresty/nginx/conf/nginx.conf"
VOLS="${VOLS} -v ${HOMEDIR}/.htpasswd:/etc/nginx/.htpasswd"
VOLS="${VOLS} -v ${LOGSDIR}:/var/log/nginx"

RESTART='--restart=unless-stopped'
PORTS='-p 8124:8124'

docker run ${DETACHED} ${RESTART} ${PORTS} ${HST} ${ENV} -e TZ='Europe/London' ${VOLS} --name ${NAME} ${CONTAINER_TAG}

