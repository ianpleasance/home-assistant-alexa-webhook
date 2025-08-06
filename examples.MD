
Some examples

A basic webhook that does nothing more than verify that things are working.
Note that because the webhook is being called from outside of localhost, local_only=False must be specified.

```
- alias: "Webhook Alexa test"
  id: webhookalexatest
  mode: single
  trigger:
    - platform: webhook
      webhook_id: alexatest
      local_only: false
      allowed_methods:
      - GET
      - POST
  action:
    - service: notify.mobile_app_ians_phone
      data:
        message: "Basic Alexa test webhook triggered"
```

this wouold be enabled by adding the following to webhooks.csv

```
alexatest,GET,/api/webhook/alexatest,"Alexa Test initiated"
```

and invoked via

```
ask hass webhook to trigger alexatest
```

This example demonstratess how to pass parameters

- alias: "Webhook Alexa test 2"
  id: webhookalexatest2
  mode: single
  trigger:
    - platform: webhook
      webhook_id: alexatest2
      local_only: false
      allowed_methods:
      - POST
  action:
    - service: notify.mobile_app_ians_phone
      data:
        message: "Basic Alexa test 2 webhook triggered - parameters = {{ trigger.json | default({}) | tojson }}"
```

and enabled by adding the following to webhooks.csv

```
parmstest,POST,/api/webhook/alexatest2,"Alexa Test with Parameters initiated"
```

and invoked via

```
ask hass webhook to trigger parmstest and set temperature equals 75
```


