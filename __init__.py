# Copyright 2017 Oursky Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import requests
import skygear
import stripe
from datetime import datetime
from . import settings

stripe.api_key = settings.stripe_settings["api_key"]

# Function responsible for charging thge customer through Stripe
# Invoked from HTML frontend via index.js
@skygear.op('submitPayment', user_required=False)
def submitPayment(stripeToken, charge, product):
    if stripeToken and charge:
        # If all necessary arguments are supplied, charge card
        try:
            charge = int(charge * 100.0) #Must convert from dollars to cents
            description = f"Charging {charge} USD for {product}"
            stripe.Charge.create(amount=charge, currency="usd",
                                description=description,
                                source="tok_visa", # obtained with Stripe.js
                                )

            dateNow = datetime.now()
            return {
              "success": True, "charge_amount": charge, "product": product,
              "year": dateNow.year,
              "month": dateNow.month,
              "day": dateNow.day
            }

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            return parseError(e)

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            return parseError(e)

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            return parseError(e)

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            return parseError(e)

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            return parseError(e)

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email

            return parseError(e)
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            return parseError(e)

    else: # Something is wrong with the arguments supplied
        return {
            "success": False,
            "error_msg": "Cloud::submitPayment(): Missing token or charge amount!"
        }

def parseError(errorObj):
    ''' For now, return all possible error content '''

    body = errorObj.json_body
    err  = body.get('error', {})
    error_msg = {
        "success": False,
        "stripe_http_status": err.http_status,
        "stripe_error_type": err.get('type'),
        "stripe_error_charge": err.get('charge'),
        "stripe_error_code": err.get('code'),
        "stripe_error_decline_code": err.get('decline_code'),
        "stripe_error_doc_url": err.get('doc_url'),
        "stripe_error_message": err.get('message'),
        "stripe_error_param": err.et('param')
    }
    return error_msg
