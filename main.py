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
    await update.message.reply_text("🏏 Welcome to IPL Predictor! Use /addmatch <team1> vs <team2> to add a match.")

async def add_match(update: Update, context: CallbackContext):
    """Owner adds a match and clears old votes before triggering voting"""
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can add matches!")
        return

    if not context.args:
        await update.message.reply_text("Usage: /addmatch <Team1> vs <Team2>")
        return

    match = " ".join(context.args)

    # Reset matches before adding a new one
    match_details["current_matches"] = []  # Clear previous matches

    match_details["current_matches"].append(match)

    await update.message.reply_text(f"📢 Match added: {match}")

    # Trigger voting immediately
    await trigger_voting(update, context)



async def trigger_voting(update: Update, context: CallbackContext):
    """Automatically send voting buttons when a match is added"""
    if not match_details.get("current_matches"):
        return  # No matches to vote on

    matches = match_details["current_matches"]
    
    # If one match is scheduled
    if len(matches) == 1:
        teams = matches[0].split(" vs ")
        keyboard = [[InlineKeyboardButton(teams[0], callback_data=f"vote_{teams[0]}"),
                     InlineKeyboardButton(teams[1], callback_data=f"vote_{teams[1]}")]]
    
    else:  # Two matches scheduled
        teams1 = matches[0].split(" vs ")
        teams2 = matches[1].split(" vs ")
        keyboard = [
            [InlineKeyboardButton(teams1[0], callback_data=f"vote1_{teams1[0]}"),
             InlineKeyboardButton(teams1[1], callback_data=f"vote1_{teams1[1]}")],
            [InlineKeyboardButton(teams2[0], callback_data=f"vote2_{teams2[0]}"),
             InlineKeyboardButton(teams2[1], callback_data=f"vote2_{teams2[1]}")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🗳️ Place your vote!", reply_markup=reply_markup)


from telegram import InlineKeyboardMarkup, InlineKeyboardButton

async def vote(update: Update, context: CallbackContext):
    """Players vote manually using inline buttons"""
    if not match_details.get("current_matches") or len(match_details["current_matches"]) == 0:
        await update.message.reply_text("❌ No matches added yet! Wait for the admin.")
        return

    # Reuse the function to show voting buttons again
    await trigger_voting(update, context)



async def vote_button_handler(update: Update, context: CallbackContext):
    """Handles button clicks for voting."""
    query = update.callback_query
    user_id = query.from_user.id
    username = query.from_user.first_name

    # Parse the button callback data
    data = query.data.split("_")

    if len(data) == 2:  # One-match scenario
        _, chosen_team = data
        if user_id not in votes:
            votes[user_id] = {"username": username}
        votes[user_id]["match1"] = chosen_team
        await query.answer("✅ Your vote has been recorded!")

    elif len(data) == 3:  # Two-match scenario
        match_number, chosen_team = data[0][-1], data[1]
        if user_id not in votes:
            votes[user_id] = {"username": username}
        if match_number == "1":
            votes[user_id]["match1"] = chosen_team
        else:
            votes[user_id]["match2"] = chosen_team
        await query.answer("✅ Your vote has been recorded!")

    # Don't use edit_text() to remove buttons globally!



async def reveal_votes(update: Update, context: CallbackContext):
    """Reveals votes when the match starts"""
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can reveal votes!")
        return

    if not votes:
        await update.message.reply_text("No votes placed yet.")
        return

    vote_text = "\n".join(
        [f"{data['username']} voted for {data.get('match1', 'N/A')} | {data.get('match2', 'N/A')}" for data in votes.values()]
    )
    
    await update.message.reply_text(f"📢 Votes are now visible:\n{vote_text}")





from datetime import datetime  # Import for date tracking

from datetime import datetime  # Import for date tracking

from datetime import datetime  # Import for date tracking

async def set_winner(update: Update, context: CallbackContext):
    """Set winners for matches and distribute 12 points per match among correct voters."""
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can set the winner!")
        return

    if len(context.args) == 0:
        await update.message.reply_text("Usage: /setwinner <Match1 Winner> [Match2 Winner]")
        return

    # Determine if there's one or two winners based on input
    winner1 = context.args[0]
    winner2 = context.args[1] if len(context.args) > 1 else None  # Match 2 is optional

    today_date = datetime.now().strftime("%Y-%m-%d")

    # Get the fixture (match added via /addmatch)
    fixture = match_details.get("current_matches", ["N/A"])[0]  # Default to "N/A" if no match found

    # Count correct votes for match 1
    correct_match1 = sum(1 for vote in votes.values() if vote.get("match1") == winner1)
    
    # Count correct votes for match 2 (only if it was played)
    correct_match2 = sum(1 for vote in votes.values() if vote.get("match2") == winner2) if winner2 else 0

    results = []  # List for the result message

    # Assign points to players
    for user_id, vote_data in votes.items():
        username = vote_data.get("username", "Unknown")
        user_points = 0

        # For Match 1
        if vote_data.get("match1") == winner1 and correct_match1 > 0:
            user_points += 12 // correct_match1

        # For Match 2 (only if it was played)
        if winner2 and vote_data.get("match2") == winner2 and correct_match2 > 0:
            user_points += 12 // correct_match2

        # Save results to Google Sheets with the fixture column
        sheet.append_row([
            username,                          # Player Name
            vote_data.get("match1", "N/A"),    # Team Voted
            winner1,                           # Winner
            user_points,                       # Points Earned
            today_date,                        # Date
            fixture                            # Fixture (Match Added)
        ])

        results.append(f"{username} gets {user_points} points.")

    # Build and send result message
    result_text = f"🏆 Winners:\nMatch 1 Winner: {winner1}\n"
    if winner2:
        result_text += f"Match 2 Winner: {winner2}\n"
    result_text += "\n".join(results)

    await update.message.reply_text(result_text)

    # Clear votes for next match day
    votes.clear()





async def leaderboard(update: Update, context: CallbackContext):
    """Show leaderboard"""
    all_records = sheet.get_all_values()
    scores = {}

    for row in all_records[1:]:  # Skip header row
        if len(row) < 6:  # ✅ Ensure we have at least 6 values
            continue  

        name, _, _, points, _, _ = row[:6]  # ✅ Slice row to avoid unpacking errors

        try:
            points = int(points)  # ✅ Convert points to integer safely
        except ValueError:
            continue  # Skip rows with invalid points

        scores[name] = scores.get(name, 0) + points

    if not scores:
        await update.message.reply_text("No leaderboard data available.")
        return

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = "\n".join([f"{name}: {points} pts" for name, points in sorted_scores])

    await update.message.reply_text(f"🏆 Leaderboard:\n{leaderboard_text}")



async def plot_graph(update: Update, context: CallbackContext):
    """Generate a graph of total scores over time (x-axis: Fixture)"""
    all_records = sheet.get_all_values()
    scores = {}

    for row in all_records[1:]:  # Skip the header
        if len(row) < 6:  # Ensure the row has at least 6 values
            continue  

        name, _, _, total_points, match_date, fixture = row[:6]  # ✅ Using fixture for x-axis

        if name not in scores:
            scores[name] = {"fixtures": [], "points": []}

        scores[name]["fixtures"].append(fixture)  # ✅ Use fixture instead of date
        scores[name]["points"].append(int(total_points))

    # Plot the graph
    plt.figure(figsize=(10, 6))
    for name, data in scores.items():
        plt.plot(data["fixtures"], data["points"], marker='o', linestyle='-', label=name)

    plt.xlabel("Fixture")  # ✅ Changed from "Date" to "Fixture"
    plt.ylabel("Total Points")
    plt.title("IPL Score Progress Over Fixtures")
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

    for row in all_records[1:]:  # Skip the header
        if len(row) < 6:  # Updated from 5 to 6
            continue  # Skip rows that don't have enough data

        name, _, _, points, match_date, fixture = row  # Added `fixture`

        try:
            points = int(points)  # Convert points to integer
        except ValueError:
            continue  # Skip invalid rows

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

    # Save and send graph
    graph_path = "graph2.png"
    plt.savefig(graph_path)
    plt.close()

    with open(graph_path, "rb") as photo:
        await update.message.reply_photo(photo=photo)


async def plot_graph3(update: Update, context: CallbackContext):
    """Generate a bar chart for cumulative scores"""
    all_records = sheet.get_all_values()
    scores = {}

    for row in all_records[1:]:  # Skip the header
        if len(row) < 6:  # Updated from 5 to 6
            continue  # Skip rows that don't have enough data

        name, _, _, points, match_date, fixture = row  # Added `fixture`

        try:
            points = int(points)  # Ensure points are integers
        except ValueError:
            continue  # Skip rows with invalid points data

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

    # Save and send graph
    graph_path = "graph3.png"
    plt.savefig(graph_path)
    plt.close()

    with open(graph_path, "rb") as photo:
        await update.message.reply_photo(photo=photo)





def main():
    """Start the bot"""
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CallbackQueryHandler(vote_button_handler, pattern="^vote"))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addmatch", add_match))
    app.add_handler(CommandHandler("vote", vote))
    app.add_handler(CommandHandler("reveal", reveal_votes))
    app.add_handler(CommandHandler("setwinner", set_winner))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("graph", plot_graph))
    app.add_handler(CommandHandler("graph2", plot_graph2))
    app.add_handler(CommandHandler("graph3", plot_graph3))

    print("Bot is running...")
    app.run_polling()
    print("Polling started... Waiting for commands.")


if __name__ == "__main__":
    main()

