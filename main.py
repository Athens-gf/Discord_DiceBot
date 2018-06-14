import parse
import discord
import help

btf = open('token.txt', 'r')
BOT_TOKEN = btf.read().replace('\n', '').strip()
btf.close()
help_mes = help.help_mes
client = discord.Client()


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


# メッセージを受信した時
@client.event
async def on_message(message):
    # 送り主がBotだった場合反応したくないので
    if message.author.bot:
        return
    if message.content.lower().startswith('!d') or parse.get_d(message.server.id):
        content = message.content
        if not parse.get_d(message.server.id):
            content = message.content[2:]
        if content.lower().startswith('help'):
            system = message.content[4:].strip()
            if system == '':
                system = 'Base'
            await client.send_message(message.channel, '```\n%s\n```' % help_mes[system])
        elif content.lower().strip() == 'allcommand':
            parse.set_d(message.server.id,
                        not parse.get_d(message.server.id))
            if parse.get_d(message.server.id):
                await client.send_message(message.channel, '```全てコマンドと認識するよう設定されました．```')
            else:
                await client.send_message(message.channel, '```全てコマンドと認識する設定を解除しました．```')
        elif content.lower().strip() == 'getall':
            mes = parse.get_all_regist(message.server.id)
            if mes:
                await client.send_message(message.channel, '<@%s> \n```%s```' % (message.author.id, mes))
        elif content.lower().strip() == 'get':
            mes = parse.get_regist(message.server.id, message.author.name)
            if mes:
                await client.send_message(message.channel, '<@%s> \n```%s```' % (message.author.id, mes))
        elif content.lower().startswith('del'):
            valcom = content[3:].strip()
            if len(valcom) == 0:
                if parse.delete_regist_name(message.server.id, message.author.name):
                    await client.send_message(message.channel, '<@%s> \n```%sの登録コマンドを削除しました．```' %
                                              (message.author.id, message.author.name))
            else:
                if parse.delete_regist_valcom(
                        message.server.id, message.author.name, valcom):
                    await client.send_message(message.channel, '<@%s> \n```登録%sを削除しました．```' %
                                              (message.author.id, valcom))
        elif content.lower().startswith('logout'):
            if parse.is_one_access_server():
                mes = parse.get_all_regist(message.server.id)
                if mes:
                    await client.send_message(message.channel, '<@%s> \n```%s```' % (message.author.id, mes))
                await client.logout()
        elif content.lower().startswith('sc'):
            res, is_dice = parse.parse(
                message.server.id, message.author.name, content[2:])
            if res:
                mes = '```%s```' % '\n'.join(res)
                await client.send_message(message.author, mes)
                if is_dice:
                    await client.send_message(message.channel, '%sはダイスを振ったようだ…' % message.author.name)
#                    voice_channel = message.author.voice_channel
#                    if voice_channel:
#                        voice = await client.join_voice_channel(voice_channel)
#                        player = voice.create_ffmpeg_player('dice.wav')
#                        player.start()
#                        while player.is_playing():
#                            pass
#                        await voice.disconnect()
        else:
            res, _ = parse.parse(
                message.server.id, message.author.name, content)
            if res:
                mes = '<@%s> \n```%s```' % (
                    message.author.id, '\n'.join(res))
                await client.send_message(message.channel, mes)
'''                
                if is_dice:
                    voice_channel = message.author.voice_channel
                    if voice_channel:
                        voice = await client.join_voice_channel(voice_channel)
                        player = voice.create_ffmpeg_player('dice.wav')
                        player.start()
                        while player.is_playing():
                            pass
                        await voice.disconnect()
'''

# サーバーから切断された時


@client.event
async def on_server_remove(server):
    print(parse.data)
    print(server.id)
    parse.delete_server(server.id)
    print(parse.data)

client.run(BOT_TOKEN)
