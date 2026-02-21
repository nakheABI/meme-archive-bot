from pathlib import Path
from telethon import events, TelegramClient, types, functions
import asyncio
import sqlite3
import random
from telethon.extensions import markdown
from telethon.tl.functions.messages import SendMessageRequest
from telethon.tl.types import InputBotInlineResultDocument, InputWebDocument, InputBotInlineMessageText, \
    InputBotInlineResult, InputBotInlineMessageMediaAuto, KeyboardButtonStyle, UpdateBotInlineSend
from telethon.utils import get_input_document
from telethon.tl.types import DocumentAttributeVideo, DocumentAttributeAudio


DB_PATH = Path(__file__).parent / "aaaaa.db"

# This class prepares a custom Markdown for the client
class CustomMarkdown:
    @staticmethod
    def parse(text):
        text, entities = markdown.parse(text)
        for i, e in enumerate(entities):
            if isinstance(e, types.MessageEntityTextUrl):
                if e.url == 'spoiler':
                    entities[i] = types.MessageEntitySpoiler(e.offset, e.length)
                elif e.url.startswith('emoji/'):
                    entities[i] = types.MessageEntityCustomEmoji(e.offset, e.length, int(e.url.split('/')[1]))
        return text, entities

    @staticmethod
    def unparse(text, entities):
        for i, e in enumerate(entities or []):
            if isinstance(e, types.MessageEntityCustomEmoji):
                entities[i] = types.MessageEntityTextUrl(e.offset, e.length, f'emoji/{e.document_id}')
            if isinstance(e, types.MessageEntitySpoiler):
                entities[i] = types.MessageEntityTextUrl(e.offset, e.length, 'spoiler')
        return markdown.unparse(text, entities)


client = TelegramClient("Bottttttttttt", api_id=1234567890, api_hash="your api hash")
client.parse_mode = CustomMarkdown()

from thefuzz import fuzz

no_auth_users = [] # These users can add memes without admin permission.
user_status = {} # This just saves user status with information about their meme and nothing more.

# In the two following functions we start the database and create its tables.
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS memes
                 (
                     ID
                     INTEGER
                     NOT
                     NULL
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     Title
                     TEXT
                     NOT
                     NULL,
                     typeof
                     TEXT
                     NOT
                     NULL
                 )
                 ''')
    conn.execute("""CREATE TABLE IF NOT EXISTS recents (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    meme_id INTEGER NOT NULL,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    """)
    cursor = conn.cursor()
    cursor.execute("SELECT ID FROM memes WHERE ID = 1")
    exists = cursor.fetchone()
    if not exists:
        conn.execute(
            "INSERT INTO memes (ID, Title, typeof) VALUES (?, ?, ?)",
            (1, "dummydkedkcjnjdokjdkdodjfkfnvkfedlpdkjfodelpj", "video")
        )
        conn.execute("UPDATE sqlite_sequence SET seq = 1 WHERE name = 'memes'")
    conn.commit()
    conn.close()

# DB function for adding meme.
async def add_meme(title, typeof):
    conn = get_connection()
    conn.execute(
        'INSERT INTO memes (Title, typeof) VALUES (?, ?)',
        (title, typeof)
    )
    conn.commit()
    conn.close()

# DB function for deleting memes.
async def delete_meme(ID):
    conn = get_connection()
    conn.execute('''DELETE FROM memes WHERE ID = ?''', (ID,))
    conn.commit()
    conn.close()

# DB function for getting all the titles.
async def get_all_title():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM memes''', )
    rows = cursor.fetchall()
    conn.close()
    return [row[1] for row in rows]

# DB function to get the ID by title.
async def get_id_by_title(title, typeof):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT ID FROM memes WHERE Title = ? AND typeof = ?''',
        (title, typeof)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

# DB function ro get the type of the meme.
async def get_type_of_meme(ID):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM memes WHERE ID = ?''', (ID,))
    row = cursor.fetchone()
    conn.close()
    return row[2]

# DB function to get the title of the meme.
async def get_title_of_meme(ID):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM memes WHERE ID = ?''', (ID,))
    row = cursor.fetchone()
    conn.close()
    return row[1]
# DB function to get type of the meme by its title.
async def get_type_by_title(title):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM memes WHERE Title = ?''', (title,))
    rows = cursor.fetchall()
    conn.close()
    return [row[2] for row in rows]
# here we update the recents table evry time a user chooses a result.
async def update_recents(user_id, meme_id):
    conn = get_connection()
    conn.execute("""INSERT INTO recents (user_id, meme_id) VALUES (?, ?)""", (user_id, meme_id))
    conn.commit()
    conn.close()

# DB function to get the memes that the user recently used.
async def get_recent_memes(user_id, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT meme_id
                   FROM recents
                   WHERE user_id = ?
                   GROUP BY meme_id
                   ORDER BY MAX(used_at) DESC LIMIT ?
                   """, (user_id, limit))
    rows = cursor.fetchall()
    if rows:
        return [row["meme_id"] for row in rows]
    return None

# The add command
@client.on(events.NewMessage(pattern="/add"))
async def add_handle(event):
    global user_status
    if user_status.get(event.sender_id): # If user already has an open request.
        await client.send_message(event.chat.id, "در حال حاضر یک درخواست فعال داری [❌](emoji/6298671811345254603)")
        return
    await client.send_message(event.chat.id, "لطفاً میم رو بدون کپشن ارسال کن [✔️](emoji/6296367896398399651)")
    user_status[event.sender_id] = {"step": "sending meme", "file_path": None, "typeof": None, "title": None} #  here we store the user info in the dict

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    global user_status
    global no_auth_users
    st = user_status.get(event.sender_id)
    if not st:
        return
    # Checking the meme type.
    if st["step"] == "sending meme" and event.message.document:
        st["file_path"] = await client.download_media(event.message)
        st["step"] = "sending text"
        if event.message.media.video:
            st["typeof"] = "video"
        elif event.message.media.voice:
            st["typeof"] = "voice"
        else:
            await client.send_message(event.chat.id, "نوع فایل پشتیبانی نمی‌شود [❌](emoji/6298671811345254603)")
            del user_status[event.sender_id]
            return
        await client.send_message(event.chat.id, "حالا اسم میم رو ارسال کن [✔️](emoji/6296367896398399651)")
    elif st["step"] == "sending text" and event.message.text:
        if event.sender_id in no_auth_users:
            channel = await client.get_input_entity("YOUR-ARCHIVE-CHANNEL")
            await client.send_file(channel, st["file_path"])
            title = event.message.raw_text
            await add_meme(title, st["typeof"])
            del user_status[event.sender_id]
            await client.send_message(event.chat.id, "میم با موفقیت اضافه شد [✅](emoji/6296367896398399651)")
        else:
            st["title"] = event.message.raw_text
            # Here we are creating some colored buttons with style and custom emoji.
            # This won't work if you don't have the latest version of telethon installed.
            # you can remove the icon argument if you don't have an account that has a premium subscription.
            success_button = KeyboardButtonStyle(bg_success=True, icon=6296367896398399651)
            danger_btn = KeyboardButtonStyle(bg_danger=True, icon=6298671811345254603)
            button = types.KeyboardButtonCallback(
                text="تأیید",
                data=f"accept_{event.sender_id}".encode(),
                style=success_button
            )
            btn = types.KeyboardButtonCallback(
                text="رد",
                data=f"reject_{event.sender_id}".encode(),
                style=danger_btn
            )
            markups = types.ReplyInlineMarkup(
                rows=[types.KeyboardButtonRow(buttons=[button]), types.KeyboardButtonRow(buttons=[btn])]
            )
            admin_entity = await client.get_input_entity(7954947981)
            await client.send_file(admin_entity, st["file_path"])
            await client(SendMessageRequest(admin_entity, message=f"یک درخواست جدید برای افزودن میم ثبت شده است.     {st["title"]}", reply_markup=markups))
            await client.send_message(event.chat.id, "درخواستت برای بررسی ارسال شد [✅](emoji/6296367896398399651)")
            st["step"] = "pending"


@client.on(events.InlineQuery())
async def handle_inline(event):
    text = event.text
    channel = await client.get_input_entity("YOUR-ARCHIVE-CHANNEL")
    titles = await get_all_title()
    matched_titles = {}
    matched_ids = []
    meme_to_show = []
    # This is related to user recents so the program shows the latest used memes.
    # Good news it now does what it is supposed to do structurally.
    # It is a possible Telegram bug but at least its fixed now.
    if text == "":
        recents = await get_recent_memes(event.sender_id)
        if recents:
            for recent in recents:
                matched_ids.append(recent)
            memes = await client.get_messages(channel, ids=matched_ids)
            for meme in memes:
                meme_title  = await get_title_of_meme(meme.id)
                meme_type = await get_type_of_meme(meme.id)
                meme_to_show.append(InputBotInlineResultDocument(id=str(random.randint(1, 9999999)), type=meme_type, title=str(meme_title), document=get_input_document(meme.document), send_message=InputBotInlineMessageMediaAuto(message="")))
    else:
        for title in titles:
            score = fuzz.token_sort_ratio(event.text, title)
            if score >= 50:
                matched_titles[title] = score
        sorted_titles = sorted(matched_titles.keys(), key=lambda k: matched_titles[k], reverse=True)
        for title in sorted_titles:
            the_type = await get_type_by_title(title)
            for t in the_type:
                ids = await get_id_by_title(title, t)
                matched_ids.append(ids)
        memes = await client.get_messages(channel, ids=list(matched_ids))
        for meme in memes:
            if not meme:
                continue
            meme_type = await get_type_of_meme(meme.id)
            meme_title = await get_title_of_meme(meme.id)
            meme_to_show.append(InputBotInlineResultDocument(id=str(meme.id), type=str(meme_type), title=str(meme_title), document=get_input_document(meme.document), send_message=InputBotInlineMessageMediaAuto(message="")))
    await event.answer(meme_to_show)


@client.on(events.CallbackQuery())
async def handle_callback_query(event):
    # This is just for the admin accept/reject flow.
    data = event.data.decode()
    if data.startswith("accept_"):
        user_id = int(data.split("_", 1)[1])
        st = user_status.get(user_id)
        if not st:
            return
        channel = await client.get_input_entity("YOUR-ARCHIVE-CHANNEL")
        await client.send_file(channel, st["file_path"])
        title = st["title"]
        await add_meme(title, st["typeof"])
        del user_status[user_id]
        await client.send_message(user_id, "میم شما تأیید و اضافه شد [✅](emoji/6296367896398399651)")
    elif data.startswith("reject_"):
        user_id = int(data.split("_", 1)[1])
        st = user_status.get(user_id)
        if not st:
            return
        del user_status[user_id]
        await client.send_message(user_id, "درخواست شما رد شد [❌](emoji/6298671811345254603)")
# With this we can find what result the user chose.
# make sure to enable inline feedback in bot father and do not forget to set it to 100%.
@client.on(events.Raw())
async def handle_choice(update):
    if isinstance(update, UpdateBotInlineSend):
        user_id = update.user_id
        meme_id = update.id
        await update_recents(user_id, meme_id)
        print("done")


async def main():
    init_db()
    await client.start(bot_token="your token")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
