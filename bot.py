#!/usr/bin/env python3
import sys
import telepot, telepot.aio
import asyncio, aiofiles, aiohttp
import json
import datetime
from datetime import datetime, timedelta
import time
import os
import random
import regex
from telepot.aio.loop import MessageLoop
from threading import Lock

with open(sys.path[0] + '/keys.json', 'r') as f:
    key = json.load(f)
bot = telepot.aio.Bot(key['telegram'])
lock = Lock()
startime = time.time()
interv = []

#-1001132937659
async def ad_roll():
    async def ad_roll_loop(adnum):
        async with aiofiles.open('keys.json', 'r') as k:
            pkeys = json.loads(await k.read())
        channel_id = pkeys['channels']
        interval = pkeys['interval']
        async with aiofiles.open('ads.json', 'r') as a:
            ad = json.loads(await a.read())['ads']
        if adnum > len(ad) - 1:
            await ad_roll_loop(0)
        if os.path.isfile('skipfile'):
            os.remove('skipfile')
            await ad_roll_loop(adnum + 1)
        for c in channel_id:
            await bot.sendMessage(c, ad[adnum])
        dt = datetime.now() + timedelta(hours=int(interval))
        #await ad_roll_loop(adnum + 1)
        while datetime.now() < dt:
            await asyncio.sleep(1)
        await ad_roll_loop(adnum + 1)
    await ad_roll_loop(0)

async def on_command(msg):
    content_type, chat_type, chat_id, msg_date, msg_id = telepot.glance(msg, long=True)
    #print(chat_id)
    try:
        botcom = msg['entities'][0]['type']
        if not botcom == 'bot_command':
            return
    except KeyError:
        pass
    if content_type == 'text':
        if chat_type == 'private':
            from_id = msg['from']['id']
            if from_id == 284015590 or 105301944:
                command = msg['text'].lower()
                if command.startswith('/addad'):
                    await bot.sendChatAction(chat_id, 'typing')
                    await add_ad(msg)
                elif command.startswith('/delad'):
                    await bot.sendChatAction(chat_id, 'typing')
                    await del_ad(msg)
                elif command.startswith('/listads'):
                    await bot.sendChatAction(chat_id, 'typing')
                    await lister(msg)
                elif command.startswith('/setinterval'):
                    await bot.sendChatAction(chat_id, 'typing')
                    await set_intv(msg)
                elif command.startswith('/skipad'):
                    await bot.sendChatAction(chat_id, 'typing')
                    await skip_ad(msg)
                elif command.startswith('/help'):
                    await bot.sendMessage(chat_id, '/addad\n/delad\n/listads\n/setinterval\n/skipad')
        elif chat_type == 'channel':
            async with aiofiles.open('keys.json', 'r') as k:
                channelkey = json.loads(await k.read())
                channel_id = channelkey['channels']
            print(type(chat_id))
            print(type(channel_id))
            if str(chat_id) not in channel_id:
                channel_id.append(str(chat_id))
            async with aiodiles.open('keys.json', 'w') as ch:
                await ch.write(json.dumps(channelkey, indent=2))

async def add_ad(msg):
    async with aiofiles.open('ads.json', 'r') as f:
        adkey = json.loads(await f.read())
    content_type, chat_type, chat_id, msg_date, msg_id = telepot.glance(msg, long=True)
    command = msg['text'].lower()
    #print(reply)
    try:
        new_ad = command.split(' ', 1)[1]
    except IndexError:
        return
    adkey['ads'].append(new_ad)
    with lock:
        async with aiofiles.open('ads.json', 'w') as f:
            await f.write(json.dumps(adkey, indent=2))
    await bot.sendMessage(chat_id, 'Ads list updated')

async def lister(msg):
    content_type, chat_type, chat_id, msg_date, msg_id = telepot.glance(msg, long=True)
    async with aiofiles.open('ads.json', 'r') as f:
        ads = json.loads(await f.read())['ads']
    adlist = list()
    n = 1
    for i in ads:
        formatt = str(n) + '. ' + i + '\n'
        adlist.append(formatt)
        n += 1
    adslistf = ''.join(adlist)
    await bot.sendMessage(chat_id, adslistf, parse_mode='html')

async def set_intv(msg):
    content_type, chat_type, chat_id, msg_date, msg_id = telepot.glance(msg, long=True)
    command = msg['text'].lower()
    try:
        newintv = command.split(' ', 1)[1]
    except IndexError:
        return
    async with aiofiles.open('keys.json') as f:
        keyfile = json.loads(await f.read())
    try:
        float(newintv)
        keyfile['interval'] = newintv
        with open('keys.json', 'w') as f:
            json.dump(keyfile, f, indent=2)
        if newintv == '1':
            msgtex = newintv + ' hour.'
        else:
            msgtex = newintv + ' hours.'
        await bot.sendMessage(chat_id, 'Ad roll interval set to ' + msgtex)
    except ValueError:
        await bot.sendMessage(chat_id, 'Send a number')


async def del_ad(msg):
    content_type, chat_type, chat_id, msg_date, msg_id = telepot.glance(msg, long=True)
    command = msg['text'].lower()
    try:
        adselc = command.split(' ', 1)[1]
    except IndexError:
        return
    try:
        float(adselc)
        adn = int(adselc) - 1
    except ValueError:
        return
    async with aiofiles.open('ads.json', 'r') as f:
        ads = json.loads(await f.read())
    del ads['ads'][adn]
    with open('ads.json', 'w') as f:
        json.dump(ads, f, indent=2)
    await bot.sendMessage(chat_id, 'Ad number ' + str(adn + 1) + ' deleted')

async def skip_ad(msg):
    content_type, chat_type, chat_id, msg_date, msg_id = telepot.glance(msg, long=True)
    open('skipfile', 'a').close()
    await bot.sendMessage(chat_id, 'Next ad roll skipped')

loop = asyncio.get_event_loop()
loop.create_task(MessageLoop(bot,on_command).run_forever())
#loop.create_task(ad_roll())
cors = asyncio.wait([ad_roll()])
print('Started...')
loop.run_until_complete(cors)
loop.run_forever()
