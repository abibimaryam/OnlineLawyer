import subprocess
import sys
import asyncio
import aiosqlite
from telegram import Bot


import os
from dotenv import load_dotenv


load_dotenv()

BOT1_TOKEN = os.getenv('USER_BOT_TOKEN')

async def send_pending_answers():
    bot = Bot(BOT1_TOKEN)
    print("✅ Запущена проверка новых ответов...")
    while True:
        try:
            async with aiosqlite.connect("telegram_data_base.db") as db:
                cursor = await db.execute("""
                    SELECT id, user_id, question_id, question_text 
                    FROM answers 
                    WHERE valuation_service = 0
                """)
                rows = await cursor.fetchall()

                for row in rows:
                    answer_id, user_id, question_id, answer_text = row
                    try:
                        await bot.send_message(
                            chat_id=user_id,
                            text=f"⚖️ Ответ от юриста на ваш вопрос #{question_id}:\n\n{answer_text}"
                        )
                        await db.execute(
                            "UPDATE answers SET valuation_service = 1 WHERE id = ?", (answer_id,)
                        )
                        await db.commit()
                        print(f"📨 Ответ #{answer_id} отправлен пользователю {user_id}")
                    except Exception as e:
                        print(f"[ОШИБКА] Не удалось отправить сообщение пользователю {user_id}: {e}")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось проверить ответы: {e}")

        await asyncio.sleep(5)

async def main():
   
    subprocess.Popen([sys.executable, 'manage.py', 'runserver'])

    
    from telegram_bot.bot import run_bot

   
    await asyncio.gather(
        send_pending_answers(),
        run_bot()
    )

if __name__ == '__main__':
    asyncio.run(main())
