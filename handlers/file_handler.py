import logging

logger = logging.getLogger(__name__)

async def file_handler(update, context):
    file = update.message.document or (
        update.message.photo[-1] if update.message.photo else None
    )

    if not file:
        return

    file_id = file.file_id
    file_name = file.file_name if update.message.document else f"photo_{file_id}.jpg"

    try:
        tg_file = await context.bot.get_file(file_id)
        await tg_file.download_to_drive(file_name)
        await update.message.reply_text(f"File received: {file_name}")
    except Exception as e:
        logger.error(f"File Handling Error: {e}")
        await update.message.reply_text("Error processing the file.")
