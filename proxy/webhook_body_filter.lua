local payloads = require("webhook_payloads")

local name = ngx.ctx.webhook_name or "unknown"
local status = ngx.ctx.status or 0
local message = payloads[name]

ngx.log(ngx.ERR, "[body_filter] webhook: ", name)
ngx.log(ngx.ERR, "[body_filter] status: ", status)
ngx.log(ngx.ERR, "[body_filter] arg[1]: ", ngx.arg[1] or "<nil>")
ngx.log(ngx.ERR, "[body_filter] arg[2] (eof): ", tostring(ngx.arg[2]))

-- Only inject body at end of stream
if status == 200 and message and ngx.arg[2] then
  ngx.arg[1] = '{"status":"ok","message":"' .. message .. '"}'
end

