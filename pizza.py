import time
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def close(session_attributes, fulfillment_state, message):
    """
    Informs Amazon Lex not to expect a response from the user. 
    """
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response

def delegate(session_attributes, slots):
    """
    Directs Amazon Lex to choose the next course of action based on the bot configuration.
    """
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Informs Amazon Lex that the user is expected to provide a slot value in the response.
    """
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }

def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def validate_pizza_order(pizza_kind, crust, size):

    pizza_kinds = ["cheese", "veg", "pepperoni"]
    if pizza_kind is not None and pizza_kind.lower() not in pizza_kinds:
        return build_validation_result(is_valid=False, violated_slot="pizzaKind", message_content="Pizza available are {}. No other options!".format(" / ".join(pizza_kinds)))

    crust_kinds = ["thin", "deep", "thick"]
    if crust is not None and crust.lower() not in crust_kinds:
        return build_validation_result(is_valid=False, violated_slot="crust", message_content="Crusts available are {}. No other options!".format(" / ".join(crust_kinds)))

    size_kinds = ["personal", "large"]
    if size is not None and size.lower() not in size_kinds:
        return build_validation_result(is_valid=False, violated_slot="size", message_content="Sizes available are {}. No other options!".format(" / ".join(size_kinds)))

    return build_validation_result(is_valid=True, violated_slot=None, message_content=None)


def order_pizza(intent_request):
    sessionAttributes = intent_request['sessionAttributes']
    intent_name = intent_request['currentIntent']['name']
    slots = intent_request['currentIntent']['slots']
    crust = slots['crust']
    size = slots['size']
    pizza_kind = slots['pizzaKind']
    source = intent_request['invocationSource']
    
    if source == "DialogCodeHook":
        validation_result = validate_pizza_order(pizza_kind=pizza_kind, crust=crust, size=size)
        if not validation_result["isValid"]:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(session_attributes=intent_request['sessionAttributes'],
                               intent_name=intent_name,
                               slots=slots,
                               slot_to_elicit=validation_result['violatedSlot'],
                               message=validation_result['message'])
        
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        if pizza_kind is not None:
            output_session_attributes['Price'] = len(pizza_kind) * 5  # Elegant pricing model
        
        return delegate(session_attributes=output_session_attributes, slots=slots)
    
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Okay, I have ordered your {} size {} pizza on {} crust.'.format(size, pizza_kind, crust)})


""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'OrderPizza':
        return order_pizza(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')   


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
