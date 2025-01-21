# invoice_service.py

import asyncio
import logging

import httpx

from src.routers.constants import MEGAPLAN_API_URL, MEGAPLAN_HEADER
from src.routers.utils import get_trigger_id


async def create_invoice(parent_deal_id, platezh_bank, parent_program):
    url = f"{MEGAPLAN_API_URL}/api/v3/deal/{parent_deal_id}/applyTrigger"

    # Получаем ID триггера на основе входных данных
    trigger_id = await get_trigger_id(platezh_bank, parent_program)
    if not trigger_id:
        raise ValueError("Не найден подходящий триггер для указанных параметров")

    # Данные для активации триггера
    data = {
        "contentType": "ProgramTrigger",
        "id": trigger_id,
        "operations": [
            {
                "contentType": "CreateInvoice",
                "invoice": {"contentType": "Invoice"}
            }
        ]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=MEGAPLAN_HEADER, json=data)
        await asyncio.sleep(1)

    if response.status_code == 200:
        logging.info("Счет успешно создан!")
        response_data = response.json()
        logging.info(response_data)
        return await get_latest_invoice_id(response_data)
    else:
        response_data = response.json()
        logging.info(response_data)
        response.raise_for_status()


async def get_latest_invoice_id(response_data):
    # Получаем список всех счетов
    invoices = response_data.get("data", {}).get("invoices", [])

    if not invoices:
        return None

    # Находим счет с максимальным ID
    parent_invoice_id = max(int(invoice["id"]) for invoice in invoices)

    return str(parent_invoice_id)


async def edit_invoice(invoice_id, child_deal_positions):
    url = f"{MEGAPLAN_API_URL}/api/v3/invoice/{invoice_id}"

    # Готовим данные для создания копии счета
    invoice_data = {
        "rows": [
            {"contentType": position["contentType"],
             "discount": position["discount"],
             "name": position["name"],
             "price": position["price"],
             "sum": position["sum"],
             "tax": {"contentType": position["tax"]["contentType"], "id": position["tax"]["id"]},
             "quantity": position["quantity"],
             "unit": {"contentType": position["unit"]["contentType"], "id": position["unit"]["id"]},
             "description": position["description"],
             "offer": {"contentType": position["offer"]["contentType"], "id": position["offer"]["id"]}}
            for position in child_deal_positions
        ],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=MEGAPLAN_HEADER, json=invoice_data)
        await asyncio.sleep(1)

    if response.status_code == 200:
        logging.info("Счет успешно отредактирован!")
        response_data = response.json()
        logging.info(response_data)
    else:
        response.raise_for_status()


async def update_child_deal_custom_field(deal_id: str, invoice_id: str):
    url = f"{MEGAPLAN_API_URL}/api/v3/deal/{deal_id}"

    data = {
        "contentType": "Deal",
        "Category1000057CustomFieldInvoiceId": invoice_id
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=MEGAPLAN_HEADER, json=data)
        await asyncio.sleep(1)

    if response.status_code == 200:
        logging.info(f"Успешно обновлено поле InvoiceId в сделке {deal_id}")
        response_data = response.json()
        logging.info(response_data)
    else:
        logging.error(f"Ошибка при обновлении поля InvoiceId: {response.status_code}")
        logging.error(f"Ответ: {response.text}")
        response.raise_for_status()

