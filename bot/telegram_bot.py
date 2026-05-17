from models.student import Student
from analysis.analyzer import (
    analyze_performance,
    get_top_student
)

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

TOKEN = "8536857384:AAHKKlzju9tLZdp4S39trq5vaT6T-aeuLhU"


# TEST DATA
student1 = Student("Alex", "S101")
student1.add_grade("Math", 90)
student1.add_grade("Science", 75)

student2 = Student("Emma", "S102")
student2.add_grade("Math", 95)
student2.add_grade("Science", 92)

students = [student1, student2]


# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🎓 Welcome to Smart Academic Assistant Bot!"
    )


# HELP COMMAND
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "/start - Start bot\n"
        "/help - Show commands\n"
        "/report - Show student reports\n"
        "/topstudent - Show top student"
    )


# REPORT COMMAND
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = ""

    for student in students:

        average = student.calculate_average()

        recommendation = analyze_performance(student)

        text += (
            f"🎓 {student.name}\n"
            f"Average: {average}\n"
            f"Recommendation: {recommendation}\n\n"
        )

    await update.message.reply_text(text)


# TOP STUDENT COMMAND
async def top_student(update: Update, context: ContextTypes.DEFAULT_TYPE):

    top = get_top_student(students)

    if top:

        await update.message.reply_text(
            f"🏆 Top Student\n\n"
            f"Name: {top.name}\n"
            f"Average: {top.calculate_average()}"
        )


# BOT SETUP
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("report", report))
app.add_handler(CommandHandler("topstudent", top_student))

print("🤖 Bot is running...")

app.run_polling()