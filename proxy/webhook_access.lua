-- Only safe operations in access phase
ngx.ctx.webhook_name = ngx.var.webhook_name or "unknown"
ngx.ctx.status = nil

