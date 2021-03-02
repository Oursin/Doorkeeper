import os
import discord
import itertools

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True

class EnterClient(discord.Client):
    inns = []

    async def on_ready(self):
        for server in self.guilds:
            inn = 0
            for channel in server.channels:
                if channel.type == discord.ChannelType.category and channel.name == 'Inn':
                    inn = channel
                    break
            door = 0
            tables = []
            for channel in server.channels:
                if channel.type == discord.ChannelType.voice and channel.category_id == inn.id:
                    if channel.name == 'door':
                        door = channel
                    else:
                        tables.append(channel)
            self.inns.append((inn, door, tables))
            to_cleanup = []
            for t in tables:
                if len(t.members) == 0:
                    await t.delete()
                    to_cleanup.append(t)
            for t in to_cleanup:
                tables.remove(t)

    def get_inn(self, channel):
        return next(filter(lambda x: x[0].id == channel.category_id, self.inns), None)

    def check_table_exists(self, inn, table_name):
        return next(filter(lambda x: x.name == table_name, inn[2]), None)

    def create_table_name(self, inn):
        for i in itertools.count(1, step=1):
            if self.check_table_exists(inn, f'table-{i}') is None:
                return f'table-{i}'

    async def create_table(self, inn):
        table_name = self.create_table_name(inn)
        table = await inn[0].create_voice_channel(table_name)
        inn[2].append(table)
        return table

    async def invite_guest(self, table, member):
        await member.move_to(table)

    async def new_guest(self, member, after):
        if after.channel is None:
            return
        inn = self.get_inn(after.channel)
        if inn is None:
            return
        if after.channel.id == inn[1].id:
            table = await self.create_table(inn)
            await self.invite_guest(table, member)

    async def guest_leaving(self, member, before):
        if before.channel is None:
            return
        inn = self.get_inn(before.channel)
        if inn is None:
            return
        if before.channel.id != inn[1].id and len(before.channel.members) == 0:
            await before.channel.delete()
            for t in inn[2]:
                if t.id == before.channel.id:
                    inn[2].remove(t)
                    break

    async def on_voice_state_update(self, member, before, after):
        await self.new_guest(member, after)
        await self.guest_leaving(member, before)


client = EnterClient(intents=intents)
client.run(os.getenv('CLIENT_SECRET'))
