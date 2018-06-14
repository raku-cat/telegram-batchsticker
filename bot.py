#!/usr/bin/env python3
import sys
import telepot, telepot.aio
import asyncio, aiofiles
import json
import validate_stickers
from telepot.aio.loop import MessageLoop
from telepot.namedtuple import ForceReply
from telepot.aio.delegate import per_chat_id, create_open, pave_event_space

# Open the json file with the api key, regardless of where the script is ran from.
with open(sys.path[0] + '/keys.json', 'r') as f:
    key = json.load(f)

# Main bot object.
class Stickers(telepot.aio.helper.ChatHandler):

    # Most of the messages are stored in variables so checking replies is easy, might as well do it here right?
    def __init__(self, *args, **kwargs):
        super(Stickers, self).__init__(*args, **kwargs)
        self.askname = 'What do you want to name the pack? This will be the url of the pack, for example in\nhttps://t.me/addstickers/animals\n\'animals\' would be the pack name.'
        self.retryname = 'Sorry, that name isnt valid, please try another.'
        self.asktitle = 'Great, now what do you want the title to be? The title is displayed at the top of the pack, using the same pack as earlier for an example, \'Just zoo it! (@TrendingStickers)\' would be the title of that pack.'
        self.retrytitle = 'Sorry this title is too long, keep it less than 64 characters.'
        self.donemsg = 'You\'re ready to go! Start sending images and I will add them to the pack, then send /done when you\'re done, or reply to this message to set the emoji to be associated with the stickers.'
        self.stickeremoji = '😶'
        self.askedit = 'What is the name of the sticker pack you want to edit? Please note, I can only edit packs I have created.'
        self.askreply = 'Please reply directly to the message you are responding to.'

    # open() is for the first message the bot receieves of the delegattion, I don't have any need to have a starting message every time so we just pass it to on_chat_message() like every other message.
    async def open(self, initial_msg, seed):
        await self.on_chat_message(initial_msg)
        self.from_id = initial_msg['from']['id']
        return True

    # Handles all incoming messages to the bot.
    async def on_chat_message(self, msg):
        content_type, chat_type, chat_id, msg_date, msg_id = telepot.glance(msg, long=True)
        # Make sure the user is private messaging us.
        if chat_type == 'private':
            # All the commands will be text, lets just make sure anyway.
            if content_type == 'text':
                command = msg['text'].lower()
                if command.startswith('/create'):
                    await self.sender.sendChatAction('typing')
                    await self.startstickers(msg)
                elif command.startswith('/done'):
                    try:
                        if self.packmade:
                            await self.sender.sendMessage('All done! The sticker pack has been made and the stickers have been added, you can now manage it in the official stickers bot or access it right now with https://t.me/addstickers/' + self.packname)
                            self.close()
                    except AttributeError:
                        return
                elif command.startswith('/edit'):
                    #print(await bot.getStickerSet('rakutest3_by_batchstickerbot'))
                    await self.sender.sendMessage(self.askedit, reply_markup=ForceReply())
                # Check if the user is replying to one of the bots messages and whicih one it is.
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
                        elif reply_text == self.askedit:
                            await self.checkownership(msg)
                    except KeyError:
                        await self.sender.sendMessage(self.askreply);
                        return
            # Stickers are added as documents.
            elif content_type == 'document':
                await self.uploader(msg)
            # We don't want them sent as photos
            elif content_type == 'photo':
                try:
                    if (self.packname and self.packtitle) or self.editing:
                        await self.sender.sendMessage('Please send the image as a file(uncompressed).', reply_to_message_id=msg_id)
                except AttributeError:
                    pass
        return

    # Initial function for making the pack, don't know why I put it in it's own function.
    async def startstickers(self, msg):
        await self.sender.sendMessage(self.askname, reply_markup=ForceReply())
        self.packmade = False
        return

    # Function to check if the name picked by the user is valid, then stores in the packname variable and continues to picking the title.
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

    # Same deal as namehandler(), checks if the title is valid and stores it.
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

    # Function to upload to stickers to the pack.
    async def uploader(self, msg):
        content_type, chat_type, chat_id, msg_date, msg_id = telepot.glance(msg, long=True)
        try:
            if (self.packname and self.packtitle) or self.editing:
                if msg['document']['mime_type'] == 'image/png':
                    try:
                        # You have to initialize the pack by creating it with a sticker, and we only do this once, afterwards self.packmade is set to true.
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
    async def checkownership(self, msg):
        packname = msg['text']
        try:
            await self.sender.sendChatAction('typing')
            await bot.addStickerToSet(self.from_id, packname, 'BQADBAADiQIAAlrMkFAokegTxHmJZAI', self.stickeremoji)
            await asyncio.sleep(10.0)
            setobj = await bot.getStickerSet(packname)
            testid = setobj['stickers'][-1]['file_id']
            await bot.deleteStickerFromSet(testid)
            self.packname = packname
            self.packtitle = False
            self.packmade = True
            self.editing = True
            await self.sender.sendMessage(self.donemsg)
        except telepot.exception.TelegramError as e:
            await self.sender.sendMessage('Sorry you dont appear to be the owner of this pack or it doesnt exist.')
            print(e)


bot = telepot.aio.DelegatorBot(key['telegram'], [
    pave_event_space()(
        per_chat_id(), create_open, Stickers, timeout=70*1300),
])
loop = asyncio.get_event_loop()
loop.create_task(MessageLoop(bot).run_forever())
print('Started...')
loop.run_forever()
