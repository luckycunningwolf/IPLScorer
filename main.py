import os
import datetime
from datetime import datetime
import matplotlib.pyplot as plt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Telegram Bot Token
TOKEN = "8118845254:AAHxkAnfoG7aYnaY2Cddji3AAzqtzVSHArQ"
OWNER_ID = 6884495226  # Replace with your Telegram ID (@userinfobot to get it)

# Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("IPL_Scores").sheet1  # Ensure 'sheet1' is the correct sheet

# Store votes and matches
votes = {}
match_details = {}

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("🏏 Welcome to IPL Predictor! Use /addmatch <team1> vs <team2> to add a match.")

async def add_match(update: Update, context: CallbackContext):
    """Owner adds a match"""
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can add matches!")
        return

    if not context.args:
        await update.message.reply_text("Usage: /addmatch <Team1> vs <Team2>")
        return

    match = " ".join(context.args)
    match_details["current_match"] = match
    await update.message.reply_text(f"📢 Match added: {match}\nPlayers, place your votes using /vote <team>!")

async def vote(update: Update, context: CallbackContext):
    """Players vote before the match starts"""
    user_id = update.message.from_user.id
    username = update.message.from_user.first_name

    if not match_details.get("current_match"):
        await update.message.reply_text("No match added yet! Wait for the admin.")
        return

    if not context.args:
        await update.message.reply_text("Please specify a team! Example: /vote CSK")
        return

    team = " ".join(context.args)
    votes[user_id] = (username, team)

    await update.message.reply_text(f"✅ {username}, your vote is recorded! Votes will be revealed when the match starts.")

async def reveal_votes(update: Update, context: CallbackContext):
    """Reveals votes when the match starts"""
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can reveal votes!")
        return

    if not votes:
        await update.message.reply_text("No votes placed yet.")
        return

    vote_text = "\n".join([f"{name} voted for {team}" for _, (name, team) in votes.items()])
    await update.message.reply_text(f"📢 Votes are now visible:\n{vote_text}")





from datetime import datetime  # Import for date tracking

from datetime import datetime  # Import for date tracking

async def set_winner(update: Update, context: CallbackContext):
    """Set match winner and calculate points"""
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can set the winner!")
        return

    if not context.args:
        await update.message.reply_text("Usage: /setwinner <team>")
        return

    winner = " ".join(context.args)
    today_date = datetime.now().strftime("%Y-%m-%d")  # Get today's date

    if not votes:
        await update.message.reply_text("No votes placed yet.")
        return

    points = {}  # Store points for each user

    # Count how many users voted for the winner
    correct_votes = sum(1 for _, team in votes.values() if team == winner)

    # Assign points based on votes
    for user, (name, team) in votes.items():
        if team == winner:
            if correct_votes == 3:
                points[user] = 2
            elif correct_votes == 2:
                points[user] = 3
            elif correct_votes == 1:
                points[user] = 6
            else:
                points[user] = 0  # No points if no one voted correctly
        else:
            points[user] = 0  # Wrong vote = 0 points

        # Save results to Google Sheets (Now includes date)
        sheet.append_row([name, team, winner, points[user], today_date])

    # Format and send results message BEFORE clearing votes
    result_text = f"🏆 The winner is {winner}!\n"
    for user, points_earned in points.items():
        name, _ = votes[user]  # Get name from votes
        result_text += f"🎉 {name} gets {points_earned} points!\n"

    await update.message.reply_text(result_text)  # ✅ FIXED: await added correctly

    # Reset votes after match result
    votes.clear()





async def leaderboard(update: Update, context: CallbackContext):
    """Show leaderboard"""
    all_records = sheet.get_all_values()
    scores = {}

    for row in all_records[1:]:  # Skip header row
        if len(row) < 5:  
            continue  # Skip incomplete rows

        name, _, _, points, _ = row  # ✅ Now correctly unpacking 5 values
        scores[name] = scores.get(name, 0) + int(points)

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = "\n".join([f"{name}: {points} pts" for name, points in sorted_scores])

    await update.message.reply_text(f"🏆 Leaderboard:\n{leaderboard_text}")


import matplotlib.pyplot as plt

async def plot_graph(update: Update, context: CallbackContext):
    """Generate a graph of total scores over time"""
    all_records = sheet.get_all_values()
    scores = {}

    for row in all_records[1:]:  # Skip the header
        if len(row) < 5:
            continue  # Skip rows that don't have enough data

        name, _, _, total_points, match_date = row

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
    plt.ylim(0, 12)  # Change 100 to your desired max limit
    plt.savefig(graph_path)
    plt.close()

    # ✅ FIXED: Properly await the reply_photo call
    await update.message.reply_photo(photo=open(graph_path, "rb"))


import numpy as np  # Import numpy for cumulative sum
import matplotlib.pyplot as plt

import numpy as np  
import matplotlib.pyplot as plt  

import numpy as np
import matplotlib.pyplot as plt

async def plot_graph2(update: Update, context: CallbackContext):
    """Generate a cumulative score graph over time"""
    all_records = sheet.get_all_values()
    scores = {}

    if len(all_records) <= 1:
        await update.message.reply_text("No data available to plot.")
        return

    for row in all_records[1:]:  # Skip the header
        if len(row) < 5:
            continue  # Skip incomplete rows

        name, _, _, points, match_date = row

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

    for row in all_records[1:]:  # Skip header row
        if len(row) < 5:
            continue  # Skip incomplete rows

        name, _, _, points, _ = row

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

