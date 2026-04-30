import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
from bot.keyboards import main_menu_keyboard, style_keyboard, confirm_keyboard
from pipeline import run_pipeline
from storage.database import Database
from config import Config
from utils import compress_image

logger = logging.getLogger(__name__)

WAITING_TOPIC, WAITING_STYLE = range(2)


def _is_admin(user_id: int) -> bool:
    return user_id == Config.TELEGRAM_ADMIN_ID


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized")
        return
    await update.message.reply_text(
        "🤖 Twitter Thread Bot\nChoose an action:",
        reply_markup=main_menu_keyboard(),
    )


async def cmd_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id):
        return
    await update.message.reply_text("📝 Send me the topic for the thread:")
    return WAITING_TOPIC


async def cmd_post_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not _is_admin(query.from_user.id):
        return ConversationHandler.END
    await query.edit_message_text("📝 Send me the topic for the thread:")
    return WAITING_TOPIC


async def cmd_preview_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not _is_admin(query.from_user.id):
        return ConversationHandler.END
    context.user_data["dry_run"] = True
    await query.edit_message_text("👁 Preview mode — send me the topic (won't post to Twitter):")
    return WAITING_TOPIC


async def receive_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["pending_topic"] = update.message.text
    await update.message.reply_text(
        "Choose thread style:", reply_markup=style_keyboard()
    )
    return WAITING_STYLE


async def receive_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    style_map = {
        "style_educational": "educational",
        "style_hot_take": "hot_take",
        "style_news_breakdown": "news_breakdown",
        "style_random": None,
    }
    style = style_map.get(query.data)
    topic = context.user_data.get("pending_topic", "")

    await query.edit_message_text(
        f"⏳ Generating thread about: *{topic}*...", parse_mode="Markdown"
    )

    db = context.bot_data["db"]
    dry_run = context.user_data.pop("dry_run", False)
    result = await run_pipeline(db, topic=topic, style=style, dry_run=dry_run)

    tweets_preview = "\n\n".join(
        f"*{i+1}.* {t}" for i, t in enumerate(result["tweets"])
    )

    if result["status"] == "dry_run":
        text = (
            f"👁 *Preview (not posted)*\n\n"
            f"Topic: {result['topic']}\n"
            f"Style: {result['style']}\n"
            f"Tweets: {result['num_tweets']}\n\n"
            f"{tweets_preview}"
        )
        image_path = result.get("image_path")
        if image_path:
            import os
            await query.edit_message_text("👁 Preview ready, sending...")
            compressed = compress_image(image_path)
            try:
                with open(compressed, "rb") as img:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=img,
                        caption=f"👁 *Preview* — {result['topic']}",
                        parse_mode="Markdown",
                        read_timeout=60,
                        write_timeout=60,
                        connect_timeout=30,
                    )
            finally:
                os.unlink(image_path)
                os.unlink(compressed)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=text,
                parse_mode="Markdown",
            )
        else:
            await query.edit_message_text(text, parse_mode="Markdown")
    elif result["status"] == "posted":
        await query.edit_message_text(
            f"✅ Thread posted!\n\n"
            f"Topic: {result['topic']}\n"
            f"Style: {result['style']}\n"
            f"Tweets: {result['num_tweets']}\n"
            f"Twitter ID: {result['twitter_id']}\n\n"
            f"{tweets_preview}",
            parse_mode="Markdown",
        )
    else:
        await query.edit_message_text(
            f"❌ Failed: {result.get('error', 'Unknown')}\n\n"
            f"Thread saved as draft #{result['thread_id']}",
        )

    return ConversationHandler.END


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not _is_admin(query.from_user.id):
        return

    if query.data == "preview_auto":
        await query.edit_message_text("⏳ Generating preview (auto topic, no posting)...")
        db = context.bot_data["db"]
        result = await run_pipeline(db, dry_run=True)
        tweets_preview = "\n\n".join(
            f"{i+1}. {t}" for i, t in enumerate(result["tweets"])
        )
        text = (
            f"👁 Preview (not posted)\n\n"
            f"Topic: {result['topic']}\n"
            f"Style: {result['style']}\n\n"
            f"{tweets_preview}"
        )
        image_path = result.get("image_path")
        if image_path:
            import os
            await query.edit_message_text("👁 Preview ready, sending...")
            compressed = compress_image(image_path)
            try:
                with open(compressed, "rb") as img:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=img,
                        caption=f"👁 {result['topic']}",
                        read_timeout=60,
                        write_timeout=60,
                        connect_timeout=30,
                    )
            finally:
                os.unlink(image_path)
                os.unlink(compressed)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=text,
            )
        else:
            await query.edit_message_text(text)

    elif query.data == "post_auto":
        await query.edit_message_text("⏳ Generating thread (auto topic)...")
        db = context.bot_data["db"]
        result = await run_pipeline(db)

        if result["status"] == "posted":
            tweets_preview = "\n\n".join(
                f"{i+1}. {t}" for i, t in enumerate(result["tweets"])
            )
            await query.edit_message_text(
                f"✅ Auto thread posted!\n\n"
                f"Topic: {result['topic']}\n"
                f"Style: {result['style']}\n"
                f"Twitter ID: {result['twitter_id']}\n\n"
                f"{tweets_preview}",
            )
        else:
            await query.edit_message_text(
                f"❌ Failed: {result.get('error', 'Unknown')}",
            )

    elif query.data == "show_queue":
        db = context.bot_data["db"]
        pending = db.get_pending_threads()
        if not pending:
            await query.edit_message_text("📋 Queue is empty.")
        else:
            lines = [
                f"#{t['id']}: {t['topic']} ({t['style']})"
                for t in pending[:10]
            ]
            await query.edit_message_text(
                "📋 Pending threads:\n\n" + "\n".join(lines)
            )

    elif query.data == "show_schedule":
        db = context.bot_data["db"]
        schedules = db.get_schedules()
        if not schedules:
            await query.edit_message_text("⏰ No schedules set.")
        else:
            lines = [f"#{s['id']}: {s['hour']:02d}:{s['minute']:02d} UTC"
                     for s in schedules]
            await query.edit_message_text(
                "⏰ Active schedules:\n\n" + "\n".join(lines)
            )

    elif query.data == "show_history":
        db = context.bot_data["db"]
        topics = db.get_recent_topics(10)
        if not topics:
            await query.edit_message_text("📊 No history yet.")
        else:
            await query.edit_message_text(
                "📊 Recent topics:\n\n" + "\n".join(f"• {t}" for t in topics)
            )


def setup_handlers(app):
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("post", cmd_post),
            CallbackQueryHandler(cmd_post_callback, pattern="^post_manual$"),
            CallbackQueryHandler(cmd_preview_callback, pattern="^preview_manual$"),
        ],
        states={
            WAITING_TOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topic)
            ],
            WAITING_STYLE: [
                CallbackQueryHandler(receive_style, pattern="^style_")
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_start)],
        per_message=False,
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(callback_handler))
