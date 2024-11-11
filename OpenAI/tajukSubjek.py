import json
import sys
import os
from fuzzywuzzy import fuzz

# # Menambahkan path ke direktori proyek
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))


import openai


openai.api_key = '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'

def is_synopsis_match(synopsis, narasi_klasifikasi, subject):
    if narasi_klasifikasi:     
        match_ratio = fuzz.token_set_ratio(synopsis.lower(), narasi_klasifikasi.lower())
    else:
        match_ratio = 0
    
    if subject:
        match_ratio_subject = fuzz.token_set_ratio(synopsis.lower(), subject.lower())
    else:
        match_ratio_subject = 0
    
    return match_ratio_subject >= 80 or  match_ratio >= 80 

# Cek apakah file cache ada
cache_file = './Damy/cache.json'
if os.path.exists(cache_file):
    with open(cache_file, 'r') as file:
        cache = json.load(file)
else:
    cache = {}

def generate_keywords_openai(synopsis):
    from app import app, KlasifikasiBuku
    # Memastikan bahwa konteks aplikasi ada saat mengakses database
    with app.app_context():
        # Mengambil semua data klasifikasi buku
        klasifikasi_buku = KlasifikasiBuku.query.all()
        
        # List untuk menyimpan hasil kecocokan
        matches = []
        
         # Jika tidak ada di cache, lakukan permintaan API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Generate keywords  maximum two sentences for the following book synopsis:\n\n{synopsis}\n\nKeywords use B.Indonesia and make split with comma:"},
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
        # print(keywords)
        # Pencocokan synopsis dengan setiap narasi klasifikasi
        for klasifikasi in klasifikasi_buku:
            # print(klasifikasi.subject)
            if is_synopsis_match(keywords, klasifikasi.narasi_klasifikasi, klasifikasi.subject):
                matches.append({
                    'deweyNoClass': klasifikasi.deweyNoClass,
                    'narasiKlasifikasi': klasifikasi.narasi_klasifikasi,
                    'subject': klasifikasi.subject
                })
        
        # Jika ada kecocokan, return nilai deweyNoClass dan subject pertama
        if matches:
            return {
                'keywords': keywords,
                'deweyNoClass': matches[0]['deweyNoClass'],
                'subject': matches[0]['subject'],
                'source': 'from database'
            }
        else:
            return "keywords tidak ada di database"

# # Contoh penggunaan
# if __name__ == '__main__':
#     synopsis = "Uang memang bukan segalanya, tetapi segalanya butuh uang. Sehingga, tak heran jika banyak orang ingin menjadi kaya dan mapan. Namun, apabila saat ini Anda belum memiliki apa-apa, menjadi kaya terasa seperti mimpi belaka. Jangan putus asa! Ada banyak cara kreatif yang dapat menjadi mesin penghasil uang dan bisa Anda lakukan di rumah saja. Di buku ini, ada lebih dari 30 macam pekerjaan untuk menghasilkan uang, mulai dari mnembuka toko online, budi daya ikan hias, menjadi penulis, membuka jasa kursus, hingga trading saham dan valuta asing. Tak perlu bekerja di kantor, karena semua dapat Anda kerjakan di rumah saja. Anda bisa memilih salah satunya sesuai minat dan keahlian."
#     keyword_openai = generate_keywords_openai(synopsis)
#     print(keyword_openai)
