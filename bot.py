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
import validate_stickers
from telepot.aio.loop import MessageLoop
from telepot.namedtuple import ForceReply
from telepot.aio.delegate import per_chat_id, create_open, pave_event_space

with open(sys.path[0] + '/keys.json', 'r') as f:
    key = json.load(f)
class Stickers(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(Stickers, self).__init__(*args, **kwargs)
        self.askname = 'What do you want to name the pack?'
        self.retryname = 'Sorry, that name isnt valid, please try another.'
        self.asktitle = 'Great, now what do you want the title to be?'
        self.retrytitle = 'Sorry this title is too long, keep it less than 64 characters.'
        self.donemsg = 'You\'re ready to go! Start sending images and I will add them to the pack, then send /done when you\'re done, or reply to this message to set the emoji to be associated with the stickers.'
        self.stickeremoji = '😶'

    async def open(self, initial_msg, seed):
        await self.on_chat_message(initial_msg)
        self.from_id = initial_msg['from']['id']
        return True

    async def on_chat_message(self, msg):
        content_type, chat_type, chat_id, msg_date, msg_id = telepot.glance(msg, long=True)
        if chat_type == 'private':
            if content_type == 'text':
                command = msg['text'].lower()
                if command.startswith('/create'):
                    await self.sender.sendChatAction('typing')
                    await self.startstickers(msg)
                if command.startswith('/done'):
                    if self.packmade:
                        await self.sender.sendMessage('All done! The sticker pack has been made and the stickers have been added, you can now manage it in the official stickers bot or access it right now with https://t.me/addstickers/' + self.packname)
                        self.close()
                else:
                    try:
                        reply_msg = msg['reply_to_message']
                        reply_text = reply_msg['text']
                        #print(msg)
                        if reply_text in (self.askname, self.retryname):
                            await self.namehandler(msg)
                        elif reply_text in (self.asktitle, self.retrytitle):
                            await self.titlehandler(msg)
                        elif reply_text == self.donemsg:
                            self.stickeremoji = msg['text']
                    except KeyError:
                        return
            elif content_type == 'document':
                    await self.uploader(msg)
        return

    async def startstickers(self, msg):
        await self.sender.sendMessage(self.askname, reply_markup=ForceReply())
        self.packmade = False
        return

    async def namehandler(self, msg):
        packname = msg['text'] + '_by_batchstickerbot'
        namevalid = validate_stickers.name(packname)
        try:
            packexists = await bot.getStickerSet(packname)
        except telepot.exception.TelegramError:
            packexists = False
        if namevalid and not packexists:
            self.packname = packname
            await self.sender.sendMessage(self.asktitle, reply_markup=ForceReply())
        else:
            await self.sender.sendMessage(self.retryname, reply_markup=ForceReply())

    async def titlehandler(self, msg):
        try:
            if self.packname:
                packtitle = msg['text']
                titlevalid = validate_stickers.title(packtitle)
                if titlevalid:
                    self.packtitle = packtitle
                    await self.sender.sendMessage(self.donemsg)
        except AttributeError:
            await self.sender.sendMessage('Your session expired or you haven\'t started creating a pack, start one with /create.')

    async def uploader(self, msg):
        content_type, chat_type, chat_id, msg_date, msg_id = telepot.glance(msg, long=True)
        try:
            if self.packname and self.packtitle:
                if msg['document']['mime_type'] == 'image/png':
                    #file_id = msg['document']['file_id']
                    try:
                        if self.packmade:
                            await bot.addStickerToSet(self.from_id, self.packname, msg['document']['file_id'], self.stickeremoji)
                            await self.sender.sendMessage('Sticker added.', reply_to_message_id=msg_id)
                        else:
                            self.packmade = await bot.createNewStickerSet(self.from_id, self.packname, self.packtitle, msg['document']['file_id'], self.stickeremoji)
                            await self.sender.sendMessage('Sticker added.', reply_to_message_id=msg_id)
                    except telepot.exception.TelegramError as e:
                        error = str(e)
                        print(error)
                        if 'DIMENSIONS' in error:
                            await self.sender.sendMessage('Image has the wrong dimensions.', reply_to_message_id=msg_id)
                        elif 'BIG' in error:
                            await self.sender.sendMessage('File is too big.', reply_to_message_id=msg_id)
                else:
                    await self.sender.sendMessage('File is the wrong type.', reply_to_message_id=msg_id)
        except AttributeError:
            return


bot = telepot.aio.DelegatorBot(key['telegram'], [
    pave_event_space()(
        per_chat_id(), create_open, Stickers, timeout=70*1300),
])
loop = asyncio.get_event_loop()
loop.create_task(MessageLoop(bot).run_forever())
print('Started...')
loop.run_forever()
