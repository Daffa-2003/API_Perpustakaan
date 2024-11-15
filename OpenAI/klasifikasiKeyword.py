import openai
import json
import os

openai.api_key = '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'

# Cek apakah file cache ada
cache_file = '../Damy/cache.json'
if os.path.exists(cache_file):
    with open(cache_file, 'r') as file:
        cache = json.load(file)
else:
    cache = {}

def generate_keywords_openai(synopsis):
    # Cek apakah hasilnya sudah ada di cache
    if synopsis in cache:
        return cache[synopsis]
    
    # Jika tidak ada di cache, lakukan permintaan API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Generate a Dewey Decimal classification and subject for the following synopsis:\n\n{synopsis}\n\nUse B. Indonesia for subject:"},
            # {"role": "user", "content": f"Buatkan abstract dari sinopsis buku berikut:\n\n{synopsis}\n\nabstract menggunakan B.Indonesia:"}
        ]
    )
    
    keywords_text = response['choices'][0]['message']['content'].strip()
    try:
        keywords_list = [keyword.strip() for keyword in keywords_text.split(',')]
        keywords = ', '.join(keywords_list)
    except Exception as e:
        print(f"Error: {e}")
        keywords = "error"
        
    # Simpan hasilnya di cache
    cache[synopsis] = keywords
    with open(cache_file, 'w') as file:
        json.dump(cache, file)
    
    return keywords

# # Contoh penggunaan
# synopsis = "Surat Kecil untuk Tuhan bercerita tentang seorang gadis bernama Gita Sesa Wanda Cantika atau Keke yang merupakan pejuang kanker rhabdomyosarcoma. Ia baru berusia 13 tahun ketika mengidap penyakit tersebut.Keke lahir dikeluarga yang berada, namun tidak utuh. Orang tuanya bercerai dan ia harus hidup bersama ayah dan dua kakak laki-lakinya. Prestasi akademik maupun kehidupan sosial Keke sangat baik. Ia memiliki banyak teman dekat dan kekasih yang menyayanginya.Sayangnya, kehidupannya yang damai mendadak runtuh setelah ia didiagnosis mengidap kanker ganas bernama rhabdomyosarcoma. Penyakit yang awalnya hanya-sakit-mata itu perlahan-lahan merenggut banyak hal dari Keke, termasuk kehidupan sekolahnya yang normal dan penampilan fisiknya. Selama tiga tahun hidup dengan kanker ganas, Keke selalu dihantui dengan bayang-bayang kematian. Ia kemudian memutuskan menulis surat kecil kepada Tuhan berisi berbagai permohonan, termasuk keinginannya untuk sembuh, tumbuh dewasa, hingga agar tidak ada lagi orang yang bernasib sama dengannya."
# keyword_openai = generate_keywords_openai(synopsis)
# print(keyword_openai)
