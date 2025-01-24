# utils.py

import asyncio
import logging

import httpx

from src.routers.constants import MEGAPLAN_API_URL, MEGAPLAN_HEADER


def get_status_sequence(current_status, target_status):
    # Определяем возможные переходы
    transitions = {
        "created": ["drawn"],
        "drawn": ["paid", "rejected"],
        "paid": ["drawn"],
        "rejected": ["created"]
    }

    sequence = []
    temp_status = current_status

    while temp_status != target_status:
        possible = transitions.get(temp_status, [])
        if not possible:
            return None
        next_status = possible[0]  # Выбираем первый возможный статус
        sequence.append(next_status)
        temp_status = next_status

    return sequence


async def get_invoice_status(invoice_id):
    invoice_data = await get_invoice(invoice_id)
    return invoice_data.get("status")


async def update_invoice_status(invoice_id: str, new_status: str):
    url = f"{MEGAPLAN_API_URL}/api/v3/invoice/{invoice_id}"

    data = {"status": new_status}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=MEGAPLAN_HEADER, json=data)
        await asyncio.sleep(1)

    if response.status_code == 200:
        logging.info(f"Статус счета {invoice_id} успешно обновлен на {new_status}")
    else:
        logging.error(f"Ошибка при обновлении статуса счета {invoice_id}: {response.status_code} - {response.text}")
        response.raise_for_status()


async def get_invoice(invoice_id):
    url = f"{MEGAPLAN_API_URL}/api/v3/invoice/{invoice_id}"
    logging.info(f"url: {url}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=MEGAPLAN_HEADER)
        await asyncio.sleep(1)

    if response.status_code == 200:
        response_data = response.json().get("data")
        logging.info(f"Response invoice Content: {response_data}")
        return response_data
    else:
        response.raise_for_status()


async def get_deal_data(deal_id):
    url = f"{MEGAPLAN_API_URL}/api/v3/deal/{deal_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=MEGAPLAN_HEADER)
        response.raise_for_status()
        await asyncio.sleep(1)

    return response.json()["data"]


async def get_deal_positions(deal_id):
    url = f"{MEGAPLAN_API_URL}/api/v3/deal/{deal_id}/offerRows"
    logging.info(f"Получаем позиции сделки. URL: {url}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=MEGAPLAN_HEADER)
        await asyncio.sleep(1)

    if response.status_code == 200:
        response_data = response.json()
        logging.info(f"Response Content: {response_data}")
        return response_data.get("data")
    else:
        response.raise_for_status()


async def send_comment(deal_id: str, content: str):
    url = f"{MEGAPLAN_API_URL}/deal/{deal_id}/comments"
    body = {
        "contentType": "CommentCreateActionRequest",
        "comment": {
            "contentType": "Comment",
            "content": content,
            "subject": {
                "contentType": "Deal",
                "id": deal_id
            }
        },
        "transports": [
            {}
        ]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=MEGAPLAN_HEADER, json=body)
        result = response.json()
        logging.info(result)
        response.raise_for_status()
        logging.info(f"Комментарий успешно отравлен в сделку: {deal_id}")
        await asyncio.sleep(1)
