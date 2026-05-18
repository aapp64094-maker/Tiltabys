import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")

class BotStates(StatesGroup):
    menu = State()
    test = State()
    journal = State()

QUESTIONS = [
    {
        "text": "1-сұрақ: Эмоцияны басқару\n\nӘріптесіңіз көпшіліктің алдында сіздің жұмысыңызды негізсіз сынады. Сіздің алғашқы реакцияңыз?",
        "options": [
            ("А) Дәл солай жауап қайтарып, оның қателіктерін айтамын.", 1),
            ("Ә) Сабыр сақтап, мәселені жеке сөйлесуге қалдырамын.", 3),
            ("Б) Үндемеймін, бірақ ішімде реніш сақталады.", 2),
        ],
    },
    {
        "text": "2-сұрақ: Келіссөз жүргізу стилі\n\nОртақ жобада пікірлер соқтығысты. Сіз үшін қайсысы маңыздырақ?",
        "options": [
            ("А) Өз пікірімнің дұрыстығын дәлелдеу.", 1),
            ("Ә) Екі жаққа да тиімді ортақ шешім (компромисс) табу.", 3),
            ("Б) Дауласпау үшін басқалардың пікіріне қосыла салу.", 2),
        ],
    },
    {
        "text": "3-сұрақ: Мәселені шешу жолы\n\nҰжымда кикілжің басталғанын сезсеңіз, не істейсіз?",
        "options": [
            ("А) Оған араласпауға тырысамын.", 2),
            ("Ә) Ашық сөйлесуге шақырып, себебін анықтаймын.", 3),
            ("Б) Басшылыққа барып шағымданамын.", 1),
        ],
    },
    {
        "text": "4-сұрақ: Күйзеліске төзімділік\n\nЖұмыстағы түсініспеушіліктен кейін көңіл-күйіңіз қаншалықты тез қалпына келеді?",
        "options": [
            ("А) Бірнеше күн бойы сол оқиғаны ойлап жүремін.", 1),
            ("Ә) Жұмыс күнінің соңына дейін ұмытып кетемін.", 3),
            ("Б) Келесі мәселе туындағанша мазасызданамын.", 2),
        ],
    },
    {
        "text": "5-сұрақ: Тыңдай білу қабілеті\n\nКонфликт кезінде қарсыласыңыздың уәжін (аргументін) тыңдайсыз ба?",
        "options": [
            ("А) Иә, оның көзқарасын түсінуге тырысамын.", 3),
            ("Ә) Тыңдаймын, бірақ тек өз жауабымды дайындау үшін.", 2),
            ("Б) Жоқ, менікі ғана дұрыс деп есептеймін.", 1),
        ],
    },
]

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Тест тапсыру", callback_data="start_test")],
        [InlineKeyboardButton(text="🧘 Стресті төмендету", callback_data="stress")],
        [InlineKeyboardButton(text="📞 Психологиялық қолдау", callback_data="support")],
    ])

def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Басты мәзір", callback_data="back_menu")],
    ])

def question_kb(q_idx):
    q = QUESTIONS[q_idx]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=opt[0], callback_data=f"ans_{i}")]
        for i, opt in enumerate(q["options"])
    ])

def result_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧘 Стресс жаттығулары", callback_data="stress")],
        [InlineKeyboardButton(text="📞 Қолдау алу", callback_data="support")],
        [InlineKeyboardButton(text="🔄 Қайта тапсыру", callback_data="start_test")],
        [InlineKeyboardButton(text="🔙 Басты мәзір", callback_data="back_menu")],
    ])

def get_result_text(score):
    bar_filled = round(score / 15 * 10)
    bar = "🟦" * bar_filled + "⬜" * (10 - bar_filled)
    if score <= 8:
        level = "🔴 Конфликтке бейімділік жоғары"
        advice = "Эмоцияны басқаруды үйрену қажет. Реакцияларыңызды бақылап, сабырлы болуға тырысыңыз.\n\n💡 Ұсыныс: «Стресті төмендету» бөлімін қараңыз."
    elif score <= 12:
        level = "🟡 Орташа деңгей"
        advice = "Көбіне бейтараптықты таңдайсыз — бұл жақсы. Бірақ мәселені іште сақтамай, ашық сөйлесуге дағдыланыңыз.\n\n💡 Ұсыныс: «Экспрессивті жазу» әдісін қолданып көріңіз."
    else:
        level = "🟢 Конструктивті деңгей"
        advice = "Керемет! Сіз кикілжіңді шебер шеше аласыз. Осы қасиетіңізді дамытуды жалғастырыңыз!\n\n💡 Ұсыныс: Ұжымдастарыңызға да осы дағдыны үйретіңіз."
    return f"📊 Тест нәтижесі\n\nҰпайыңыз: {score} / 15\n{bar}\n\n{level}\n\n{advice}"

async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(BotStates.menu)
    await message.answer(
        "Сәлеметсіз бе! 👋\n\n"
        "Сіз «Тілтабыс» ботына кірдіңіз.\n"
        "Бұл бот ұйымдағы қақтығыстардың алдын алуға арналған.\n\n"
        "Мұнда сіз:\n"
        "• конфликт деңгейін анықтай аласыз\n"
        "• психологиялық кеңес ала аласыз\n"
        "• тиімді коммуникация әдістерімен таныса аласыз",
        reply_markup=main_menu_kb(),
    )

async def cmd_menu(message: Message, state: FSMContext):
    await state.set_state(BotStates.menu)
    await message.answer("Басты мәзір 👇", reply_markup=main_menu_kb())

async def cb_back_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.menu)
    await callback.message.answer("Басты мәзір 👇", reply_markup=main_menu_kb())
    await callback.answer()

async def cb_start_test(callback: CallbackQuery, state: FSMContext):
    await state.update_data(score=0, q_idx=0)
    await state.set_state(BotStates.test)
    q = QUESTIONS[0]
    await callback.message.answer(
        f"🔵⚪⚪⚪⚪ (1/5)\n\n{q['text']}",
        reply_markup=question_kb(0),
    )
    await callback.answer()

async def cb_answer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    q_idx = data.get("q_idx", 0)
    opt_idx = int(callback.data.split("_")[1])
    pts = QUESTIONS[q_idx]["options"][opt_idx][1]
    chosen = QUESTIONS[q_idx]["options"][opt_idx][0]
    new_score = data.get("score", 0) + pts
    new_idx = q_idx + 1
    await callback.message.answer(f"✅ {chosen}")
    await callback.answer()
    if new_idx < len(QUESTIONS):
        await state.update_data(score=new_score, q_idx=new_idx)
        dots = "🔵" * (new_idx + 1) + "⚪" * (5 - new_idx - 1)
        q = QUESTIONS[new_idx]
        await callback.message.answer(
            f"{dots} ({new_idx+1}/5)\n\n{q['text']}",
            reply_markup=question_kb(new_idx),
        )
    else:
        await state.set_state(BotStates.menu)
        await state.update_data(score=0, q_idx=0)
        await callback.message.answer(get_result_text(new_score), reply_markup=result_kb())

async def cb_stress(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.menu)
    await callback.message.answer(
        "🧘 Стресті төмендету әдістері\n\n"
        "Эмоцияны іште сақтау — «жарылғалы тұрған бомбаны» ұстап тұрумен тең.\n\n"
        "━━━━━━━━━━━━━━━\n"
        "🫧 «Көпіршік» әдісі\n"
        "Ашу немесе мазасыздық буып тұрса, денеңізді 1 минут бойы қатты сілкіңіз. "
        "Қолды, аяқты, иықты бос тастап, дірілдетіңіз.\n"
        "Дене «қауіп өтті» деген сигнал алып, кортизол деңгейін төмендетеді.\n\n"
        "━━━━━━━━━━━━━━━\n"
        "✍️ «Экспрессивті жазу» әдісі\n"
        "5-10 минут бойы тоқтамай, ойыңызға не келеді, соны жазыңыз.\n"
        "Жазу эмоцияны логикалық тілге айналдырады.\n\n"
        "━━━━━━━━━━━━━━━\n"
        "💪 «Сублимация» әдісі\n"
        "Эмоцияны физикалық күшке айналдырыңыз: үй жинау, тез жүру, қағазды жырту.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Ойымды жазғым келеді", callback_data="journal")],
            [InlineKeyboardButton(text="🔙 Басты мәзір", callback_data="back_menu")],
        ]),
    )
    await callback.answer()

async def cb_journal(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.journal)
    await callback.message.answer(
        "📝 Мәтіндік терапия\n\n"
        "Ойыңызды еркін жазыңыз. Бот сақтамайды.\n\n"
        "Тоқтату үшін /menu деп жазыңыз."
    )
    await callback.answer()

async def journal_msg(message: Message, state: FSMContext):
    await state.set_state(BotStates.menu)
    await message.answer(
        "🌿 Рахмет, бөліскеніңіз үшін.\n\n"
        "Ойыңызды жазу — жақсы қадам. Жазбаңыз сақталмады.\n\n"
        "Эмоцияны сыртқа шығарудың бұл тәсілі миды тынышталтады.",
        reply_markup=back_kb(),
    )

async def cb_support(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.menu)
    await callback.message.answer(
        "📞 Психологиялық қолдау\n\n"
        "Егер сіз өзіңізді тығырыққа тірелгендей сезінсеңіз:\n\n"
        "🆘 150 — тегін психологиялық көмек\n"
        "Кез келген уақытта, тәулік бойы.\n"
        "Қоңырау тегін және құпия сақталады.\n\n"
        "━━━━━━━━━━━━━━━\n"
        "🏥 Психикалық денсаулық орталықтары (ПДО)\n\n"
        "• невроз және мазасыздықпен жұмыс істейді\n"
        "• күйзеліске көмектеседі\n"
        "• анонимді кабинеттер бар",
        reply_markup=back_kb(),
    )
    await callback.answer()

async def fallback_msg(message: Message, state: FSMContext):
    await message.answer("Мәзірге оралу үшін /menu деп жазыңыз.", reply_markup=main_menu_kb())

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_menu, Command("menu"))
    dp.callback_query.register(cb_start_test, F.data == "start_test")
    dp.callback_query.register(cb_back_menu, F.data == "back_menu")
    dp.callback_query.register(cb_stress, F.data == "stress")
    dp.callback_query.register(cb_journal, F.data == "journal")
    dp.callback_query.register(cb_support, F.data == "support")
    dp.callback_query.register(cb_answer, F.data.startswith("ans_"), BotStates.test)
    dp.message.register(journal_msg, BotStates.journal)
    dp.message.register(fallback_msg)
    logger.info("Тілтабыс боты іске қосылды!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
