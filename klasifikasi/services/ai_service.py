
import os
from groq import Groq


def tanya_ai(pertanyaan):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "API Key Groq belum dikonfigurasi."

    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Kamu adalah Asisten AI KaloriMakanan. "
                        "Tugasmu membantu pengguna memahami kalori, "
                        "kandungan nutrisi, dan pola makan sehat. "
                        "Gunakan bahasa Indonesia yang sederhana, "
                        "ramah, dan mudah dipahami. "
                        "Berikan informasi umum, bukan diagnosis medis."
                    )
                },
                {
                    "role": "user",
                    "content": pertanyaan
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content

    except Exception as e:
        print("ERROR GROQ:", repr(e))
        return "Terjadi kendala saat menghubungkan ke Groq."
