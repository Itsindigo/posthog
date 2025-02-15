from posthog.cdp.templates.hog_function_template import HogFunctionTemplate

# Based off of https://customer.io/docs/api/track/#operation/entity

template: HogFunctionTemplate = HogFunctionTemplate(
    status="beta",
    id="template-customerio",
    name="Send events to Customer.io",
    description="Identify or track events against customers in Customer.io",
    icon_url="/static/services/customerio.png",
    hog="""
let action := inputs.action
let name := event.name

let hasIdentifier := false

for (let key, value in inputs.identifiers) {
    if (not empty(value)) {
        hasIdentifier := true
    }
}

if (not hasIdentifier) {
    print('No identifier set. Skipping as at least 1 identifier is needed.')
    return
}

if (action == 'automatic') {
    if (event.name in ('$identify', '$set')) {
        action := 'identify'
        name := null
    } else if (event.name == '$pageview') {
        action := 'page'
        name := event.properties.$current_url
    } else if (event.name == '$screen') {
        action := 'screen'
        name := event.properties.$screen_name
    } else {
        action := 'event'
    }
}

let attributes := inputs.include_all_properties ? action == 'identify' ? person.properties : event.properties : {}
let timestamp := toInt(toUnixTimestamp(toDateTime(event.timestamp)))

for (let key, value in inputs.attributes) {
    attributes[key] := value
}

let res := fetch(f'https://{inputs.host}/api/v2/entity', {
    'method': 'POST',
    'headers': {
        'User-Agent': 'PostHog Customer.io App',
        'Authorization': f'Basic {base64Encode(f'{inputs.site_id}:{inputs.token}')}',
        'Content-Type': 'application/json'
    },
    'body': {
        'type': 'person',
        'action': action,
        'name': name,
        'identifiers': inputs.identifiers,
        'attributes': attributes,
        'timestamp': timestamp
    }
})

if (res.status >= 400) {
    print('Error from customer.io api:', res.status, res.body)
}

""".strip(),
    inputs_schema=[
        {
            "key": "site_id",
            "type": "string",
            "label": "Customer.io site ID",
            "secret": False,
            "required": True,
        },
        {
            "key": "token",
            "type": "string",
            "label": "Customer.io API Key",
            "description": "You can find your API key in your Customer.io account settings (https://fly.customer.io/settings/api_credentials)",
            "secret": True,
            "required": True,
        },
        {
            "key": "host",
            "type": "choice",
            "choices": [
                {
                    "label": "US (track.customer.io)",
                    "value": "track.customer.io",
                },
                {
                    "label": "EU (track-eu.customer.io)",
                    "value": "track-eu.customer.io",
                },
            ],
            "label": "Customer.io region",
            "description": "Use the EU variant if your Customer.io account is based in the EU region",
            "default": "track.customer.io",
            "secret": False,
            "required": True,
        },
        {
            "key": "identifiers",
            "type": "dictionary",
            "label": "Identifiers",
            "description": "You can choose to fill this from an `email` property or an `id` property. If the value is empty nothing will be sent. See here for more information: https://customer.io/docs/api/track/#operation/entity",
            "default": {
                "email": "{person.properties.email}",
            },
            "secret": False,
            "required": True,
        },
        {
            "key": "action",
            "type": "choice",
            "label": "Action",
            "description": "Choose the action to be tracked. Automatic will convert $identify, $pageview and $screen to identify, page and screen automatically - otherwise defaulting to event",
            "default": "automatic",
            "choices": [
                {
                    "label": "Automatic",
                    "value": "automatic",
                },
                {
                    "label": "Identify",
                    "value": "identify",
                },
                {
                    "label": "Event",
                    "value": "event",
                },
                {
                    "label": "Page",
                    "value": "page",
                },
                {
                    "label": "Screen",
                    "value": "screen",
                },
                {
                    "label": "Delete",
                    "value": "delete",
                },
            ],
            "secret": False,
            "required": True,
        },
        {
            "key": "include_all_properties",
            "type": "boolean",
            "label": "Include all properties as attributes",
            "description": "If set, all event properties will be included as attributes. Individual attributes can be overridden below. For identify events the Person properties will be used.",
            "default": False,
            "secret": False,
            "required": True,
        },
        {
            "key": "attributes",
            "type": "dictionary",
            "label": "Attribute mapping",
            "description": "Map of Customer.io attributes and their values. You can use the filters section to filter out unwanted events.",
            "default": {
                "email": "{person.properties.email}",
                "lastname": "{person.properties.lastname}",
                "firstname": "{person.properties.firstname}",
            },
            "secret": False,
            "required": False,
        },
    ],
    filters={
        "events": [
            {"id": "$identify", "name": "$identify", "type": "events", "order": 0},
            {"id": "$pageview", "name": "$pageview", "type": "events", "order": 0},
        ],
        "actions": [],
        "filter_test_accounts": True,
    },
)
