# invoice_service.py

import asyncio
import logging

import httpx

from src.routers.constants import MEGAPLAN_API_URL, MEGAPLAN_HEADER
from src.routers.utils import send_comment


async def create_invoice(parent_deal_id, platezh_bank, child_deal_id):
    url = f"{MEGAPLAN_API_URL}/api/v3/deal/{parent_deal_id}"

    data = {
        "Category1000059CustomFieldBankIzPostupleniya": platezh_bank,
    }

    async with httpx.AsyncClient(timeout=240.0) as client:
        response = await client.post(url, headers=MEGAPLAN_HEADER, json=data)
        await asyncio.sleep(2)

    if response.status_code == 200:
        logging.info("Счет успешно создан!")
        response_data = response.json()
        logging.info(response_data)
        return await get_latest_invoice_id_and_number(response_data)
    else:
        error_content = "[KUBIT — Отчет] Ошибка при создании счёта"
        await send_comment(child_deal_id, error_content)
        response_data = response.json()
        logging.info(response_data)
        response.raise_for_status()


async def get_latest_invoice_id_and_number(response_data):
    # Получаем список всех счетов
    invoices = response_data.get("data", {}).get("invoices", [])

    if not invoices:
        return None, None

    # Находим счет с максимальным ID
    parent_invoice_id = str(max(int(invoice["id"]) for invoice in invoices))
    parent_invoice_number = None
    for invoice in invoices:
        if invoice["id"] == parent_invoice_id:
            parent_invoice_number = invoice["number"]
            break

    return parent_invoice_id, parent_invoice_number


async def edit_invoice(invoice_id, child_deal_positions, status=None):
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
             "offer": {"contentType": position["offer"]["contentType"], "id": position["offer"]["id"]}}
            for position in child_deal_positions
        ],
    }

    if status is not None:
        invoice_data["status"] = status

    async with httpx.AsyncClient(timeout=240.0) as client:
        response = await client.post(url, headers=MEGAPLAN_HEADER, json=invoice_data)
        await asyncio.sleep(2)

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

    async with httpx.AsyncClient(timeout=240.0) as client:
        response = await client.post(url, headers=MEGAPLAN_HEADER, json=data)
        await asyncio.sleep(2)

    if response.status_code == 200:
        logging.info(f"Успешно обновлено поле InvoiceId в сделке {deal_id}")
        response_data = response.json()
        logging.info(response_data)
    else:
        logging.error(f"Ошибка при обновлении поля InvoiceId: {response.status_code}")
        logging.error(f"Ответ: {response.text}")
        response.raise_for_status()

