import asyncio
import functools
import json
import os
import warnings
from contextlib import suppress
from logging.config import dictConfig
from typing import Dict, Any

import aioredis
import asynctest
import trio
import trio_asyncio
from quart import request, websocket, Response
from quart_trio import QuartTrio
from werkzeug.datastructures import MultiDict

from db import Database
from test_smsc import get_send_mock_data
from utils import convert_sms_data
from smsc import request_smsc, SmscApiError

app = QuartTrio(__name__)

SMS_LOGIN: str = os.getenv("SMS_LOGIN")
SMS_PASS: str = os.getenv("SMS_PASS")
REDIS_HOST: str = os.getenv("REDIS_HOST", 'localhost')
REDIS_PORT: str = os.getenv("REDIS_PORT", 6379)
REDIS_PASS: str = os.getenv("REDIS_PASS", "SetPass")
DEBUG: str = os.getenv('DEBUG_SENDER')


@app.before_serving
async def create_db_pool() -> None:
    create_redis_pool = functools.partial(
        aioredis.create_redis_pool,
        password=REDIS_PASS,
        encoding='utf-8',
    )
    redis_uri = f"redis://{REDIS_HOST}:{REDIS_PORT}"
    redis = await trio_asyncio.run_asyncio(create_redis_pool, redis_uri)
    app.db_pool = Database(redis)


@app.after_serving
async def close_db_pool() -> None:
    if app.db_pool:
        app.db_pool.redis.close()
        await trio_asyncio.run_asyncio(app.db_pool.redis.wait_closed)


@app.route('/send/', methods=['POST'])
async def send_sms() -> Dict[str, Any]:
    form: MultiDict = await request.form
    send_sms_mock = get_send_mock_data()
    with asynctest.patch("asks.get", side_effect=send_sms_mock):
        payload = {
            "phones": "911",  # TODO change when disable mock
            "mes": form.get("text", ""),
        }
        try:
            result: Dict[str, Any] = await request_smsc("send", SMS_LOGIN, SMS_PASS, payload)
        except SmscApiError as e:
            return {"errorMessage": str(e)}

    await trio_asyncio.run_asyncio(
        app.db_pool.add_sms_mailing,
        result.get('id'),
        [79778838763],
        form.get("text"),
    )
    app.logger.debug(f'added message: "{form.get("text")}"; smsc response: "{result}"')
    tra = await trio_asyncio.run_asyncio(
        app.db_pool.get_sms_mailings,
        "9332", "18582"
    )
    app.logger.debug(tra)
    return result


@app.route('/')
async def hello() -> Response:
    return await app.send_static_file('index.html')


@app.websocket('/ws')
async def ws() -> None:
    while True:
        sms_ids = await trio_asyncio.run_asyncio(
            app.db_pool.list_sms_mailings
        )
        sms_list = await trio_asyncio.run_asyncio(
            app.db_pool.get_sms_mailings,
            *sms_ids
        )
        converted_sms_list = []
        for sms in sms_list:
            converted_sms = await convert_sms_data(sms)
            app.logger.debug(converted_sms)
            converted_sms_list.append(converted_sms)
        response = {
            "msgType": "SMSMailingStatus",
            "SMSMailings": converted_sms_list
        }
        await websocket.send(json.dumps(response))
        await trio.sleep(1)


async def run_server() -> None:
    async with trio_asyncio.open_loop():
        # because run_asyncio don't work with aioredis
        # https://github.com/python-trio/trio-asyncio/issues/63#issuecomment-569155225
        asyncio._set_running_loop(asyncio.get_event_loop())
        dictConfig({
            'version': 1,
            'loggers': {
                'quart.app': {
                    'level': 'DEBUG' if DEBUG else "ERROR",
                },
            },
        })
        app.static_folder = "frontend"
        main_task = app.run_task()
        await main_task()


if __name__ == '__main__':
    warnings.filterwarnings("ignore", category=trio.TrioDeprecationWarning)
    with suppress(KeyboardInterrupt):
        trio.run(run_server)
