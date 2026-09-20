import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = "8958961901:AAHfFSRW1idiM_E5qj_bxIMhbvFXBzP7q1g"

# سنضع رقم المسؤول هنا لاحقًا
ADMIN_ID = 222373783

TYPE, NAME, DATE, DAYS, OUT_TIME, IN_TIME, REASON = range(7)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📝 طلب إجازة"],
        ["⏱️ طلب زمنية"],
    ]

    await update.message.reply_text(
        "مرحبًا بك في نظام طلبات الإجازات والزمنيات.\n\n"
        "يرجى اختيار نوع الطلب:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        ),
    )

    return TYPE


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Telegram ID الخاص بك هو:\n{update.effective_user.id}"
    )


async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📝 طلب إجازة":
        context.user_data.clear()
        context.user_data["type"] = "إجازة"

        await update.message.reply_text("أدخل اسمك:")
        return NAME

    if text == "⏱️ طلب زمنية":
        context.user_data.clear()
        context.user_data["type"] = "زمنية"

        await update.message.reply_text("أدخل اسمك:")
        return NAME

    return TYPE


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text

    await update.message.reply_text(
        "أدخل التاريخ:\nمثال: 20/09/2026"
    )

    return DATE


async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["date"] = update.message.text

    if context.user_data["type"] == "إجازة":
        await update.message.reply_text(
            "كم يومًا؟\nمثال: 1"
        )
        return DAYS

    await update.message.reply_text(
        "أدخل وقت الخروج:\nمثال: 10:30"
    )

    return OUT_TIME


async def get_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["days"] = update.message.text

    await update.message.reply_text(
        "ما سبب الإجازة؟"
    )

    return REASON


async def get_out_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["out_time"] = update.message.text

    await update.message.reply_text(
        "أدخل وقت العودة المتوقع:\nمثال: 12:30"
    )

    return IN_TIME


async def get_in_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["in_time"] = update.message.text

    await update.message.reply_text(
        "ما سبب الزمنية؟"
    )

    return REASON


async def get_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reason"] = update.message.text

    request_type = context.user_data["type"]
    name = context.user_data["name"]
    date = context.user_data["date"]
    reason = context.user_data["reason"]

    if request_type == "إجازة":
        days = context.user_data["days"]

        message = (
            "📋 طلب إجازة جديد\n\n"
            f"👤 الموظف: {name}\n"
            f"📅 التاريخ: {date}\n"
            f"📆 المدة: {days} يوم\n"
            f"📝 السبب: {reason}"
        )

    else:
        out_time = context.user_data["out_time"]
        in_time = context.user_data["in_time"]

        message = (
            "📋 طلب زمنية جديد\n\n"
            f"👤 الموظف: {name}\n"
            f"📅 التاريخ: {date}\n"
            f"🚪 وقت الخروج: {out_time}\n"
            f"🔙 وقت العودة: {in_time}\n"
            f"📝 السبب: {reason}"
        )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ موافقة",
                callback_data="approve"
            ),
            InlineKeyboardButton(
                "❌ رفض",
                callback_data="reject"
            ),
        ]
    ])

    if ADMIN_ID != 0:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=message,
            reply_markup=keyboard
        )

        await update.message.reply_text(
            "✅ تم إرسال طلبك إلى المسؤول.\n"
            "سيتم إشعارك بالنتيجة."
        )

    else:
        await update.message.reply_text(
            "✅ تم تسجيل الطلب.\n\n"
            "لم يتم تحديد حساب المسؤول بعد."
        )

    context.user_data.clear()

    return ConversationHandler.END


async def decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.answer(
            "ليس لديك صلاحية اتخاذ القرار.",
            show_alert=True
        )
        return

    if query.data == "approve":
        result = "✅ تمت الموافقة على الطلب."
    else:
        result = "❌ تم رفض الطلب."

    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(result)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "تم إلغاء الطلب."
    )

    return ConversationHandler.END


def main():
    application = Application.builder().token(TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^(📝 طلب إجازة|⏱️ طلب زمنية)$"),
                choose_type
            )
        ],

        states={
            TYPE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    choose_type
                )
            ],

            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_name
                )
            ],

            DATE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_date
                )
            ],

            DAYS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_days
                )
            ],

            OUT_TIME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_out_time
                )
            ],

            IN_TIME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_in_time
                )
            ],

            REASON: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_reason
                )
            ],
        },

        fallbacks=[
            CommandHandler("cancel", cancel)
        ],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CallbackQueryHandler(decision))
    application.add_handler(conversation)

print("البوت يعمل الآن...")
threading.Thread(target=run_web_server, daemon=True).start()

  application.run_polling()

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

if __name__ == "__main__":
    main()
