

# Home Assistant Webhook Alexa Skill

**Step-by-Step Instructions**

1. Clone this repository:
```
$ git clone https://github.com/ianpleasance/home-assistant-alexa-webhook
$ cd alexa-webhook/proxy
```

2. Configure and launch the OpenResty proxy

Create a user to run the proxy under, I'm using 
- User: nginxproxy
- Home directory: /home/nginxproxy
- Logging into /logs/nginxproxy
- Proxy listening on port 8124 via plain HTTP

```
$ sudo adduser nginxproxy  
$ sudo usermod -aG docker nginxproxy  
$ sudo su -<br>
% su - nginxproxy<br>
$ mkdir /logs/nginxproxy<br>
```

Edit either docker-compose.yml or the launch.sh script and change the listening port and paths.

If you want to restrict access to your webhooks to AWS Lambda server IPs then edit build_aws_lambda_ips_conf.py to define the region that you'll be deploying the Lambda into, then run ./build_aws_lamdba_ips_conf.py

Then credit webhooks.csv, the format of this is one line per webhook with 4 fields.

```
Field 1: The name of the webhook as it will be invoked by the Alexa skill, this is used so that you can have a different (friendly) name for the webhook in the command than the actual HASS webhook ID.
Field 2: GET or POST. The method via which the webbook should be invoked from the lambda.
Field 3: The path on your HASS server of the webhook
Field 4: (Optional) The text to return to the lambda for speaking 
```

for example

```
open_gate,GET,/api/webhook/webhook_open_gates"Opened Gates"
close_gate,GET,/api/webhook/webhook_close_gates"Closed Gates"
all_lights_on,GET,/api/webhook/webook_all_lights_on,"OK All Lights On"
bedtime,POST,/api/webhook/webhook_bedtime,"Bedtime routine started"
lights_dim,POST,/api/webhook/webhook_lights_dim,"Lights dimmed"
```

Edit build_webhooks_conf.py and specify the internal URL of your HASS server in "HA_BASE_URL"

Run ./build_webhooks_conf.py - if you want to limit access to the webhooks to AWS Lambda servers then do ./build_webhooks_conf.py aws_only

Run docker-compose up -d, or ./launch.sh

This will start the OpenResty container.

3. Test the OpenResty proxy

Verify that the webhooks JSON file is served

```
$ curl http://localhost:8124/hass_webhooks.json
[
  {
    "name": "open_gates",
    "method": "GET",
    "path": "/api/webhook/webhook_open_gates"
  },
  {
    "name": "close_gates",
    "method": "GET",
    "path": "/api/webhook/webhook_close_gates"
  },
  etc
]
```

Verify that a webhook is successfully triggered

```
$ curl -X GET http://localhost:8124/api/webhook/webhook_open_gates
{"status":"ok","message":"Opened Gates"} 
```

4. Set up the Alexa Skill

Prerequisites: 
An Amazon Account - but presumably you already have this if you have any Alexa-powered devices!

Go to the Alexa Developer Console - https://developer.amazon.com/alexa/console/ask and login with the same email address that your Alexa-powered devices log into. It must match, as you'll be creating and running the skill as a private (non-published) skill.

Part A: Create the New Alexa Skill
- Click the "Create Skill" button (top right).
- Configure Basic Skill Information:
  - Skill Name: Enter Home Assistant Webhook.
  - Primary Locale: Select English (UK) (or your preferred English locale, e.g., English (US)).
- Click Next
- Choose Type Of Experience: Other
- Choose a model to add to your skill: Select Custom.
- Choose a Hosting services method to host the skill's backend resources: Select Alexa-Hosted (Python). This is Amazon's recommended way for ease of use, as it sets up and manages the AWS Lambda function for you.
- Choose a Hosting region to host in, e.g. EU (Ireland)
- Click "Create Skill".
- On the next screen, choose "Start from scratch".
- Click "Next".
- Click “Create Skill”
Part B: Build the Interaction Model (How Alexa Understands User Input)
This section defines what users can say to your skill and how Alexa maps those phrases to actions (intents).
- Set the Invocation Name:
- In the left-hand navigation, click on "Invocation"
- For "Skill Invocation Name", enter: hass webhook (This is the phrase users will say to open your skill, e.g., "Alexa, tell hass webhook open main gates").
- Click "Save" at the top.
- Define the WebhookIntent:
- In the left-hand navigation click on "Interaction Model" then "Intents".
- You'll see some pre-built Amazon intents (AMAZON.CancelIntent, AMAZON.HelpIntent, AMAZON.StopIntent, etc.).
- Delete the HelloWorld sample stuff
- Click the "Add Intent" button.
- Select "Create custom intent".
- Custom Intent Name: Enter WebhookIntent.
- Click "Create custom intent".
- Configure WebhookIntent Utterances and Slot:
- You are now on the WebhookIntent configuration page.
- Sample Utterances: Add the following phrases. As you type, {webhookId} will automatically be recognized as a slot (highlighted in yellow or orange). If not, you can manually select the word, click "Add Slot," and assign it the slot type.
```
  {webhookId} now
  trigger {webhookId}
  run {webhookId}
  execute {webhookId}
  ask {webhookId} to
```
- Configure Slots: In the "Intent Slots" section (below the utterances), you should see webhookId.
- For the Slot Type of webhookId, select AMAZON.SearchQuery from the dropdown menu. This is important for allowing flexible, multi-word webhook IDs.
- Click "Save" at the top.
- Build the Development Model: At the top of the left-hand navigation (or sometimes a blue button on the main content area), you will see a "Build Model" button. Click this.
- This process compiles your voice interaction model and might take a minute or two. Wait for it to complete.
Click “Build Skill”, and wait for successful completion

Part C: Add the Backend Code (AWS Lambda Function)
This is where you'll put the Python code that handles the logic of the skill.
- Using the top navigation bar, click Code to navigate to Code Editor:
- In the left-hand navigation, click on "Code".
- This will open an in-browser code editor for Alexa-Hosted Python Lambda function. 
- You should see a lambda_function.py file.
- Delete all the code thats already in the lambda_function.py
- Copy and paste the entire Python code from skill/hass_webhook.py
- Click Save

Part D: Ensure Dependencies are Present (requirements.txt):
- In the left-hand file browser (within the code editor), click on requirements.txt.
- Make sure these two lines are present in the file:
```
requests
urllib3
```
- If not then add them, and click on Save

Part E: Create a file config.py

Define these variables

```
WEBHOOK_CONFIG_URL = "http://[your-proxy-domain]/hass_webhooks.json"
WEBHOOK_TRIGGER_BASE_URL = "http://[your-proxy-domain]"
SSL_VERIFY = True
# Leave AUTH_USERNAME = "" to disable authentication
AUTH_USERNAME = "your_username"
AUTH_PASSWORD = "your_password"

```
- Save the file.

The configuration parameters are 

WEBHOOK_CONFIG_URL: This defines the full URL from which the hass webhooks JSON file is loaded. This can be HTTP or HTTPs
WEBHOOK_TRIGGER_BASE_URL: This defines the base URL to which the webhook paths in the webbooks.csv/webbooks.json will be appended. It can be HTTP or HTTPS, it should not have a trailing /. The reason that this URL is specified as well as the above is because you may wish to host the JSON file on a different web server. 
SSL_VERIFY: If using HTTPS, then you can leave this to True or set it to False to skip SSL certificate verification (for example if you are using a self-signed SSL certificate)
AUTH_USERNAME/AUTH_PASSWORD: If specified then the lambda will send HTTP Basic Auth headers on all calls. This allows you to lock down access to your webhooks.

Part F: Deploy the Lambda Function:
- Back in the code editor (on lambda_function.py), click the "Deploy" button.
This action saves your code, installs any specified dependencies from requirements.txt, and deploys your Lambda function. 
- Wait for the "Deployment successful" message. This can take a few minutes

Part 5: Test the Skill
- Click on Back to return to the Skills list and click on your skill name agaibn
- On the top navigation bar go to the Test Tab:
- Under the "Test is disabled for this Skill" dropdown, select Development.
- In the "Enter your query" text box, type: "run hass webhook" and press Enter or click "Send"
-  Alexa should say: "Welcome to Home Assistant Webhook. What webhook ID would you like to trigger?"
-  Select the name of one of your webhooks and trigger it by typing "trigger webhook_name" (where webhook_name is one of the webhook invocation names that you put in field  1 of the webhooks.csv file)
-  Or type "ask hass webhook to trigger webhook_name"
- The skill will
  - Attempt to fetch the hass_webhooks.json file from your OpenResty proxy
  - Find the name matching open_main_gates and determine its method and path.
  - Construct and call the full URL
  - The OpenResty proxy will handle that request, forward it to Home Assistant, get a response, and then return a JSON body like {"status":"ok","message":"Main gates are opening."} if 200 OK, or The request returned status code 404. if not.
  - You should see and hear a speech response
    - If successful (200 OK from proxy with a "message" field): Alexa should speak the value of the "message" field (e.g., "Main gates are opening.").
    - If successful but no "message" field: Alexa should say "Webhook 'open main gates' triggered successfully, but no message was provided."
    - If not successful (non-200 from proxy): Alexa should say "The request returned status code [HTTP Status Code]."
    - If the webhook ID isn't found in your JSON config: "I couldn't find a webhook with the ID 'open main gates'. Please check the ID and try again."

Debugging problems.

There are three places to check and debug if things aren't working
- The usual HASS logs, verify if your webhook/automation are being invoked
- The OpenResty proxy logs within /logs/nginxproxy (or wherever you put them).
- CloudWatch Logs: Go back to the "Code" tab. At the bottom, click the "CloudWatch logs" link. This will open AWS CloudWatch Logs in a new tab. Click on the latest log stream to see detailed logs from your Lambda function, including INFO messages about what the skill is doing, and ERROR messages if anything went wrong. 
