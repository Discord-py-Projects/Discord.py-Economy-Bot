import discord
import sqlite3
import random
from discord.ext import commands

def get_random_color():
    return random.choice([0x4287f5, 0xf54242, 0xf5f242])

def open_account(user: discord.Member):
    db = sqlite3.connect('data/bank.sqlite')
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM main WHERE member_id = {user.id}")
    result = cursor.fetchone()

    if result:
        return
    if not result:
        sql = "INSERT INTO main(member_id, wallet, bank) VALUES(?,?,?)"
        val = (user.id, 500, 0)

    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()

def check_bal_greater_than(user: discord.Member, amount: int):
    db = sqlite3.connect('data/bank.sqlite')
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM main WHERE member_id = {user.id}")
    result = cursor.fetchone()

    if result[1] >= amount:
        return True
    return False

def add_bal(user: discord.Member, amount: int):
    db = sqlite3.connect('data/bank.sqlite')
    cursor = db.cursor()
    cursor.execute(f"SELECT * from main WHERE member_id = {user.id}")
    result = cursor.fetchone()

    sql = f"UPDATE main SET wallet = ? WHERE member_id = ?"
    val = (result[1] + amount, user.id)

    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()

def remove_bal(user: discord.Member, amount: int):
    db = sqlite3.connect('data/bank.sqlite')
    cursor = db.cursor()
    cursor.execute(f"SELECT * from main WHERE member_id = {user.id}")
    result = cursor.fetchone()

    sql = f"UPDATE main SET wallet = ? WHERE member_id = ?"
    val = (result[1] - amount, user.id)

    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close() 

class Economy(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="bal", aliases=['balance'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def balance(self, ctx, member: discord.Member=None):
        if member == None:
            member = ctx.author
        open_account(member)

        db = sqlite3.connect('data/bank.sqlite')
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM main WHERE member_id = {member.id}")
        result = cursor.fetchone()

        embed = discord.Embed(color=get_random_color(), timestamp=ctx.message.created_at)
        embed.set_author(name=f"{member.name}'s Balance", icon_url=member.avatar_url)
        embed.add_field(name="Wallet", value=f"{result[1]}")
        embed.add_field(name="Bank", value=f"{result[2]}")
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=member.avatar_url)
        embed.set_thumbnail(url=ctx.guild.icon_url)

        await ctx.send(embed=embed)

    @commands.command(name="beg")
    async def beg(self, ctx):
        open_account(user=ctx.author)
        possibility = random.randint(1, 5)
        if possibility == 3:
            return await ctx.send(
                "You begged for coins but recieved a 🩴 instead"
            )

        amount = random.randrange(60, 200)

        outcomes = [
            f"You got **{amount}**",
            f"Batman gave you **{amount}**",
            f"You begged your mom for **{amount}**"
        ]

        add_bal(ctx.author, amount)
        await ctx.send(random.choice(outcomes))

    @commands.command(name="dep", aliases=['deposit'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def dep(self, ctx, amount):
        open_account(user=ctx.author)
        db = sqlite3.connect('data/bank.sqlite')
        cursor = db.cursor()
        cursor.execute(f"SELECT * from main WHERE member_id = {ctx.author.id}")
        result = cursor.fetchone()

        if result[1] == 0:
            return await ctx.send(
                "You have 0 coins in your wallet :|"
            )
        done = False
        if amount == "all" or amount == "max":
            sql = "UPDATE main SET bank = ? WHERE member_id = ?"
            val = (result[2] + result[1], ctx.author.id)
            await ctx.send(f"Successfully deposited **{result[1]}**")
            remove_bal(ctx.author, result[1])  
            done = True
        if not done:
            try:
                amount = int(amount)
            except ValueError:
                return await ctx.send(
                    "Only `integers | max | all` will be excepted as the amount"
                )

            if result[1] < amount:
                return await ctx.send(
                    f"You cannot deposit more than **{result[1]}**"
                )
            
            sql = "UPDATE main SET bank = ? WHERE member_id = ?"
            val = (result[2] + amount, ctx.author.id)
            await ctx.send(
                f"Successfully deposited **{amount}**"
            )
            remove_bal(ctx.author, amount)

        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    @commands.command(name='gamble')
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def gamble(self, ctx, amount):
        open_account(user=ctx.author)
        try:
            amount = int(amount)
        except ValueError:
            self.client.get_command("gamble").reset_cooldown(ctx)
            return await ctx.send(
                "You have to give an integer small brain"
            )

        if amount < 100:
            self.client.get_command("gamble").reset_cooldown(ctx)
            return await ctx.send(
                "At least gamble 100 coins ._."
            )

        result = check_bal_greater_than(user=ctx.author, amount=amount)
        if result == False:
            self.client.get_command("gamble").reset_cooldown(ctx)
            return await ctx.send(
                "Your amount cannot be greater than your balance :|"
            )

        chance = random.randint(1, 4)
        if chance != 3:
            remove_bal(ctx.author, amount)
            return await ctx.send(
                "You lost the bet!"
            )
        multiplier = random.choice([2, 2.25, 2.5, 1.25, 1.5, 1.75])
        total_wallet = int(amount * multiplier)
        add_bal(ctx.author, total_wallet)
        await ctx.send(f"You won {total_wallet}!")

    @commands.command(name="with", aliases=['withdraw'])
    async def withdraw(self, ctx, amount: str):
        open_account(user=ctx.author)
        db = sqlite3.connect('data/bank.sqlite')
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM main WHERE member_id = {ctx.author.id}")
        result = cursor.fetchone()
        if result[2] == 0:
            return await ctx.send(
                "You dont have any balance in your bank :|"
            )
        done = False
        if amount == "max" or amount == "all":
            sql = "UPDATE main SET bank = ? WHERE member_id = ?"
            val = (0, ctx.author.id)
            add_bal(ctx.author, result[2])
            await ctx.send(
                f"You successfully deposited **{result[2]}** to your bank!"
            )
            done = True
        
        if not done:
            try:
                amount = int(amount)
            except ValueError:
                return await ctx.send(
                    "Only `integers | max | all` will be accepted"
                )

            if amount >= result[2]:
                sql = "UPDATE main SET bank = ? WHERE member_id = ?"
                val = (0, ctx.author.id)
                add_bal(ctx.author, result[2])
                await ctx.send(
                    f"You successfully deposited **{result[2]}** to your bank!"
                )
            else:
                sql = "UPDATE main SET bank = ? WHERE member_id = ?"
                val = (result[2] - amount, ctx.author.id)
                add_bal(ctx.author, amount)
                await ctx.send(
                    f"You successfully deposited **{amount}** to your bank!"
                )
        
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    @commands.command(name='work')
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def work(self, ctx):
        open_account(user=ctx.author)
        chance = [1, 4]
        if chance == 2:
            return await ctx.send(
                "You worked so hard that you got fired from your office ecks deeeeee"
            )

        amount = random.randrange(400, 600)
        outcomes = [
            f"You worked in your office for **{amount}**",
            f"Your boss was frustrated but you worked for him and got **{amount}**",
            f"You begged your boss for **{amount}**",
            f"You killed your boss and got **{amount}** from his wallet",
            f"You got a promotion! You earned **{amount}** today :D"
        ]

        await ctx.send(random.choice(outcomes))
        add_bal(ctx.author, amount)

    def get_rich_people(self):
        db = sqlite3.connect('data/bank.sqlite')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM main")
        result = cursor.fetchall()

        networths = [{"id" : member_id, "networth" : wallet + bank} for member_id, wallet, bank in result]
        networths.sort(reverse=True, key=lambda x: x["networth"])

        try:
            return networths[0:5]
        except ValueError:
            return networths

    @commands.command(name="leaderboard", aliases=['lb', 'rich'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def lb(self, ctx):
        open_account(user=ctx.author)
        rich_people = self.get_rich_people()
        
        if len(rich_people) == 0:
            return await ctx.send("There are no rich people in this server..")

        embed = discord.Embed(color=get_random_color(), timestamp=ctx.message.created_at)

        first_guy, first_guy_worth = rich_people[0]["id"], rich_people[0]["networth"]
        embed.add_field(
            name=f"1. {ctx.guild.get_member(first_guy)} | [{first_guy}]:",
            value=f"**{first_guy_worth}**",
            inline=False
        )

        try:
            second_guy, second_guy_worth = rich_people[1]["id"], rich_people[1]["networth"]
            embed.add_field(
            name=f"2. {ctx.guild.get_member(second_guy)} | [{second_guy}]:",
            value=f"**{second_guy_worth}**",
            inline=False
        )
        except IndexError:
            pass

        try:
            third_guy, third_guy_worth = rich_people[2]["id"], rich_people[2]["networth"]
            embed.add_field(
                name=f"3. {ctx.guild.get_member(third_guy)} | [{third_guy}]:",
                value=f"**{third_guy_worth}**",
                inline=False
            )
        except IndexError:
            pass

        try:
            fourth_guy, fourth_guy_worth = rich_people[3]["id"], rich_people[3]["networth"]
            embed.add_field(
                name=f"4. {ctx.guild.get_member(fourth_guy)} | [{fourth_guy}]:",
                value=f"**{fourth_guy_worth}**",
                inline=False
            )
        except IndexError:
            pass

        try:
            fifth_guy, fifth_guy_worth = rich_people[4]["id"], rich_people[4]["networth"]
            embed.add_field(
                name=f"5. {ctx.guild.get_member(fifth_guy)} | [{fifth_guy}]:",
                value=f"**{fifth_guy_worth}**",
                inline=False
            )
        except IndexError:
            pass

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=ctx.guild.icon_url)

        await ctx.send(embed=embed)

def setup(client):
    client.add_cog(Economy(client))