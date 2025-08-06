local status = ngx.status
local name = ngx.ctx.webhook_name or "unknown"

-- Capture upstream status for body phase
ngx.ctx.status = status

-- Only override if status is 200 and we have a known webhook
if status == 200 and require("webhook_payloads")[name] then
  ngx.header["Content-Length"] = nil
  ngx.header["Content-Type"] = "application/json"
end

