import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ══════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════
TOKEN     = "8536857384:AAHKKlzju9tLZdp4S39trq5vaT6T-aeuLhU"
DATA_FILE = "data/students.json"

# ── Conversation states ──────────────────────
(
    ADD_STUDENT_NAME, ADD_STUDENT_ID,
    ADD_GRADE_ID, ADD_GRADE_SUBJECT, ADD_GRADE_VALUE,
    VIEW_STUDENT_ID,
    DELETE_STUDENT_ID,
    AI_ADVICE_ID,
    COMPARE_ID1, COMPARE_ID2,
) = range(10)


# ══════════════════════════════════════════════
#  DATA HELPERS
# ══════════════════════════════════════════════
def _load() -> list[dict]:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def _save(data: list[dict]) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def _find(data: list[dict], sid: str) -> dict | None:
    for s in data:
        if s["student_id"] == sid:
            return s
    return None

def _average(subjects: dict) -> float:
    total, count = 0, 0
    for grades in subjects.values():
        total += sum(grades)
        count += len(grades)
    return round(total / count, 2) if count else 0.0

def _subj_avg(grades: list) -> float:
    return round(sum(grades) / len(grades), 2) if grades else 0.0

def _weak_subject(subjects: dict) -> str | None:
    if not subjects:
        return None
    return min(subjects, key=lambda s: _subj_avg(subjects[s]))

def _strong_subject(subjects: dict) -> str | None:
    if not subjects:
        return None
    return max(subjects, key=lambda s: _subj_avg(subjects[s]))

def _status_emoji(avg: float) -> str:
    if avg >= 85: return "🟢"
    if avg >= 70: return "🟡"
    if avg >= 50: return "🟠"
    return "🔴"

def _grade_letter(avg: float) -> str:
    if avg >= 90: return "A+"
    if avg >= 85: return "A"
    if avg >= 80: return "A-"
    if avg >= 75: return "B+"
    if avg >= 70: return "B"
    if avg >= 65: return "B-"
    if avg >= 60: return "C+"
    if avg >= 55: return "C"
    if avg >= 50: return "C-"
    return "F"

def _trend(grades: list) -> str:
    """Check if grades are going up, down or stable."""
    if len(grades) < 2:
        return "➡️ stable"
    first_half = sum(grades[:len(grades)//2]) / (len(grades)//2)
    second_half = sum(grades[len(grades)//2:]) / (len(grades) - len(grades)//2)
    diff = second_half - first_half
    if diff >= 5:
        return "📈 improving"
    if diff <= -5:
        return "📉 declining"
    return "➡️ stable"

def _format_student(s: dict) -> str:
    avg    = _average(s["subjects"])
    weak   = _weak_subject(s["subjects"])
    strong = _strong_subject(s["subjects"])
    em     = _status_emoji(avg)
    letter = _grade_letter(avg)
    lines  = [
        f"┌─────────────────────────",
        f"│ 👤 *{s['name']}*",
        f"│ 🆔 `{s['student_id']}`",
        f"│ 📊 Average: *{avg}* ({letter}) {em}",
        f"└─────────────────────────",
    ]
    if s["subjects"]:
        lines.append("\n📚 *Subjects:*")
        for subj, grades in s["subjects"].items():
            sa  = _subj_avg(grades)
            tr  = _trend(grades)
            tag = ""
            if subj == weak:   tag = " 🔴"
            elif subj == strong: tag = " 🟢"
            lines.append(f"  • *{subj}*: {sa} {_grade_letter(sa)}{tag} {tr}")
            lines.append(f"    _{', '.join(map(str, grades))}_")
    else:
        lines.append("_No grades yet._")
    return "\n".join(lines)


# ══════════════════════════════════════════════
#  SMART AI ADVISOR  (pure Python, no API)
# ══════════════════════════════════════════════
# Study tips library per subject category
_STUDY_TIPS = {
    "math":     ["Practice problems daily — even 10 problems/day makes a huge difference 📐",
                 "Focus on understanding formulas, not memorizing them 🧠",
                 "Use Khan Academy or YouTube for step-by-step explanations 🎥"],
    "physics":  ["Draw diagrams for every problem — it helps visualize forces 📌",
                 "Connect theory to real-life examples to remember better 🌍",
                 "Re-derive formulas yourself to understand where they come from ⚙️"],
    "chemistry":["Make flashcards for elements and reactions 🃏",
                 "Do practice reactions daily and check your work 🧪",
                 "Group similar reactions together when studying 📋"],
    "english":  ["Read 15 minutes in English every day 📖",
                 "Write a short paragraph daily — even a diary in English ✍️",
                 "Watch movies/series with English subtitles 🎬"],
    "history":  ["Create timelines on paper — it helps connect events 📅",
                 "Tell the story out loud to yourself like you're teaching someone 🗣️",
                 "Link historical events to causes and effects, not just dates 🔗"],
    "cs":       ["Code every day — even 30 minutes of practice is enough 💻",
                 "Build small projects to apply what you learn 🛠️",
                 "Debug your old code to find and learn from mistakes 🐛"],
    "default":  ["Review your notes within 24 hours of the lecture 📝",
                 "Use the Pomodoro method: 25 min study → 5 min break ⏱️",
                 "Teach the topic to a friend — if you can explain it, you know it 👥"]
}

def _get_subject_tips(subject_name: str) -> list[str]:
    name = subject_name.lower()
    if any(k in name for k in ["math", "calculus", "algebra", "maths"]):
        return _STUDY_TIPS["math"]
    if any(k in name for k in ["physics", "phys"]):
        return _STUDY_TIPS["physics"]
    if any(k in name for k in ["chem", "chemistry"]):
        return _STUDY_TIPS["chemistry"]
    if any(k in name for k in ["english", "writing", "language"]):
        return _STUDY_TIPS["english"]
    if any(k in name for k in ["history", "social"]):
        return _STUDY_TIPS["history"]
    if any(k in name for k in ["cs", "programming", "python", "code", "computer"]):
        return _STUDY_TIPS["cs"]
    return _STUDY_TIPS["default"]

def _smart_advice(s: dict) -> str:
    avg    = _average(s["subjects"])
    weak   = _weak_subject(s["subjects"])
    strong = _strong_subject(s["subjects"])
    em     = _status_emoji(avg)
    lines  = [f"🤖 *Smart Advisor Report*\n👤 {s['name']}\n"]

    # Overall status
    if avg >= 85:
        lines.append("🌟 *Overall: Excellent!*")
        lines.append("You're performing at a high level. Here's how to stay on top:\n")
    elif avg >= 70:
        lines.append("👍 *Overall: Good performance*")
        lines.append("You're doing well but there's room to grow:\n")
    elif avg >= 50:
        lines.append("⚠️ *Overall: Needs improvement*")
        lines.append("Don't worry — with the right approach you can improve:\n")
    else:
        lines.append("🚨 *Overall: At risk!*")
        lines.append("You need to take action now. Let's focus on what matters most:\n")

    # Trend analysis
    all_grades = []
    for grades in s["subjects"].values():
        all_grades.extend(grades)
    if len(all_grades) >= 4:
        half = len(all_grades) // 2
        early = sum(all_grades[:half]) / half
        recent = sum(all_grades[half:]) / (len(all_grades) - half)
        if recent > early + 3:
            lines.append("📈 *Trend: Your grades are improving! Keep it up!*\n")
        elif recent < early - 3:
            lines.append("📉 *Trend: Your grades have been declining lately. Time to refocus.*\n")
        else:
            lines.append("➡️ *Trend: Your performance is stable.*\n")

    # Weak subject advice
    if weak and _subj_avg(s["subjects"][weak]) < 70:
        wa = _subj_avg(s["subjects"][weak])
        tips = _get_subject_tips(weak)
        lines.append(f"🔴 *Focus area: {weak}* (avg: {wa})")
        lines.append("Specific tips for this subject:")
        for tip in tips:
            lines.append(f"  • {tip}")
        lines.append("")

    # Strong subject recognition
    if strong and _subj_avg(s["subjects"][strong]) >= 70:
        sa = _subj_avg(s["subjects"][strong])
        lines.append(f"🟢 *Strength: {strong}* (avg: {sa}) — keep it up!\n")

    # General advice based on avg
    lines.append("📌 *General recommendations:*")
    if avg >= 85:
        lines += [
            "  • Try tutoring classmates — it deepens your own knowledge",
            "  • Start preparing for exams 2 weeks early",
            "  • Explore advanced topics in your strongest subject",
        ]
    elif avg >= 70:
        lines += [
            "  • Spend 30 extra minutes daily on your weak subject",
            "  • Review lecture notes the same day",
            "  • Form a study group with 2-3 classmates",
        ]
    elif avg >= 50:
        lines += [
            "  • Visit your teacher during office hours for help",
            "  • Create a strict daily study schedule",
            "  • Focus on one subject at a time — don't spread yourself thin",
            "  • Use YouTube tutorials for topics you don't understand",
        ]
    else:
        lines += [
            "  • Talk to your academic advisor immediately",
            "  • Attend every class without exception",
            "  • Study at least 3 hours daily",
            "  • Ask for help — from teachers, tutors, or classmates",
            "  • Remove distractions: limit phone use during study time",
        ]

    return "\n".join(lines)


# ══════════════════════════════════════════════
#  GROUP STATS
# ══════════════════════════════════════════════
def _group_stats(data: list[dict]) -> str:
    if not data:
        return "📭 No students."
    avgs    = [_average(s["subjects"]) for s in data]
    at_risk = [s["name"] for s in data if _average(s["subjects"]) < 50]
    excellent = [s["name"] for s in data if _average(s["subjects"]) >= 85]
    lines = [
        "📊 *Group Statistics*\n",
        f"👥 Total students: *{len(data)}*",
        f"📈 Group average:  *{round(sum(avgs)/len(avgs), 2)}*",
        f"🏆 Highest avg:    *{max(avgs)}*",
        f"📉 Lowest avg:     *{min(avgs)}*",
    ]
    if excellent:
        lines.append(f"\n🌟 *Excellent students (≥85):*")
        for name in excellent:
            lines.append(f"  • {name}")
    if at_risk:
        lines.append(f"\n⚠️ *At-risk students (<50):*")
        for name in at_risk:
            lines.append(f"  • {name}")
    return "\n".join(lines)


# ══════════════════════════════════════════════
#  KEYBOARDS
# ══════════════════════════════════════════════
def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Student",    callback_data="menu_add_student"),
            InlineKeyboardButton("📝 Add Grade",      callback_data="menu_add_grade"),
        ],
        [
            InlineKeyboardButton("🔍 View Student",   callback_data="menu_view_student"),
            InlineKeyboardButton("📋 All Students",   callback_data="menu_all"),
        ],
        [
            InlineKeyboardButton("🏆 Top Student",    callback_data="menu_top"),
            InlineKeyboardButton("📊 Group Stats",    callback_data="menu_stats"),
        ],
        [
            InlineKeyboardButton("🤖 Smart Advice",   callback_data="menu_ai"),
            InlineKeyboardButton("⚖️ Compare",        callback_data="menu_compare"),
        ],
        [
            InlineKeyboardButton("⚠️ At-Risk",        callback_data="menu_atrisk"),
            InlineKeyboardButton("🗑 Delete Student",  callback_data="menu_delete"),
        ],
        [
            InlineKeyboardButton("📄 Full Report",    callback_data="menu_report"),
            InlineKeyboardButton("ℹ️ About",           callback_data="menu_about"),
        ],
    ])


# ══════════════════════════════════════════════
#  COMMANDS
# ══════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"🎓 *Smart Academic Assistant*\n\n"
        f"Hello, *{name}*! 👋\n\n"
        f"I help you track grades, analyse performance\n"
        f"and give smart study recommendations.\n\n"
        f"👇 Choose an action:",
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 *Main Menu*", parse_mode="Markdown", reply_markup=main_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Commands*\n\n"
        "*/start* — Main menu\n"
        "*/addstudent* — Add new student\n"
        "*/addgrade* — Add a grade\n"
        "*/view* — View student profile\n"
        "*/all* — List all students\n"
        "*/report* — Full detailed report\n"
        "*/stats* — Group statistics\n"
        "*/top* — Top student\n"
        "*/atrisk* — At-risk students\n"
        "*/advice* — 🤖 Smart study advice\n"
        "*/compare* — Compare two students\n"
        "*/delete* — Delete a student\n"
        "*/about* — About project\n"
        "*/cancel* — Cancel current action",
        parse_mode="Markdown",
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    await msg.reply_text(
        "ℹ️ *Smart Academic Assistant*\n\n"
        "A Python-based system for managing student\n"
        "grades and analysing academic performance.\n\n"
        "✨ *Features:*\n"
        "  • Student & grade management\n"
        "  • Performance analysis with trends\n"
        "  • Smart study recommendations\n"
        "  • Group statistics & at-risk alerts\n"
        "  • Student comparison\n\n"
        "👨‍💻 *Authors:* Aibyn Mukhametsharip,\n"
        "              Srazhdin Yasmin\n"
        "📚 *Group:* SE-2504",
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = _load()
    msg  = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    if not data:
        await msg.reply_text("📭 No students found.")
        return
    await msg.reply_text("📄 *Full Report*", parse_mode="Markdown")
    for s in data:
        await msg.reply_text(_format_student(s), parse_mode="Markdown")
    await msg.reply_text(_group_stats(data), parse_mode="Markdown", reply_markup=main_keyboard())

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = _load()
    msg  = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    await msg.reply_text(_group_stats(data), parse_mode="Markdown", reply_markup=main_keyboard())

async def top_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = _load()
    msg  = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    if not data:
        await msg.reply_text("📭 No students found.")
        return
    top = max(data, key=lambda s: _average(s["subjects"]))
    await msg.reply_text(
        f"🏆 *Top Student*\n\n{_format_student(top)}",
        parse_mode="Markdown", reply_markup=main_keyboard(),
    )

async def all_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = _load()
    msg  = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    if not data:
        await msg.reply_text("📭 No students found.")
        return
    lines = ["📋 *All Students*\n"]
    for i, s in enumerate(data, 1):
        avg = _average(s["subjects"])
        lines.append(
            f"{i}. {_status_emoji(avg)} *{s['name']}* "
            f"(`{s['student_id']}`) — *{avg}* {_grade_letter(avg)}"
        )
    await msg.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=main_keyboard())

async def at_risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = _load()
    msg  = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    risk = [s for s in data if _average(s["subjects"]) < 50]
    if not risk:
        await msg.reply_text("✅ No at-risk students! Everyone is above 50.", reply_markup=main_keyboard())
        return
    lines = ["⚠️ *At-Risk Students* (avg < 50)\n"]
    for s in risk:
        avg  = _average(s["subjects"])
        weak = _weak_subject(s["subjects"])
        lines.append(f"🔴 *{s['name']}* — avg: {avg}")
        if weak:
            lines.append(f"   Weakest: _{weak}_ ({_subj_avg(s['subjects'][weak])})")
    await msg.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=main_keyboard())


# ══════════════════════════════════════════════
#  ADD STUDENT conversation
# ══════════════════════════════════════════════
async def add_student_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    await msg.reply_text("✏️ Enter the student's *full name*:", parse_mode="Markdown")
    return ADD_STUDENT_NAME

async def add_student_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_name"] = update.message.text.strip()
    await update.message.reply_text("🆔 Enter a unique *student ID* (e.g. SE2504-01):", parse_mode="Markdown")
    return ADD_STUDENT_ID

async def add_student_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid  = update.message.text.strip()
    data = _load()
    if _find(data, sid):
        await update.message.reply_text(f"❌ ID `{sid}` already exists. Try another:", parse_mode="Markdown")
        return ADD_STUDENT_ID
    data.append({"name": context.user_data["new_name"], "student_id": sid, "subjects": {}})
    _save(data)
    await update.message.reply_text(
        f"✅ *{context.user_data['new_name']}* added!\n\nUse /addgrade to add their first grade.",
        parse_mode="Markdown", reply_markup=main_keyboard(),
    )
    return ConversationHandler.END


# ══════════════════════════════════════════════
#  ADD GRADE conversation
# ══════════════════════════════════════════════
async def add_grade_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    await msg.reply_text("🆔 Enter the *student ID*:", parse_mode="Markdown")
    return ADD_GRADE_ID

async def add_grade_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid  = update.message.text.strip()
    data = _load()
    s    = _find(data, sid)
    if not s:
        await update.message.reply_text("❌ Student not found. Enter a valid ID:")
        return ADD_GRADE_ID
    context.user_data["grade_sid"] = sid
    await update.message.reply_text(f"📚 Subject name for *{s['name']}*:", parse_mode="Markdown")
    return ADD_GRADE_SUBJECT

async def add_grade_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["grade_subject"] = update.message.text.strip()
    await update.message.reply_text("🔢 Enter the *grade* (0 – 100):", parse_mode="Markdown")
    return ADD_GRADE_VALUE

async def add_grade_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        grade = float(update.message.text.strip())
        if not (0 <= grade <= 100):
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Enter a number between 0 and 100:")
        return ADD_GRADE_VALUE
    data = _load()
    s    = _find(data, context.user_data["grade_sid"])
    subj = context.user_data["grade_subject"]
    s["subjects"].setdefault(subj, []).append(grade)
    _save(data)
    new_avg = _average(s["subjects"])
    await update.message.reply_text(
        f"✅ *Grade added!*\n\n"
        f"👤 {s['name']} → _{subj}_: *{grade}*\n"
        f"📊 New average: *{new_avg}* {_grade_letter(new_avg)} {_status_emoji(new_avg)}",
        parse_mode="Markdown", reply_markup=main_keyboard(),
    )
    return ConversationHandler.END


# ══════════════════════════════════════════════
#  VIEW STUDENT conversation
# ══════════════════════════════════════════════
async def view_student_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    await msg.reply_text("🆔 Enter the *student ID*:", parse_mode="Markdown")
    return VIEW_STUDENT_ID

async def view_student_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid  = update.message.text.strip()
    data = _load()
    s    = _find(data, sid)
    if not s:
        await update.message.reply_text("❌ Student not found. Try again:")
        return VIEW_STUDENT_ID
    await update.message.reply_text(_format_student(s), parse_mode="Markdown", reply_markup=main_keyboard())
    return ConversationHandler.END


# ══════════════════════════════════════════════
#  DELETE STUDENT conversation
# ══════════════════════════════════════════════
async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    await msg.reply_text("🗑 Enter the *student ID* to delete:\n_(This cannot be undone!)_", parse_mode="Markdown")
    return DELETE_STUDENT_ID

async def delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid  = update.message.text.strip()
    data = _load()
    s    = _find(data, sid)
    if not s:
        await update.message.reply_text("❌ Student not found.")
        return DELETE_STUDENT_ID
    data = [x for x in data if x["student_id"] != sid]
    _save(data)
    await update.message.reply_text(
        f"🗑 *{s['name']}* has been deleted.",
        parse_mode="Markdown", reply_markup=main_keyboard(),
    )
    return ConversationHandler.END


# ══════════════════════════════════════════════
#  SMART ADVICE conversation
# ══════════════════════════════════════════════
async def ai_advice_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    await msg.reply_text("🤖 Enter the *student ID* to get a smart study plan:", parse_mode="Markdown")
    return AI_ADVICE_ID

async def ai_advice_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid  = update.message.text.strip()
    data = _load()
    s    = _find(data, sid)
    if not s:
        await update.message.reply_text("❌ Student not found.")
        return AI_ADVICE_ID
    await update.message.reply_text("⏳ Analysing performance...")
    advice = _smart_advice(s)
    await update.message.reply_text(advice, parse_mode="Markdown", reply_markup=main_keyboard())
    return ConversationHandler.END


# ══════════════════════════════════════════════
#  COMPARE TWO STUDENTS conversation
# ══════════════════════════════════════════════
async def compare_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
    await msg.reply_text("⚖️ Enter *first student ID*:", parse_mode="Markdown")
    return COMPARE_ID1

async def compare_id1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid  = update.message.text.strip()
    data = _load()
    if not _find(data, sid):
        await update.message.reply_text("❌ Student not found. Try again:")
        return COMPARE_ID1
    context.user_data["cmp1"] = sid
    await update.message.reply_text("⚖️ Enter *second student ID*:", parse_mode="Markdown")
    return COMPARE_ID2

async def compare_id2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid2 = update.message.text.strip()
    data = _load()
    s2   = _find(data, sid2)
    if not s2:
        await update.message.reply_text("❌ Student not found. Try again:")
        return COMPARE_ID2
    s1   = _find(data, context.user_data["cmp1"])
    avg1 = _average(s1["subjects"])
    avg2 = _average(s2["subjects"])
    winner = s1["name"] if avg1 > avg2 else (s2["name"] if avg2 > avg1 else "Tie!")

    # Common subjects
    common = set(s1["subjects"]) & set(s2["subjects"])
    lines  = [
        "⚖️ *Student Comparison*\n",
        f"{'👤'} *{s1['name']}* vs *{s2['name']}*\n",
        f"📊 {s1['name']}: *{avg1}* {_grade_letter(avg1)} {_status_emoji(avg1)}",
        f"📊 {s2['name']}: *{avg2}* {_grade_letter(avg2)} {_status_emoji(avg2)}",
        f"\n🏆 Better overall: *{winner}*",
    ]
    if common:
        lines.append("\n📚 *Head-to-head by subject:*")
        for subj in sorted(common):
            a1 = _subj_avg(s1["subjects"][subj])
            a2 = _subj_avg(s2["subjects"][subj])
            w  = s1["name"] if a1 > a2 else (s2["name"] if a2 > a1 else "Tie")
            lines.append(f"  • *{subj}*: {a1} vs {a2} → _{w}_")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=main_keyboard())
    return ConversationHandler.END


# ══════════════════════════════════════════════
#  /cancel
# ══════════════════════════════════════════════
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❎ Cancelled.", reply_markup=main_keyboard())
    return ConversationHandler.END


# ══════════════════════════════════════════════
#  INLINE BUTTON ROUTER
# ══════════════════════════════════════════════
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = query.data
    if d == "menu_all":      await all_students(update, context)
    elif d == "menu_report": await report(update, context)
    elif d == "menu_top":    await top_student(update, context)
    elif d == "menu_stats":  await stats(update, context)
    elif d == "menu_about":  await about(update, context)
    elif d == "menu_atrisk": await at_risk(update, context)


# ══════════════════════════════════════════════
#  BOT SETUP
# ══════════════════════════════════════════════
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    convs = [
        ConversationHandler(
            entry_points=[CommandHandler("addstudent", add_student_start),
                          CallbackQueryHandler(add_student_start, pattern="^menu_add_student$")],
            states={ADD_STUDENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_student_name)],
                    ADD_STUDENT_ID:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_student_id)]},
            fallbacks=[CommandHandler("cancel", cancel)],
        ),
        ConversationHandler(
            entry_points=[CommandHandler("addgrade", add_grade_start),
                          CallbackQueryHandler(add_grade_start, pattern="^menu_add_grade$")],
            states={ADD_GRADE_ID:      [MessageHandler(filters.TEXT & ~filters.COMMAND, add_grade_id)],
                    ADD_GRADE_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_grade_subject)],
                    ADD_GRADE_VALUE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_grade_value)]},
            fallbacks=[CommandHandler("cancel", cancel)],
        ),
        ConversationHandler(
            entry_points=[CommandHandler("view", view_student_start),
                          CallbackQueryHandler(view_student_start, pattern="^menu_view_student$")],
            states={VIEW_STUDENT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, view_student_id)]},
            fallbacks=[CommandHandler("cancel", cancel)],
        ),
        ConversationHandler(
            entry_points=[CommandHandler("delete", delete_start),
                          CallbackQueryHandler(delete_start, pattern="^menu_delete$")],
            states={DELETE_STUDENT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_confirm)]},
            fallbacks=[CommandHandler("cancel", cancel)],
        ),
        ConversationHandler(
            entry_points=[CommandHandler("advice", ai_advice_start),
                          CallbackQueryHandler(ai_advice_start, pattern="^menu_ai$")],
            states={AI_ADVICE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_advice_run)]},
            fallbacks=[CommandHandler("cancel", cancel)],
        ),
        ConversationHandler(
            entry_points=[CommandHandler("compare", compare_start),
                          CallbackQueryHandler(compare_start, pattern="^menu_compare$")],
            states={COMPARE_ID1: [MessageHandler(filters.TEXT & ~filters.COMMAND, compare_id1)],
                    COMPARE_ID2: [MessageHandler(filters.TEXT & ~filters.COMMAND, compare_id2)]},
            fallbacks=[CommandHandler("cancel", cancel)],
        ),
    ]
    for conv in convs:
        app.add_handler(conv)

    for cmd, fn in [
        ("start",   start),   ("menu",    menu_command), ("help",  help_command),
        ("about",   about),   ("report",  report),       ("top",   top_student),
        ("all",     all_students), ("stats", stats),     ("atrisk", at_risk),
        ("cancel",  cancel),
    ]:
        app.add_handler(CommandHandler(cmd, fn))

    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Smart Academic Assistant is running...")
    app.run_polling()


if __name__ == "__main__":
    main()