

# Home Assistant Webhook Alexa Skill

This project is designed to link Amazon Alexa's speech and Home Assistant (HASS) so that users can trigger simple and complex automations via HASS webhooks, and optionally pass parameters to them.

**Background**

There are other methods available that allow the integration of Alexa and Home Assistant - including the Nabu Casa service and the Home Assistant Alexa Integration. 

I chose not to use the Nabu Casa service because its a paid service and while it is good value I didn't need the other parts of the service. 

I chose not to use the Alexa Integration due to its complexity - it requires an AWS developer account and has a long setup process - and because it didn't allow automations to be run in the way that I wanted.


**Purpose**

The core of the project is an Alexa skill, which provides a flexible and secure way to interact with your Home Assistant instance using voice commands to call Home Assistant webhooks.

Instead of directly exposing your Home Assistant's webhook endpoint to the internet, all requests are routed through a hardened OpenResty proxy, which you will typically run as a Docker container.

The skill's primary function is to:

Listen for a custom invocation and command (e.g., "ask [skill name] to trigger [a webhook]").

Parse the spoken command to extract the webhook ID and any parameters.

Consult a configuration file hosted on the OpenResty proxy to determine the correct HTTP method (GET or POST) and path.

Send the final HTTP request, including a JSON payload for any parameters, to the OpenResty proxy.

Read the response from the proxy and provide a friendly voice response back to the user.

**Architecture**

The system is designed in a three-part architecture to enhance security, flexibility, and reliability.

The components used and the data flow are :-


1. Alexa User ---Voice Command--> Alexa Device
2. Alexa Device ---Voice Command--> Alexa Service
3. Alexa Service ---Intent Request--> Lambda Function
4. Lambda Function ---HTTP(S) Request---> OpenResty Proxy
5. OpenRestyProxy ---HTTP(S) Response with Configuration---> Lambda Function
6. AWS Lambda Function ---HTTP(S) Request---> OpenRestyProxy
7. OpenResty Proxy ---Internal Webhook Call---> Home Assistant<br>OpenResty Proxy ---HTTPS(S) Response with Speech Text---> Lambda Function
8. Home Assistant ---Automation Trigger---> Home Assistant Automation

*Alexa Service:* Transcribes the user's voice command and sends a structured request (an IntentRequest) to the AWS Lambda function.

*AWS Lambda Function*: The core logic of the Alexa skill. It receives the request, parses the spoken command for a webhook ID and parameters, and constructs an authenticated HTTP request.

*OpenResty Proxy*: OpenResty is an extended version of the nginx HTTP server with inbuilt Lua scripting capabilities. It receives the request from Lambda, verifies it, and securely forwards it to the Home Assistant instance. This proxy acts as a single point of entry and provides a layer of security and abstraction.

*Home Assistant*: The webhooks are received by Home Assistant, which then triggers the corresponding automations.

**Why Use an OpenResty Proxy?**

Using an OpenResty proxy between the Alexa skill and Home Assistant provides several key benefits:

Enhanced Security: It prevents the direct public exposure of your Home Assistant instance. The proxy can enforce strict security rules, such as only accepting requests from the Alexa Lambda function and validating them before forwarding. It can also add Basic Auth requirements to protect endpoints.

Abstraction and Flexibility: The proxy hides the internal IP address and port of your Home Assistant server. You can change your Home Assistant's internal URL without needing to update the Alexa skill.

Centralized Configuration: All webhook configurations (methods, paths) are stored in a single hass_webhooks.json file on the proxy, making them easy to manage without redeploying the Lambda code.

Custom Logic: The Lua scripts in OpenResty allow for advanced request handling, such as custom authentication, rate limiting, or logging, before a request ever reaches Home Assistant. 

Insertion of custom responses: Home Assistant has a "fire and forget" policy regarding webhooks, the HTTP(S) trigger to launch the webhook completes immediately and does not return a success or failure status nor does Home Assistant allow any output from the webhook to be returned to the invoker. Use of Lua within OpenResty allows us to hook into the HTTP chain and insert a custom response, effectively faking a response from the webhook which can be passed back to the Lambda as text to speak back to the user

**How to Use the Skill**

Once the skill is configured and running, you can use it with voice commands structured as follows:

"*Alexa, ask [Skill Invocation Name] to trigger [Webhook Command]*"

The [Webhook Command] can include parameters, which the skill will automatically parse and convert into a JSON payload for Home Assistant.

Example commands with no parameters

"*Alexa, ask hass webhook to trigger openmaingates*"

Sends a GET or POST request to the webhook configured as open_main_gates.

"*Alexa, ask hass webhook to trigger turnonlights*" 

Sends a GET request to the webhook configured as turn_on_lights.

Example commands with parameters

"*Alexa, ask hass webhook to trigger settemperature equals twenty three*"

Sends a POST request with {"temperature": "23"} to the webhook configured as settemperature.

"*Alexa, ask hass webhook to trigger lights with color red brightness one fifty*"

Sends a POST request with {"color": "red", "brightness": "150"} to the webhook configured as lights.


While you can use these voice commands as-is, to make them easier you'll probably want to add Alexa Routines to your account to remap them to easier voice calls. To do this you can run the Alexa App, Create a Routine, and then a "When" and a "Will" - for example "When:Voice:Open Gates" "Alexa Will:Customised:ask hass webhook to trigger opengates"


**OpenResty Proxy Setup via Docker**

The recommended way to deploy the OpenResty proxy is using Docker - manually or via docker-compose.

Prerequisites
- Docker (and optionally Docker Compose) installed.
- A publicly accessible domain name (e.g., your-proxy-domain.duckdns.org) or static IP address
- Incoming HTTP port access allowed by your ISP
- Your home router configured to forward an appropriate HTTP or HTTPS port to your Docker host

Files

docker-compose.yml: Defines the services (OpenResty).
launch.sh: Launcher shell script for people who don't use Docker Compose

nginx.conf: The main nginx configuration file.
openresty.conf: OpenResty-specific configuration file.

Lua scripts to control access and HTTP(S) request transformation
webhook_access.lua: The Lua script for custom access control (e.g., authenticating the request)
webhook_body_filter.lua: Lua script for processing the request body
webhook_header_filter.lua: Lua script for processing headers 
webhook_payloads.lua

aws_lambda_ips.conf: A list of known AWS IP addresses, optionally used to limit access to webhooks so that only AWS Lambda functions can call them
build_aws_lambda_ips_conf.py: Script to build the above

webhooks.csv: The primary file which defines names, paths, HTTP(S) methods, and response text for webhooks. This is the one that should be edited to add and remove webbooks
webhooks.conf: OpenResty location configurations, built from the above
webhooks.json: Static JSON file listing webhooks and their configuration, built from the above
build_webhooks_conf.py: Script to turn webhooks.csv into webhooks.conf and webhooks.json and webhook_payloads.lua


See INSTALLATION.md for full instructions

See SECURITY.md for a discussion on potential security issues and how you might want to mitigate them.


**Version** 

- 1.00 - Initial public release

