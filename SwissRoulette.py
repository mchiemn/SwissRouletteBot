import discord
import json
import random
import os
from discord.ext import commands

if not os.environ.get("DISCORD_TOKEN"):
    from dotenv import load_dotenv
    load_dotenv()
# Token for the discord bot to use in the server
TOKEN = os.environ.get("DISCORD_TOKEN")

# Setting bot prefix to '!' so that commands are unique from normal messages
client = commands.Bot(command_prefix = '!')

# Function to know that the bot is on and ready
@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

# The next three functions are commands that are identical in how each is operated.
# These are the main commands (!red, !black, !green) that users will utilize in order to make bets.
# Embed messages are used to format the bot messages in a cleaner way and a json file is
# used to store all of the users and their statistics.

@client.command()
async def red(ctx,*, bet:int):
    # Opening the json file and set a variable to the file
    with open('UserMoney.json', 'r') as f:
        userMoney = json.load(f)
    
    # Call funtion that adds discord users that are not already on the json file
    await update_user_data(userMoney, ctx.message.author.id)

    # Validation check to ensure the bet amount is not over or negative
    # If it is not a valid bet, then wait for another command
    valid = await bet_validation(userMoney, ctx, bet)
    if not valid:
        return
    
    # Once the user is added in the json and bet is valid, then start the embed message
    botEmbed = discord.Embed(title = 'Your bet:', description = f'${bet} on Red', color = discord.Color.red())
    
    # Perform the roulette with the user's color choice and store result in boolean variable
    betResult = await roulette_Result('red', botEmbed)
    
    # Based on the results of the roulette, call function to update the user's
    # money accordingly
    await update_user_money(userMoney, bet, betResult, 'red', ctx, botEmbed)

    # When finished, send the embed message and dump the updated information back into
    # the json  
    await ctx.send(embed = botEmbed)
    with open('UserMoney.json', 'w') as f:
        json.dump(userMoney, f)

# Function for !black command that is the same as red
@client.command()
async def black(ctx,*, bet:int):
    with open('UserMoney.json', 'r') as f:
        userMoney = json.load(f)

    await update_user_data(userMoney, ctx.message.author.id)

    valid = await bet_validation(userMoney, ctx, bet)
    if not valid:
        return
    
    botEmbed = discord.Embed(title = 'Your bet:', description = f'${bet} on Black')
    betResult = await roulette_Result('black', botEmbed)
    await update_user_money(userMoney, bet, betResult, 'black', ctx, botEmbed)
    await ctx.send(embed = botEmbed)

    with open('UserMoney.json', 'w') as f:
        json.dump(userMoney, f)

# Function for !green command that is the same as red
@client.command()
async def green(ctx,*, bet:int):
    with open('UserMoney.json', 'r') as f:
        userMoney = json.load(f)

    await update_user_data(userMoney, ctx.message.author.id)

    valid = await bet_validation(userMoney, ctx, bet)
    if not valid:
        return

    botEmbed = discord.Embed(title = 'Your bet:', description = f'${bet} on Green', color = discord.Color.green())
    betResult = await roulette_Result('green', botEmbed)
    await update_user_money(userMoney, bet ,betResult, 'green', ctx, botEmbed)
    await ctx.send(embed = botEmbed)
    with open('UserMoney.json', 'w') as f:
        json.dump(userMoney, f)

# Function that allows users to buy their way back into roulette when they
# no longer have any money.  Users are given the base amount again and the
# number of buybacks done for the user increases by 1.
@client.command()
async def buyback(ctx):
    # Variable with the string version of the user's id to get from json
    user_id = str(ctx.message.author.id)
    with open('UserMoney.json', 'r') as f:
        userMoney = json.load(f)
    
    if userMoney[user_id]['Money'] != 0:
        await ctx.send(f'{ctx.message.author.mention} cannot buyback because you still have money!')
        with open('UserMoney.json', 'w') as f:
            json.dump(userMoney, f)
        return

    # Set the user's money and increase their buybacks
    userMoney[user_id]['Money'] = 10000
    userMoney[user_id]['Buybacks'] += 1
    await ctx.send(f'{ctx.message.author.mention} has bought back! Try not to lose it.')

    with open('UserMoney.json', 'w') as f:
        json.dump(userMoney, f)

# Stats command to allow users to check their money, buybacks, and profits
@client.command()
async def stats(ctx):
    with open('UserMoney.json', 'r') as f:
        userMoney = json.load(f)
    user = str(ctx.message.author.id)
    
    # Get each field of the user and print
    currentMoney = userMoney[user]['Money']
    currentBuybacks = userMoney[user]['Buybacks']
    currentProfit = userMoney[user]['Profit']
    statsEmbed = discord.Embed(title = f"{ctx.message.author.name}'s stats", description = 'Here are your stats!')
    statsEmbed.add_field(name = 'Money:', value = f'${currentMoney}')
    statsEmbed.add_field(name = 'Buybacks:', value = f'{currentBuybacks}')
    statsEmbed.add_field(name = 'Profit:', value = f'{currentProfit}')
    await ctx.send(embed = statsEmbed)
    with open('UserMoney.json', 'w') as f:
        json.dump(userMoney, f)

# Leaderboard command to let users see the rankings of all other users who play
@client.command()
async def leaderboard(ctx):
    with open('UserMoney.json', 'r') as f:
        userMoney = json.load(f)
    
    # Sort the json data based on the 'Profit' value from greatest to least
    topMoney = {k: v for k, v in sorted(userMoney.items(), key = lambda item: item[1]['Profit'], reverse=True)}
    usernames = ''
    
    # Print the standing, money, number of buybacks, and profit for each user based on money value
    for position, user, in enumerate(topMoney):
        moneyString = topMoney[user]['Money']
        buybackString = topMoney[user]['Buybacks']
        profitString = topMoney[user]['Profit']
        usernames += f'{position+1} - <@!{user}> : ${moneyString} with {buybackString} buybacks: ${profitString} profit\n'
    
    # Format and print leaderboard
    leaderboardEmbed = discord.Embed(title = 'LEADERBOARD')
    leaderboardEmbed.add_field(name = 'From greatest to least:', value = usernames, inline = False)
    await ctx.send(embed = leaderboardEmbed)
    with open('UserMoney.json', 'w') as f:
        json.dump(userMoney, f)

# Info command to allow users to be able to see a list of all of the commands that they can use with the bot
@client.command()
async def info(ctx):
    infoEmbed = discord.Embed(title = 'COMMANDS', description = 'Here are some of the commands that you can use:', color = discord.Color.blue())
    infoEmbed.add_field(name = '!black (bet amount)', value = 'Win = 2x your bet', inline=False)
    infoEmbed.add_field(name = '!red (bet amount)', value = 'Win = 2x your bet', inline=False)
    infoEmbed.add_field(name = '!green (bet amount)', value = 'Win = 25x your bet', inline=False)
    infoEmbed.add_field(name = '!buyback', value = 'Buy your way back in with your own money', inline=False)
    infoEmbed.add_field(name = '!stats', value = 'View your stats in roulette', inline=False)
    infoEmbed.add_field(name = '!leaderboard', value = 'View the current standings based on who has the most profit', inline=False)
    await ctx.send(embed = infoEmbed)

# Funtion to update a user's data to add them into the json file
async def update_user_data(userMoney, user):
    # If the user is not found within the json, then add them in
    user_id = str(user)
    if user_id not in userMoney:
        userMoney[user_id] = {}
        userMoney[user_id]['Money'] = 10000
        userMoney[user_id]['Buybacks'] = 0
        userMoney[user_id]['Profit'] = 0

# Function to perform the roulette and determine if the user wins
async def roulette_Result(userColor, botEmbed):
    # Get a random number from 0-14
    result = random.randrange(24)

    # If the random number is 1-7, then it is considered red and
    # is added to the message with an image
    if 1 <= result <= 12:
        color = 'red'
        botEmbed.add_field(name = "Result:", value = 'Red!')
        botEmbed.set_image(url = 'https://i.imgur.com/wVPieMM.png')
    
    # If the random number is 8-14, then it is considered black and
    # is added to the message with an image
    elif 13 <= result <= 24:
        color = 'black'
        botEmbed.add_field(name = "Result:", value = 'Black!')
        botEmbed.set_image(url = 'https://i.imgur.com/mJjcKet.jpg')
    
    # If the number is 0, then it is considered green and is added
    # to the message with an image
    else:
        color = 'green'
        botEmbed.add_field(name = "Result:", value = 'Green!')
        botEmbed.set_image(url = 'https://i.imgur.com/8XymAk7.png')
    
    # If the chosen color matches the roulette's color, then the user wins
    if userColor == color:
        return True
    else:
        return False

# Function to calculate the change in money for the user based on whether
# they win, lose, or win with green
async def update_user_money(userMoney, bet, betResult, color, user, botEmbed):
    user_id = str(user.message.author.id)

    # If the user wins, then detemine if they win with green or not
    if betResult:
        # If the user wins with green, then they win 25 times their bet amount
        if color == 'green':
            greenWin = bet * 24
            userMoney[user_id]['Money'] += greenWin
            # Update the user's profit
            userMoney[user_id]['Profit'] += greenWin
            currentMoney = userMoney[user_id]['Money']
            botEmbed.add_field(name = f'{user.message.author.name} won ${greenWin} and now has ${currentMoney}! HUGE!!!', value = 'FAT DUB', inline = False)
        # If the user wins with black or red, then double their money
        else:
            userMoney[user_id]['Money'] += bet
            userMoney[user_id]['Profit'] += bet
            currentMoney = userMoney[user_id]['Money']
            botEmbed.add_field(name = f'{user.message.author.name} won ${bet} and now has ${currentMoney}!', value = 'W', inline = False)            
    # If they lose, then the user loses their bet amount
    else:
            userMoney[user_id]['Money'] -= bet
            userMoney[user_id]['Profit'] -= bet
            currentMoney = userMoney[user_id]['Money']
            botEmbed.add_field(name = f'{user.message.author.name} lost ${bet} and now has ${currentMoney}!', value = 'L', inline = False)            

# Function to validate the bet ammount
async def bet_validation(userMoney, user, bet):
    user_id = str(user.message.author.id)
    # Bet cannot happen when user has no money
    if userMoney[user_id]['Money'] == 0:
        await user.send(f'{user.message.author.mention} has no money left. Use !buyback to buyback in.')
        return False
    # Cannot bet more money than what the user has
    if bet > userMoney[user_id]['Money']:
        await user.send('You cannot bet more than you have!')
        return False
    # Cannot bet a negative value
    if bet <= 0:
        await user.send('You cannot have a negative bet!')
        return False
    else:
        return True

client.run(TOKEN)
