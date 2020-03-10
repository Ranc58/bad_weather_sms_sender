from typing import Dict, Any

import asks

from asks.response_objects import Response

SMSC_RESPONSE_FORMAT: str = "3"  # JSON response format


class SmscApiError(Exception):
    pass


async def request_smsc(
        method: str,
        login: str,
        password: str,
        payload: Dict[str, str]
) -> Dict[str, Any]:
    request_params = {
        "login": login,
        "psw": password,
        "fmt": SMSC_RESPONSE_FORMAT,
        "charset": 'utf-8',
        **payload,
    }
    if method.lower() == "send":
        response: Response = await send_sms(request_params)
    elif method.lower() == "status":
        response: Response = await check_sms_status(request_params)
    else:
        raise SmscApiError(f"'{method}' not available method. Use 'send' or 'status' instead")
    response.raise_for_status()
    response_data = response.json()
    error_msg = response_data.get('error')
    if error_msg:
        raise SmscApiError(error_msg)
    return response.json()


async def send_sms(payload: Dict[str, str]) -> Response:
    if not payload.get('phones') or not payload.get('mes'):
        raise SmscApiError("'phones' and 'mes' are required params")
    url = f"https://smsc.ru/sys/send.php?"
    response = await asks.get(url, params=payload)
    return response


async def check_sms_status(payload: Dict[str, str]) -> Response:
    if not payload.get('phone') or not payload.get("id"):
        raise SmscApiError("'phone' and 'id' are required params")
    url = "https://smsc.ru/sys/status.php"
    response = await asks.get(url, params=payload)
    return response
