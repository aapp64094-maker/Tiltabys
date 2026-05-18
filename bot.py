import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = ("8893980495:AAGDsANpMZl9RCQbNrSu9GLdS2k5sPzOSkg")

# Conversation states
MENU, TEST, JOURNAL = range(3)

# ─── Тест сұрақтары ───────────────────────────────────────────
QUESTIONS = [
    {
        "text": "1-сұрақ: Эмоцияны басқару\n\n"
                "Әріптесіңіз көпшіліктің алдында сіздің жұмысыңызды негізсіз сынады. "
                "Сіздің алғашқы реакцияңыз?",
        "options": [
            ("А) Дәл солай жауап қайтарып, оның қателіктерін айтамын.", 1),
            ("Ә) Сабыр сақтап, мәселені жеке сөйлесуге қалдырамын.", 3),
            ("Б) Үндемеймін, бірақ ішімде реніш сақталады.", 2),
        ],
    },
    {
        "text": "2-сұрақ: Келіссөз жүргізу стилі\n\n"
                "Ортақ жобада пікірлер соқтығысты. Сіз үшін қайсысы маңыздырақ?",
        "options": [
            ("А) Өз пікірімнің дұрыстығын дәлелдеу.", 1),
            ("Ә) Екі жаққа да тиімді ортақ шешім (компромисс) табу.", 3),
            ("Б) Дауласпау үшін басқалардың пікіріне қосыла салу.", 2),
        ],
    },
    {
        "text": "3-сұрақ: Мәселені шешу жолы\n\n"
                "Ұжымда кикілжің басталғанын сезсеңіз, не істейсіз?",
        "options": [
            ("А) Оған араласпауға тырысамын.", 2),
            ("Ә) Ашық сөйлесуге шақырып, себебін анықтаймын.", 3),
            ("Б) Басшылыққа барып шағымданамын.", 1),
        ],
    },
    {
        "text": "4-сұрақ: Күйзеліске төзімділік\n\n"
                "Жұмыстағы түсініспеушіліктен кейін көңіл-күйіңіз қаншалықты тез қалпына келеді?",
        "options": [
            ("А) Бірнеше күн бойы сол оқиғаны ойлап жүремін.", 1),
            ("Ә) Жұмыс күнінің соңына дейін ұмытып кетемін.", 3),
            ("Б) Келесі мәселе туындағанша мазасызданамын.", 2),
        ],
    },
    {
        "text": "5-сұрақ: Тыңдай білу қабілеті\n\n"
                "Конфликт кезінде қарсыласыңыздың уәжін (аргументін) тыңдайсыз ба?",
        "options": [
            ("А) Иә, оның көзқарасын түсінуге тырысамын.", 3),
            ("Ә) Тыңдаймын, бірақ тек өз жауабымды дайындау үшін.", 2),
            ("Б) Жоқ, менікі ғана дұрыс деп есептеймін.", 1),
        ],
    },
]


# ─── Helpers ──────────────────────────────────────────────────
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Тест тапсыру", callback_data="start_test")],
        [InlineKeyboardButton("🧘 Стресті төмендету", callback_data="stress")],
        [InlineKeyboardButton("📞 Психологиялық қолдау", callback_data="support")],
    ])


def get_result_text(score: int) -> str:
    bar_filled = round(score / 15 * 10)
    bar = "🟦" * bar_filled + "⬜" * (10 - bar_filled)

    if score <= 8:
        level = "🔴 Конфликтке бейімділік жоғары"
        advice = (
            "Эмоцияны басқаруды үйрену қажет.\n"
            "Реакцияларыңызды бақылап, сабырлы болуға тырысыңыз.\n\n"
            "💡 Ұсыныс: «Стресті төмендету» бөлімін қараңыз."
        )
    elif score <= 12:
        level = "🟡 Орташа деңгей"
        advice = (
            "Көбіне бейтараптықты таңдайсыз — бұл жақсы.\n"
            "Бірақ мәселені іште сақтамай, ашық сөйлесуге дағдыланыңыз.\n\n"
            "💡 Ұсыныс: «Экспрессивті жазу» әдісін қолданып көріңіз."
        )
    else:
        level = "🟢 Конструктивті деңгей"
        advice = (
            "Керемет! Сіз кикілжіңді шебер шеше аласыз.\n"
            "Осы қасиетіңізді дамытуды жалғастырыңыз!\n\n"
            "💡 Ұсыныс: Ұжымдастарыңызға да осы дағдыны үйретіңіз."
        )

    return (
        f"📊 *Тест нәтижесі*\n\n"
        f"Ұпайыңыз: *{score} / 15*\n"
        f"{bar}\n\n"
        f"{level}\n\n"
        f"{advice}"
    )


# ─── Handlers ─────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "Сәлеметсіз бе! 👋\n\n"
        "Сіз *«Тілтабыс»* ботына кірдіңіз.\n"
        "Бұл бот ұйымдағы қақтығыстардың алдын алуға арналған.\n\n"
        "Мұнда сіз:\n"
        "• конфликт деңгейін анықтай аласыз\n"
        "• психологиялық кеңес ала аласыз\n"
        "• тиімді коммуникация әдістерімен таныса аласыз",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
    return MENU


async def menu_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "start_test":
        ctx.user_data["score"] = 0
        ctx.user_data["q_idx"] = 0
        await send_question(query, ctx)
        return TEST

    elif data == "stress":
        await query.message.reply_text(
            "🧘 *Стресті төмендету әдістері*\n\n"
            "Эмоцияны іште сақтау — «жарылғалы тұрған бомбаны» ұстап тұрумен тең.\n\n"
            "━━━━━━━━━━━━━━━\n"
            "🫧 *«Көпіршік» әдісі*\n"
            "Ашу немесе мазасыздық буып тұрса, денеңізді 1 минут бойы қатты сілкіңіз. "
            "Қолды, аяқты, иықты бос тастап, дірілдетіңіз.\n"
            "_Дене «қауіп өтті» деген сигнал алып, кортизол деңгейін төмендетеді._\n\n"
            "━━━━━━━━━━━━━━━\n"
            "✍️ *«Экспрессивті жазу» әдісі*\n"
            "5-10 минут бойы тоқтамай, ойыңызға не келеді, соны жазыңыз. "
            "Грамматикаға, мағынаға қарамаңыз.\n"
            "_Жазу эмоцияны логикалық тілге айналдырады — мидың тынышталуына көмектеседі._\n\n"
            "━━━━━━━━━━━━━━━\n"
            "💪 *«Сублимация» әдісі*\n"
            "Эмоцияны физикалық күшке айналдырыңыз: үй жинау, тез жүру, қағазды майдалап жырту.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Ойымды жазғым келеді", callback_data="journal")],
                [InlineKeyboardButton("🔙 Басты мәзір", callback_data="back_menu")],
            ]),
        )
        return MENU

    elif data == "support":
        await query.message.reply_text(
            "📞 *Психологиялық қолдау*\n\n"
            "Егер сіз өзіңізді тығырыққа тірелгендей сезінсеңіз немесе "
            "эмоционалды ауырлықты жалғыз көтере алмасаңыз:\n\n"
            "🆘 *150* — тегін психологиялық көмек\n"
            "Кез келген уақытта, тәулік бойы.\n"
            "Қоңырау тегін және *құпия сақталады.*\n\n"
            "━━━━━━━━━━━━━━━\n"
            "🏥 *Психикалық денсаулық орталықтары (ПДО)*\n\n"
            "Әр қалада мемлекеттік орталықтар жұмыс істейді. Олар:\n"
            "• невроз және мазасыздықпен жұмыс істейді\n"
            "• күйзеліске көмектеседі\n"
            "• анонимді кабинеттер бар",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Басты мәзір", callback_data="back_menu")],
            ]),
        )
        return MENU

    elif data == "journal":
        await query.message.reply_text(
            "📝 *Мәтіндік терапия*\n\n"
            "Ойыңызды еркін жазыңыз. Бот сақтамайды және жоятын болады.\n\n"
            "Тоқтату үшін /menu деп жазыңыз.",
            parse_mode="Markdown",
        )
        return JOURNAL

    elif data == "back_menu":
        await query.message.reply_text(
            "Басты мәзір 👇",
            reply_markup=main_menu_keyboard(),
        )
        return MENU

    elif data == "retry_test":
        ctx.user_data["score"] = 0
        ctx.user_data["q_idx"] = 0
        await send_question(query, ctx)
        return TEST

    return MENU


async def send_question(query, ctx):
    idx = ctx.user_data.get("q_idx", 0)
    q = QUESTIONS[idx]
    total = len(QUESTIONS)
    progress = "🔵" * (idx + 1) + "⚪" * (total - idx - 1)

    keyboard = [
        [InlineKeyboardButton(opt[0], callback_data=f"ans_{i}")]
        for i, opt in enumerate(q["options"])
    ]

    await query.message.reply_text(
        f"{progress} ({idx+1}/{total})\n\n{q['text']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def test_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("ans_"):
        return await menu_callback(update, ctx)

    opt_idx = int(query.data.split("_")[1])
    q_idx = ctx.user_data.get("q_idx", 0)
    pts = QUESTIONS[q_idx]["options"][opt_idx][1]
    ctx.user_data["score"] = ctx.user_data.get("score", 0) + pts
    ctx.user_data["q_idx"] = q_idx + 1

    chosen_label = QUESTIONS[q_idx]["options"][opt_idx][0]
    await query.message.reply_text(f"✅ {chosen_label}")

    if ctx.user_data["q_idx"] < len(QUESTIONS):
        await send_question(query, ctx)
        return TEST
    else:
        score = ctx.user_data["score"]
        result = get_result_text(score)
        await query.message.reply_text(
            result,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🧘 Стресс жаттығулары", callback_data="stress")],
                [InlineKeyboardButton("📞 Қолдау алу", callback_data="support")],
                [InlineKeyboardButton("🔄 Қайта тапсыру", callback_data="retry_test")],
                [InlineKeyboardButton("🔙 Басты мәзір", callback_data="back_menu")],
            ]),
        )
        return MENU


async def journal_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌿 Рахмет, бөліскеніңіз үшін.\n\n"
        "Ойыңызды жазу — жақсы қадам. Жазбаңыз сақталмады.\n\n"
        "_Эмоцияны сыртқа шығарудың бұл тәсілі миды тынышталтады._",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Басты мәзір", callback_data="back_menu")],
        ]),
    )
    return MENU


async def menu_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "Басты мәзір 👇",
        reply_markup=main_menu_keyboard(),
    )
    return MENU


async def fallback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Мәзірге оралу үшін /menu деп жазыңыз.",
        reply_markup=main_menu_keyboard(),
    )
    return MENU


# ─── Main ─────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [
                CallbackQueryHandler(menu_callback),
                CommandHandler("menu", menu_command),
            ],
            TEST: [
                CallbackQueryHandler(test_answer),
            ],
            JOURNAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, journal_handler),
                CommandHandler("menu", menu_command),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("menu", menu_command),
            MessageHandler(filters.ALL, fallback),
        ],
    )

    app.add_handler(conv)
    logger.info("Тілтабыс боты іске қосылды...")
    app.run_polling()


if __name__ == "__main__":
    main()
