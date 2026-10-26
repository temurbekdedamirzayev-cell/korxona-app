# AI Telegram bot (bepul)

Bot uchta bepul AI xizmatidan navbat bilan foydalanadi: **Gemini → Groq → OpenRouter**.
Biri limitga yetsa yoki ishlamasa, avtomatik keyingisiga o'tadi. Limiti tugagan xizmat
`COOLDOWN_SECONDS` (standart 60 soniya) davomida chetlab o'tiladi.

## Kalitlarni olish
- **Telegram:** @BotFather → `/newbot`
- **Gemini:** https://aistudio.google.com → Get API key
- **Groq:** https://console.groq.com → API Keys
- **OpenRouter:** https://openrouter.ai → Keys

Kamida bitta AI kaliti kerak, lekin uchalasini qo'ysangiz bot ishonchliroq ishlaydi.

## Ishga tushirish
```bash
pip install -r requirements.txt
cp .env.example .env     # keyin .env ichiga kalitlarni yozing
python bot.py
```

## Buyruqlar
- `/start` — salomlashish
- `/new` — suhbat tarixini tozalash

`.env` faylini hech qachon GitHub'ga yuklamang (u `.gitignore` da).
