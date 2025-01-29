import asyncio
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.requests import Request

from src.routers.invoice_service import create_invoice, edit_invoice, update_child_deal_custom_field
from src.routers.utils import get_status_sequence, get_invoice_status, update_invoice_status, get_invoice, \
    get_deal_positions, get_deal_data, send_comment, get_custom_field

router = APIRouter()


@router.get("/test")
async def test_endpoint():
    logging.info(f"Test handler works!")
    return JSONResponse(status_code=200, content={"message": "Test request successful!"})


@router.post("/new")
async def handle_invoice_webhook(request: Request):
    invoice_webhook_data = await request.json()
    logging.info(f"Received invoice_webhook_data: {invoice_webhook_data}")

    # Создаем асинхронную задачу для обработки выгрузки
    asyncio.create_task(process_copying_invoice(invoice_webhook_data))
    return JSONResponse(status_code=200, content={"message": "Задача копирования счёта принята в обработку"})


@router.post("/paid")
async def handle_paid_webhook(request: Request):
    webhook_data = await request.json()
    logging.info(f"Received paid_webhook_data: {webhook_data}")

    asyncio.create_task(process_update_status(webhook_data, "paid"))
    return JSONResponse(status_code=200,
                        content={"message": "Задача обновления статуса счета на 'Оплачено' принята в обработку"})


@router.post("/cancel")
async def handle_cancel_webhook(request: Request):
    webhook_data = await request.json()
    logging.info(f"Received cancel_webhook_data: {webhook_data}")

    asyncio.create_task(process_update_status(webhook_data, "rejected"))
    return JSONResponse(status_code=200,
                        content={"message": "Задача обновления статуса счета на 'Отказ' принята в обработку"})


@router.post("/update")
async def handle_update_webhook(request: Request):
    webhook_data = await request.json()
    logging.info(f"Received update_webhook_data: {webhook_data}")

    asyncio.create_task(process_update_positions(webhook_data))
    return JSONResponse(status_code=200, content={"message": "Задача обновления позиций счета принята в обработку"})


async def process_copying_invoice(invoice_webhook_data):
    child_deal_id = invoice_webhook_data["data"]["deal"]["Id"]
    child_deal_custom_category, platezh_bank = get_custom_field(invoice_webhook_data["data"]["deal"], field_suffix="PlatezhBank")
    child_deal_data = await get_deal_data(child_deal_id)
    child_deal_number = child_deal_data["number"]
    child_deal_positions = await get_deal_positions(child_deal_id)

    parent_deal_id = invoice_webhook_data["data"]["deal"]["RelatedObjects"][0]["Id"]
    parent_deal_data = await get_deal_data(parent_deal_id)
    parent_deal_custom_category, _ = get_custom_field(parent_deal_data, field_suffix="BankIzPostupleniya")

    parent_invoice_id, parent_invoice_number, parent_invoice_status = await create_invoice(parent_deal_id, platezh_bank, child_deal_id, parent_deal_custom_category)
    comment_text = f"[KUBIT] - создан счет №{parent_invoice_number}. на основании поступления №{child_deal_number}"
    if parent_invoice_status != "created":
        comment_text = f"[KUBIT] Попытка создания счета не удалась"
        await send_comment(parent_deal_id, comment_text)
        return
    await send_comment(parent_deal_id, comment_text)
    await update_child_deal_custom_field(child_deal_id, parent_invoice_id, child_deal_custom_category)
    await edit_invoice(parent_invoice_id, child_deal_positions, status="drawn")


async def process_update_status(webhook_data, target_status):
    _, invoice_id = get_custom_field(webhook_data["data"]["deal"], field_suffix="InvoiceId")

    current_status = await get_invoice_status(invoice_id)
    logging.info(f"Текущий статус счета {invoice_id}: {current_status}")

    status_sequence = get_status_sequence(current_status, target_status)

    for status in status_sequence:
        await update_invoice_status(invoice_id, status)
        logging.info(f"Статус счета {invoice_id} обновлен на '{status}'")


async def process_update_positions(webhook_data):
    _, invoice_id = get_custom_field(webhook_data["data"]["deal"], field_suffix="InvoiceId")
    child_deal_id = webhook_data["data"]["deal"]["Id"]

    invoice_data = await get_invoice(invoice_id)
    current_status = invoice_data.get("status")
    logging.info(f"Текущий статус счета {invoice_id}: {current_status}")

    if current_status != "created":
        status_sequence = get_status_sequence(current_status, "created")

        for status in status_sequence:
            await update_invoice_status(invoice_id, status)
            logging.info(f"Статус счета {invoice_id} обновлен на '{status}'")

    child_deal_positions = await get_deal_positions(child_deal_id)

    await edit_invoice(invoice_id, child_deal_positions)

    status_sequence = get_status_sequence("created", current_status)

    for status in status_sequence:
        await update_invoice_status(invoice_id, status)
        logging.info(f"Статус счета {invoice_id} обновлен на '{status}'")
    logging.info(f"Позиции счета {invoice_id} успешно обновлены")

