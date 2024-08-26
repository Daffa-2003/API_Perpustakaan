import openai
import json
import os

openai.api_key = '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'

# Cek apakah file cache ada
cache_file = './Damy/cache_abstract.json'
if os.path.exists(cache_file):
    with open(cache_file, 'r') as file:
        cache = json.load(file)
else:
    cache = {}

def generate_abstract_openai(synopsis):
    # Cek apakah hasilnya sudah ada di cache
    if synopsis in cache:
        return cache[synopsis]
    
    # Jika tidak ada di cache, lakukan permintaan API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            # {"role": "user", "content": f"Generate keywords for the following book synopsis:\n\n{synopsis}\n\nKeywords use B.Indonesia:"},
            {"role": "user", "content": f"Generate abstract for the following book synopsis:\n\n{synopsis}\n\nabstract use B.Indonesia:"}
        ]
    )
    abstract = response['choices'][0]['message']['content'].strip()
    cache[synopsis] = abstract
    with open(cache_file, 'w') as file:
        json.dump(cache, file)
    
    return abstract

# # Contoh penggunaan
# synopsis = "Novel Laskar Pelangi mengisahkan tentang kehidupan dari 10 anak hebat yang mempunyai semangat juang yang tinggi untuk tetap melanjutkan sekolah di kampung Gantung, Kepulauan Bangka Belitung. Kesepuluh anak tersebut dinamai Laskar Pelangi, yang terdiri dari Ikal, Lintang, Mahar Ahlan, Sahara Aulia Fadillah, Syahdan Noor Aziz, Samson atau Borek, Muhammad Jundullah Gufron Nur Zaman atau A kiong, Harun Ardhili Ramadhan, Trapani Ihsan Jamari, dan Mukharam Kudai Khairani. Kesepuluh anak ini bersekolah di sebuah sekolah yang bernama SD Muhammadiyah Gantung, yang dibimbing oleh Bu Muslimah dan Pak Harfan. Selama mereka sekolah, mereka juga mendapatkan seorang teman baru, pindahan dari SD PN Timah yang bernama Flo. Sebagian besar dari kesepuluh anak yang bersekolah di SD Muhammadiyah Gantung ada anak-anak dari para penambang timah di pulau dengan perolehan kekayaan alam timah yang terbesar di dunia. Namun, hal itu berbanding terbalik dengan taraf kesejahteraan hidup masyarakat aslinya. Cerita ini dimulai dari penerimaan siswa baru di SD Muhammadiyah Gantung, di mana hanya terdapat 9 orang yang mendaftar untuk sekolah.Hal ini yang membuat Bu Muslimah dan Pak Harfan"
# keyword_openai = generate_abstract_openai(synopsis)
# print(keyword_openai)
