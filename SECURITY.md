# Home Assistant Webhook Alexa Skill

**Security**

Use of this project requires that you make your Home Assistant server reachable from the public Internet. Obviously this is a potential security risk, however there are various ways of reducing/mitigating risks.

*Obscurity*

Security via Obscurity is never secure, but its the initial part.

Firstly, don't make the hostname/IP address of your forwarded Home Assistant server well known, if you are using a dynamic DNS service like duckdns.org then make it something not obvious and not easily guessable.

Secondly, don't make the names of your webhooks easily guessable. I've used an example of webhook_open_gates, but a non-guessable one like webhook_12341208hASDljk32 is better.

Thirdly, the default URL for retriving the list of webhooks is /hass_webhooks.json but you can change this to something more obscure

*Limiting access*

You can limit access to the webhook URLs so that only AWS Lambda servers can call them. To do this, run the build_aws_lambda_ips_conf.py script (after editing it to select your Lambda hosting region) and when you run build_webhooks_conf.py specify "aws_only"

*Using SSL*

You can configure the OpenResty proxy to support SSL. To do this, obtain a suitable SSL certificate or create a self-signed one, then edit nginx.conf and 

1. Change
```
listen 8124;
  to
listen 8124 ssl;
```
2. Add
```
ssl_certificate     /etc/ssl/certs/your_cert.pem;
ssl_certificate_key /etc/ssl/private/your_key.pem;

ssl_protocols       TLSv1.2 TLSv1.3;
ssl_ciphers         HIGH:!aNULL:!MD5;

# (Optional) Strong security headers
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
```

*Protect webhooks and JSON file via basic auth*

```
$ sudo apt-get install apache2-utils  # if not already installed
$ htpasswd -cb /home/nginxproxy/.htpasswd hass hasshook
```
Obviously don't now use hass and hasshook!

then to each /location configuration item in the webhooks.conf file add
```
auth_basic "Restricted";
auth_basic_user_file /etc/nginx/.htpasswd;
```
Running the build_webhooks_conf.py script with the parameter "basic_auth" will do this for you.

You can also add the above lines to the server block in nginx.conf if you prefer.

Then 
- Restart the docker container
- Go back into the Alexa Developer console
- In the skill, edit config.py and put the username and password into AUTH_USERNAME and AUTHPASSWORD
- Save the skill code, and redeploy


Make your own decision as to which of these, if any, you want to implement. I made the decision to not use SSL and to use Basic Authentication.

