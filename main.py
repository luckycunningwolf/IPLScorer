import os
import datetime
from datetime import datetime
import matplotlib.pyplot as plt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler


import os
import json
from oauth2client.service_account import ServiceAccountCredentials

# Telegram Bot Token
TOKEN = "8118845254:AAHxkAnfoG7aYnaY2Cddji3AAzqtzVSHArQ"
OWNER_ID = 6884495226  # Replace with your Telegram ID (@userinfobot to get it)

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from the environment variable
credentials_json = os.getenv("GOOGLE_CREDENTIALS")

if not credentials_json:
    raise Exception("GOOGLE_CREDENTIALS environment variable is not set")

# Convert JSON string to dictionary
credentials_dict = json.loads(credentials_json)

# Authenticate using the credentials
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open("IPL_Scores").sheet1
 # Ensure 'sheet1' is the correct sheet

# Store votes and matches
votes = {}
match_details = {}

# Now you can use 'creds' for authentication in Google APIs


# Store votes and matches
votes = {}
match_details = {}

async def start(update: Update, context: CallbackContext):
    """Handles the /start command and shows available commands."""
    start_message = (
        "🏏 **Welcome to IPL Predictor!** 🎉\n\n"
        "Use the commands below to interact with the bot:\n\n"
        
        "🏆 **Leaderboard & Scores**\n"
        "📊 /leaderboard - View the current leaderboard.\n\n"
        
        "🗳 **Voting & Matches**\n"
        "📝 /addmatch <Team1> vs <Team2> - Add a new match (Admin only).\n"
        "🔘 /vote - Vote for a team.(only use this when normal voting isn't working)\n"
        "📢 /reveal - Reveal all votes.\n"
        "🏅 /setwinner <Team> - Set the match winner (Admin only).\n\n"
        
        "📊 **Graphs & Analysis**\n"
        "📈 /graph1 - Show daily match scores.\n"
        "📊 /graph2 - Show cumulative scores.\n"
        "📉 /graph3 - Show a bar chart of the leaderboard.\n\n"
        
        "✨ **Type a command or click on one to get started!** 🚀"
    )

    await update.message.reply_text(start_message, parse_mode="Markdown")


async def add_match1(update: Update, context: CallbackContext):
    """Owner adds Match 1 and clears old votes before triggering voting"""
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can add matches!")
        return

    if not context.args:
        await update.message.reply_text("Usage: /addmatch1 <Team1> vs <Team2>")
        return

    match = " ".join(context.args)

    # Reset Match 1 before adding a new one
    match_details["match1"] = match  # Store Match 1 separately

    global match1_votes
    match1_votes = {}  # Clear previous votes for Match 1

    await update.message.reply_text(f"📢 Match 1 added: {match}")

    # Trigger voting for Match 1
    await trigger_voting1(update, context)


async def add_match2(update: Update, context: CallbackContext):
    """Owner adds Match 2 and clears old votes before triggering voting"""
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can add matches!")
        return

    if not context.args:
        await update.message.reply_text("Usage: /addmatch2 <Team1> vs <Team2>")
        return

    match = " ".join(context.args)

    # Reset Match 2 before adding a new one
    match_details["match2"] = match  # Store Match 2 separately

    global match2_votes
    match2_votes = {}  # Clear previous votes for Match 2

    await update.message.reply_text(f"📢 Match 2 added: {match}")

    # Trigger voting for Match 2
    await trigger_voting2(update, context)




async def trigger_voting1(update: Update, context: CallbackContext):
    """Automatically send voting buttons for Match 1"""
    if "match1" not in match_details or not match_details["match1"]:
        return  # No match added yet

    teams = match_details["match1"].split(" vs ")
    keyboard = [[InlineKeyboardButton(teams[0], callback_data=f"vote1_{teams[0]}"),
                 InlineKeyboardButton(teams[1], callback_data=f"vote1_{teams[1]}")]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🗳️ Place your vote for Match 1!", reply_markup=reply_markup)


async def trigger_voting2(update: Update, context: CallbackContext):
    """Automatically send voting buttons for Match 2"""
    if "match2" not in match_details or not match_details["match2"]:
        return  # No match added yet

    teams = match_details["match2"].split(" vs ")
    keyboard = [[InlineKeyboardButton(teams[0], callback_data=f"vote2_{teams[0]}"),
                 InlineKeyboardButton(teams[1], callback_data=f"vote2_{teams[1]}")]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🗳️ Place your vote for Match 2!", reply_markup=reply_markup)



from telegram import InlineKeyboardMarkup, InlineKeyboardButton

async def vote1(update: Update, context: CallbackContext):
    """Players vote manually using inline buttons for Match 1"""
    if "match1" not in match_details or not match_details["match1"]:
        await update.message.reply_text("❌ No Match 1 added yet! Wait for the admin.")
        return

    # Show voting buttons for Match 1
    await trigger_voting1(update, context)


async def vote2(update: Update, context: CallbackContext):
    """Players vote manually using inline buttons for Match 2"""
    if "match2" not in match_details or not match_details["match2"]:
        await update.message.reply_text("❌ No Match 2 added yet! Wait for the admin.")
        return

    # Show voting buttons for Match 2
    await trigger_voting2(update, context)




async def vote_button_handler1(update: Update, context: CallbackContext):
    """Handles button clicks for voting on Match 1."""
    query = update.callback_query
    user_id = query.from_user.id
    username = query.from_user.first_name

    data = query.data.split("_")

    if user_id not in match1_votes:
        match1_votes[user_id] = {"username": username, "match1": None}

    if len(data) == 2:  # Match 1 voting scenario
        _, chosen_team = data
        match1_votes[user_id]["match1"] = chosen_team
        await query.answer(f"✅ Vote recorded for Match 1: {chosen_team}!")


async def vote_button_handler2(update: Update, context: CallbackContext):
    """Handles button clicks for voting on Match 2."""
    query = update.callback_query
    user_id = query.from_user.id
    username = query.from_user.first_name

    data = query.data.split("_")

    if user_id not in match2_votes:
        match2_votes[user_id] = {"username": username, "match2": None}

    if len(data) == 2:  # Match 2 voting scenario
        _, chosen_team = data
        match2_votes[user_id]["match2"] = chosen_team
        await query.answer(f"✅ Vote recorded for Match 2: {chosen_team}!")




    # ✅ Buttons remain active for others—only user's button click is processed



async def reveal_votes1(update: Update, context: CallbackContext):
    """Reveals votes for Match 1 - Now accessible to all users!"""
    
    if not match1_votes:
        await update.message.reply_text("❌ No votes have been placed for Match 1 yet!")
        return

    vote_text = "\n".join(
        [
            f"👤 **{data['username']}**\n"
            f"🏅 **Match 1:** {data['match1'] if 'match1' in data else '❌ No Vote'}"
            for data in match1_votes.values()
        ]
    )

    await update.message.reply_text(f"📢 **Votes for Match 1 Revealed!**\n\n{vote_text}", parse_mode="Markdown")


async def reveal_votes2(update: Update, context: CallbackContext):
    """Reveals votes for Match 2 - Now accessible to all users!"""
    
    if not match2_votes:
        await update.message.reply_text("❌ No votes have been placed for Match 2 yet!")
        return

    vote_text = "\n".join(
        [
            f"👤 **{data['username']}**\n"
            f"🏅 **Match 2:** {data['match2'] if 'match2' in data else '❌ No Vote'}"
            for data in match2_votes.values()
        ]
    )

    await update.message.reply_text(f"📢 **Votes for Match 2 Revealed!**\n\n{vote_text}", parse_mode="Markdown")







from datetime import datetime  # Import for date tracking

from datetime import datetime  # Import for date tracking

from datetime import datetime  # Import for date tracking

async def set_winner1(update: Update, context: CallbackContext):
    """Set winner for Match 1 and distribute 12 points among correct voters."""
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can set the winner!")
        return

    if len(context.args) == 0:
        await update.message.reply_text("Usage: /setwinner1 <Match1 Winner>")
        return

    winner1 = context.args[0]
    today_date = datetime.now().strftime("%d-%m")

    fixture = match_details.get("current_matches", ["N/A"])[0]  # Default to "N/A" if no match found

    correct_match1 = sum(1 for vote in match1_votes.values() if vote.get("match1") == winner1)

    results = []

    for user_id, vote_data in match1_votes.items():
        username = vote_data.get("username", "Unknown")
        user_points = 12 // correct_match1 if correct_match1 > 0 and vote_data.get("match1") == winner1 else 0

        sheet.append_row([
            username,
            vote_data.get("match1", "N/A"),
            winner1,
            user_points,
            today_date,
            fixture
        ])

        results.append(f"{username} gets {user_points} points.")

    result_text = f"🏆 Winner:\nMatch 1 Winner: {winner1}\n" + "\n".join(results)

    await update.message.reply_text(result_text)

    match1_votes.clear()


async def set_winner2(update: Update, context: CallbackContext):
    """Set winner for Match 2 and distribute 12 points among correct voters."""
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can set the winner!")
        return

    if len(context.args) == 0:
        await update.message.reply_text("Usage: /setwinner2 <Match2 Winner>")
        return

    winner2 = context.args[0]
    today_date = datetime.now().strftime("%d-%m")

    fixture = match_details.get("current_matches", ["N/A"])[1] if len(match_details.get("current_matches", [])) > 1 else "N/A"

    correct_match2 = sum(1 for vote in match2_votes.values() if vote.get("match2") == winner2)

    results = []

    for user_id, vote_data in match2_votes.items():
        username = vote_data.get("username", "Unknown")
        user_points = 12 // correct_match2 if correct_match2 > 0 and vote_data.get("match2") == winner2 else 0

        sheet.append_row([
            username,
            vote_data.get("match2", "N/A"),
            winner2,
            user_points,
            today_date,
            fixture
        ])

        results.append(f"{username} gets {user_points} points.")

    result_text = f"🏆 Winner:\nMatch 2 Winner: {winner2}\n" + "\n".join(results)

    await update.message.reply_text(result_text)

    match2_votes.clear()






async def leaderboard(update: Update, context: CallbackContext):
    """Show a clean and stylish leaderboard highlighting the leader."""
    all_records = sheet.get_all_values()
    scores = {}

    for row in all_records[1:]:  # Skip header row
        if len(row) < 4:  # ✅ Ensure necessary columns exist
            continue  

        name, _, _, points = row[:4]  # ✅ Extract relevant fields

        try:
            points = int(points)  # ✅ Convert points safely
        except ValueError:
            continue  # Skip invalid rows

        scores[name] = scores.get(name, 0) + points

    if not scores:
        await update.message.reply_text("🏆 No leaderboard data available yet!")
        return

    # Sort scores in descending order
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Extract the leader
    leader_name, leader_points = sorted_scores[0]
    
    leaderboard_text = f"🏆 **IPL Predictor Leaderboard** 🏆\n\n"
    leaderboard_text += f"👑 **Current Leader:** {leader_name} - **{leader_points} pts** 🎖\n\n"
    leaderboard_text += "📊 **Top Players:**\n"

    # Format leaderboard display
    for rank, (name, points) in enumerate(sorted_scores, start=1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "🎯"
        leaderboard_text += f"{medal} {rank}. **{name}** - {points} pts\n"

    await update.message.reply_text(leaderboard_text, parse_mode="Markdown")



import numpy as np

async def plot_graph(update: Update, context: CallbackContext):
    """Generate a graph of total scores over time"""
    all_records = sheet.get_all_values()
    scores = {}

    for row in all_records[1:]:  # Skip the header
        if len(row) < 6:  # Ensure the row has at least 6 values
            continue  

        name, _, _, total_points, match_date, fixture = row[:6]  # ✅ Slice row to avoid extra values

        if name not in scores:
            scores[name] = {"dates": [], "points": []}

        scores[name]["dates"].append(match_date)
        scores[name]["points"].append(int(total_points))

    # Plot the graph
    plt.figure(figsize=(10, 6))
    for name, data in scores.items():
        plt.plot(data["dates"], data["points"], marker='o', linestyle='-', label=name)

    plt.xlabel("Date")
    plt.ylabel("Total Points")
    plt.title("IPL Score Progress Over Time")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid()

    # Save and send graph
    graph_path = "graph.png"
    plt.ylim(0, 12)  # Change as needed
    plt.savefig(graph_path)
    plt.close()

    await update.message.reply_photo(photo=open(graph_path, "rb"))


async def plot_graph2(update: Update, context: CallbackContext):
    """Generate a cumulative score graph over time"""
    all_records = sheet.get_all_values()
    scores = {}

    if len(all_records) <= 1:
        await update.message.reply_text("No data available to plot.")
        return

    for row in all_records[1:]:
        if len(row) < 6:
            continue

        name, _, _, points, match_date, fixture = row[:6]  # ✅ Slice row to avoid errors

        try:
            points = int(points)
        except ValueError:
            continue

        if name not in scores:
            scores[name] = {"dates": [], "points": []}

        scores[name]["dates"].append(match_date)
        scores[name]["points"].append(points)

    if not scores:
        await update.message.reply_text("No valid data available to plot.")
        return

    plt.figure(figsize=(10, 6))

    for name, data in scores.items():
        sorted_dates, sorted_points = zip(*sorted(zip(data["dates"], data["points"])))
        cumulative_points = np.cumsum(sorted_points)

        plt.plot(sorted_dates, cumulative_points, marker='o', linestyle='-', label=name)

    plt.xlabel("Date")
    plt.ylabel("Total Points (Cumulative)")
    plt.title("IPL Score Progress Over Time")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid()

    graph_path = "graph2.png"
    plt.savefig(graph_path)
    plt.close()

    with open(graph_path, "rb") as photo:
        await update.message.reply_photo(photo=photo)


async def plot_graph3(update: Update, context: CallbackContext):
    """Generate a bar chart for cumulative scores"""
    all_records = sheet.get_all_values()
    scores = {}

    for row in all_records[1:]:
        if len(row) < 6:
            continue

        name, _, _, points, match_date, fixture = row[:6]  # ✅ Slice row to avoid errors

        try:
            points = int(points)
        except ValueError:
            continue

        scores[name] = scores.get(name, 0) + points

    if not scores:
        await update.message.reply_text("No data available to plot.")
        return

    names = list(scores.keys())
    total_points = list(scores.values())

    plt.figure(figsize=(10, 6))
    plt.bar(names, total_points, color='skyblue')
    plt.xlabel("Players")
    plt.ylabel("Total Points")
    plt.title("Cumulative Score Bar Chart")
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    graph_path = "graph3.png"
    plt.savefig(graph_path)
    plt.close()

    with open(graph_path, "rb") as photo:
        await update.message.reply_photo(photo=photo)





def main():
    """Start the bot"""
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CallbackQueryHandler(vote_button_handler1, pattern="^vote1"))
    app.add_handler(CallbackQueryHandler(vote_button_handler2, pattern="^vote2"))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addmatch1", add_match1))
    app.add_handler(CommandHandler("addmatch2", add_match2))
    app.add_handler(CommandHandler("vote1", vote1))
    app.add_handler(CommandHandler("vote2", vote2))
    app.add_handler(CommandHandler("reveal", reveal_votes))
    app.add_handler(CommandHandler("setwinner1", set_winner1))
    app.add_handler(CommandHandler("setwinner2", set_winner2))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("graph1", plot_graph))
    app.add_handler(CommandHandler("graph2", plot_graph2))
    app.add_handler(CommandHandler("graph3", plot_graph3))

    print("Bot is running...")
    app.run_polling()
    print("Polling started... Waiting for commands.")


if __name__ == "__main__":
    main()

