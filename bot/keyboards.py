from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Post Now (auto topic)", callback_data="post_auto")],
        [InlineKeyboardButton("✍️ Post with topic", callback_data="post_manual")],
        [InlineKeyboardButton("📋 Queue", callback_data="show_queue")],
        [InlineKeyboardButton("⏰ Schedule", callback_data="show_schedule")],
        [InlineKeyboardButton("📊 History", callback_data="show_history")],
    ])

def style_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎓 Educational", callback_data="style_educational")],
        [InlineKeyboardButton("🔥 Hot Take", callback_data="style_hot_take")],
        [InlineKeyboardButton("📰 News Breakdown", callback_data="style_news_breakdown")],
        [InlineKeyboardButton("🎲 Random", callback_data="style_random")],
    ])

def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Post it", callback_data="confirm_post"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_post"),
        ],
    ])
