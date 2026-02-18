# 📦 Telegram Meme Archive Bot

A Telegram inline bot for storing, organizing, and retrieving memes (or any media documents) using fuzzy search.

This bot uses **Telethon**, **SQLite**, and **thefuzz** to create a searchable meme archive system with admin approval support.

---

## 🚀 Features

### 🔎 Fuzzy Search
Uses `thefuzz` (`token_sort_ratio`) to intelligently match user queries with stored meme titles.

### 🗂 SQLite Database
Stores meme titles and their types in a lightweight local database.

### 📎 Inline Mode Support
Returns matched memes as inline query results inside Telegram.

### 📤 Instant Delivery
When a meme is selected, it is sent directly into the chat with an empty caption.

### 🛠 Admin Approval System
Users can submit memes.
Admins can approve or reject submissions before they are added to the archive.

### 📁 Multi-Purpose Design
Although designed for memes, this bot can also function as:
- Media archive system
- Document storage bot
- Voice/video organizer
- Internal content library

---

## 🧠 How It Works

1. A user sends an inline query.
2. The bot compares the query against stored titles using fuzzy matching.
3. Matching titles are mapped to their database IDs.
4. The bot fetches the corresponding Telegram documents.
5. Results are displayed as inline options.
6. When selected, the file is sent to the chat.

---

## 🏗 Tech Stack

- Python
- Telethon
- SQLite3
- thefuzz

---

## ⚠️ Known Limitations

This project is functional but not fully optimized.

But I am looking forward to improve it.

Contributions are welcome.

---

## 🤝 Contributing

If you'd like to improve performance, refactor the code, or add features:

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

All constructive contributions are appreciated.

---

## 📜 License

This project is licensed under the MIT License.
See the LICENSE file for details.
