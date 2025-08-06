#
# V1.0 - Initial public release
# V0.3 - Support Basic Auth
# V0.2 - Support passing parameters to POSTs
# V0.1 - Initial working version
#
#
import logging
import os
import json # Import json to handle JSON responses
import ask_sdk_core.utils as ask_utils
import requests
import urllib3
import re
import base64

import config 

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_core.utils import is_request_type

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configuration using Environment Variables
# The URL for the webhook *configuration list* file (now JSON)
# This should point to your OpenResty proxy. Example: "https://your_proxy_domain.duckdns.org/hass_webhooks.json"
WEBHOOK_CONFIG_URL = config.WEBHOOK_CONFIG_URL

# The base URL for triggering individual webhooks on your OpenResty proxy.
# Example: "https://your_proxy_domain.duckdns.org/api/webhook"
WEBHOOK_TRIGGER_BASE_URL = config.WEBHOOK_TRIGGER_BASE_URL

# Get SSL_VERIFY setting from environment variables.
SSL_VERIFY = config.SSL_VERIFY

AUTH_USERNAME = config.AUTH_USERNAME
AUTH_PASSWORD = config.AUTH_PASSWORD

# Suppress the InsecureRequestWarning if SSL verification is turned off
if not SSL_VERIFY:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logger.warning("SSL verification is DISABLED. This is INSECURE for production environments.")
    
AUTH_HEADERS = {}
if AUTH_USERNAME:
    try:
        auth_string = f"{AUTH_USERNAME}:{AUTH_PASSWORD}"
        # Encode the username:password string in base64
        encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        AUTH_HEADERS = {"Authorization": f"Basic {encoded_auth}"}
        logger.info("Basic Authentication enabled for HTTP requests.")
    except Exception as e:
        logger.error(f"Failed to set up Basic Authentication headers: {e}")
        AUTH_HEADERS = {} # Ensure it's empty if an error occurs
else:
    logger.info("Basic Authentication not enabled (AUTH_USERNAME is empty).")

def _parse_key_value_parameters(param_string):
    """
    Parses a string like "param1=abc param2=def" or "param1 equals abc" into a dictionary.
    Handles multiple key=value pairs separated by spaces.
    Normalizes common spoken equivalents for '='.
    Supports quoted values (e.g., location="living room").
    """
    if not param_string:
        return None
    
    params_dict = {}
    
    # Normalize common spoken equivalents for '='
    normalized_param_string = param_string.replace(" equals ", "=").replace(" is ", "=")
    
    # This regex splits by spaces but keeps quoted strings (e.g., "living room") together.
    # It ensures that 'param="value with spaces"' is treated as one unit.
    pairs = re.findall(r'(?:[^\s"]|"(?:\\.|[^"])*")+', normalized_param_string)

    for pair in pairs:
        # Split each pair by the first '='
        parts = pair.split('=', 1)
        if len(parts) == 2:
            key = parts[0].strip().lower() # Normalize key to lowercase
            value = parts[1].strip()
            
            # Remove quotes from value if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            
            if key and value:
                params_dict[key] = value
        else:
            logger.warning(f"Malformed parameter pair found: '{pair}' in string '{param_string}'")
    
    return params_dict if params_dict else None


def _extract_webhook_id_and_params_from_utterance(utterance_string):
    """
    Parses the full utterance string (from the webhookId slot) to extract the
    actual webhook ID and any embedded parameters.
    Examples:
    - "lights" -> ("lights", None)
    - "open main gates" -> ("open_main_gates", None)
    - "lights with color red brightness 200" -> ("lights", {"color": "red", "brightness": "200"})
    - "trigger home assistant and set status equals away" -> ("home_assistant", {"status": "away"})
    """
    if not utterance_string:
        return None, None

    normalized_utterance = utterance_string.strip().lower()

    # Define common separators that indicate parameters are about to follow
    # Order matters: more specific/longer phrases first
    param_separators = [" and set ", " with ", " set ", " value ", " for "]

    webhook_id_part_raw = normalized_utterance
    parameters_part = None

    for sep in param_separators:
        if sep in normalized_utterance:
            parts = normalized_utterance.split(sep, 1) # Split only on the first occurrence
            webhook_id_part_raw = parts[0].strip()
            parameters_part = parts[1].strip()
            break # Found a separator, no need to check others

    # Normalize the extracted webhook ID part for lookup in your JSON config
    # This replaces spaces and periods with underscores
    webhook_id_for_lookup = webhook_id_part_raw.replace(" ", "_").replace(".", "_")

    parsed_params = None
    if parameters_part:
        # Pass the identified parameter string to our dedicated key-value parser
        parsed_params = _parse_key_value_parameters(parameters_part)

    logger.info(f"Parsed utterance: Original='{utterance_string}', Extracted WebhookID='{webhook_id_for_lookup}', Parameters={parsed_params}")
    return webhook_id_for_lookup, parsed_params

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "You can say a webhook command to trigger it, like 'trigger open main gates' or 'trigger lights with color red'. What would you like to do?"
 
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )
        
class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speak_output = "Goodbye!"
        return handler_input.response_builder.speak(speak_output).response
        

class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for Fallback Intent."""
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "Sorry, I didn't understand that. Please tell me a webhook command, for example, 'trigger open main gates' or 'run fan speed medium'."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )
        
class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # Optional: log the reason
        print(f"Session ended: {handler_input.request_envelope.request.reason}")
        return handler_input.response_builder.response
        
class IntentReflectorHandler(AbstractRequestHandler):
    """Debugging tool to reflect intent name back to user."""
    def can_handle(self, handler_input):
        return is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        intent_name = handler_input.request_envelope.request.intent.name
        speak_output = f"You just triggered the intent named {intent_name}."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )
        
class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handler to catch all exceptions."""
    def can_handle(self, handler_input, exception):
        return True  # Catch everything

    def handle(self, handler_input, exception):
        logger.error(f"Exception caught: {exception}", exc_info=True)
        speak_output = "Sorry, I had trouble doing what you asked. Please try again."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Please try again.")
                .response
        )

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome to Home Assistant Webhook. What webhook ID would you like to trigger?"
        reprompt_output = "What webhook ID would you like to trigger?"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_output)
                .response
        )

class WebhookIntentHandler(AbstractRequestHandler):
    """Handler for WebhookIntent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("WebhookIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        slots = handler_input.request_envelope.request.intent.slots
        webhook_id_raw_full_utterance = slots["webhookId"].value # Raw value from Alexa

        if not webhook_id_raw_full_utterance: 
            speak_output = "I didn't catch the webhook command. Please tell me which webhook you want to trigger." 
            reprompt_output = "What webhook command would you like to trigger?" 
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(reprompt_output)
                    .response
            )

        # Parse webhook_id_raw_full_utterance to get webhook_id_for_lookup and parameters ---
        webhook_id_for_lookup, parsed_parameters = _extract_webhook_id_and_params_from_utterance(webhook_id_raw_full_utterance)
        
        if not webhook_id_for_lookup: # In case parsing fails to extract an ID
             speak_output = "I couldn't understand the webhook ID from your command. Please try again."
             return handler_input.response_builder.speak(speak_output).response

        logger.info(f"Received request for full utterance: '{webhook_id_raw_full_utterance}'") 
        logger.info(f"Extracted Webhook ID for lookup: '{webhook_id_for_lookup}', Parsed Parameters: {parsed_parameters}") 
        logger.info(f"Using config URL: {WEBHOOK_CONFIG_URL}, Trigger Base URL: {WEBHOOK_TRIGGER_BASE_URL}, SSL Verify: {SSL_VERIFY}")

        try:
            # Fetch the JSON configuration file
            response = requests.get(WEBHOOK_CONFIG_URL, headers=AUTH_HEADERS, timeout=10, verify=SSL_VERIFY)
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

            # Parse the JSON response
            config_data = response.json()

            target_webhook = None
            for item in config_data:
                # Assuming 'name' field is the primary identifier
                if item.get("name", "").lower() == webhook_id_for_lookup: # Use parsed ID for lookup
                    target_webhook = {
                        "name": item.get("name"),
                        "method": item.get("method", "GET").upper(), # Default to GET if not specified
                        "path": item.get("path")
                    }
                    # Basic validation for essential fields
                    if not target_webhook["name"] or not target_webhook["path"]:
                        logger.warning(f"Malformed webhook entry found in config for name '{item.get('name')}': {item}")
                        target_webhook = None # Invalidate this entry
                        continue
                    break

            if not target_webhook:
                speak_output = f"I couldn't find a webhook for '{webhook_id_raw_full_utterance}'. Please check the command and try again." 
                return handler_input.response_builder.speak(speak_output).response

            method = target_webhook["method"]
            path = target_webhook["path"] # This is the path relative to WEBHOOK_TRIGGER_BASE_URL

            # Construct the full URL to call on the OpenResty proxy
            full_webhook_url = f"{WEBHOOK_TRIGGER_BASE_URL}{path}"

            logger.info(f"Found webhook config: Name={target_webhook['name']}, Method={method}, Path={path}, Full URL={full_webhook_url}")

            # Execute the HTTP request to the OpenResty proxy
            http_response = None
            # Conditional Method and JSON Body for Parameters ---
            if parsed_parameters: # If parameters are extracted, always use POST with JSON body
                logger.info(f"Parameters detected, sending POST request with JSON body: {parsed_parameters}")
                http_response = requests.post(full_webhook_url, json=parsed_parameters, headers=AUTH_HEADERS, timeout=10, verify=SSL_VERIFY)
            elif method == "GET":
                http_response = requests.get(full_webhook_url, headers=AUTH_HEADERS, timeout=10, verify=SSL_VERIFY)
            elif method == "POST":
                # If no parameters, but config specifies POST, send empty POST or specific body if needed
                http_response = requests.post(full_webhook_url, headers=AUTH_HEADERS, timeout=10, verify=SSL_VERIFY)
            else:
                speak_output = f"Unsupported HTTP method '{method}' found for webhook ID '{webhook_id_for_lookup}'. Parameters require POST." 
                return handler_input.response_builder.speak(speak_output).response

            # Handle HTTP response from the OpenResty proxy
            if http_response.status_code == 200:
                try:
                    response_json = http_response.json()
                    message_to_speak = response_json.get("message")
                    if message_to_speak:
                        speak_output = message_to_speak
                    else:
                        speak_output = f"Webhook '{webhook_id_for_lookup}' triggered successfully, but no message was provided." 
                        logger.warning(f"200 OK from proxy but no 'message' field in JSON for {webhook_id_for_lookup}.") 
                except json.JSONDecodeError:
                    speak_output = f"Webhook '{webhook_id_for_lookup}' triggered successfully, but the response was not valid JSON." 
                    logger.error(f"Failed to decode JSON from proxy for {webhook_id_for_lookup}. Response: {http_response.text}") 
                except Exception as parse_error:
                    speak_output = f"There was an error processing the success message for '{webhook_id_for_lookup}'." 
                    logger.error(f"Error getting message from JSON: {parse_error}. Response: {http_response.text}")
            else:
                speak_output = f"The request returned status code {http_response.status_code}."

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request error for config URL ({WEBHOOK_CONFIG_URL}) or target URL ({WEBHOOK_TRIGGER_BASE_URL}): {e}")
            speak_output = "There was a problem making the request to your webhook or fetching its configuration. Please check the URLs and try again."
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from webhook config URL: {WEBHOOK_CONFIG_URL}. Response: {response.text}")
            speak_output = "I had trouble reading the webhook configuration. It might be malformed."
        except Exception as e:
            logger.error(f"General error in WebhookIntentHandler: {e}", exc_info=True)
            speak_output = "I had trouble processing your request. Please try again later."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

# The SkillBuilder object is used to register your handlers.
sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(WebhookIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
# sb.add_request_handler(IntentReflectorHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

# The Lambda handler that's invoked by the Alexa service.
lambda_handler = sb.lambda_handler()


