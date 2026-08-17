"""Translations for DB-driven content (achievement names/descriptions, point
history reasons, etc.) that can't be extracted by pybabel from templates.

Add a key for each language code in LANGUAGES (web/app.py).
"""

# Each entry: (name_en, description_en) -> (name_<lang>, description_<lang>)
ACHIEVEMENT_TRANSLATIONS_ID = {
    ("Welcome!", "Create your first account"): (
        "Selamat Datang!",
        "Buat akun pertama Anda",
    ),
    ("First Steps", "Generate your first prompt"): (
        "Langkah Pertama",
        "Buat prompt pertama Anda",
    ),
    ("Collector", "Save your first prompt"): (
        "Kolektor",
        "Simpan prompt pertama Anda",
    ),
    ("Community Member", "Share your first prompt"): (
        "Anggota Komunitas",
        "Bagikan prompt pertama Anda",
    ),
    ("Getting Started", "Generate 10 prompts"): (
        "Mulai Bergerak",
        "Buat 10 prompt",
    ),
    ("Dedicated", "Generate 50 prompts"): (
        "Berdedikasi",
        "Buat 50 prompt",
    ),
    ("Prompt Master", "Generate 100 prompts"): (
        "Master Prompt",
        "Buat 100 prompt",
    ),
    ("Legendary Creator", "Generate 500 prompts"): (
        "Pembuat Legendaris",
        "Buat 500 prompt",
    ),
    ("Archivist", "Save 10 prompts"): (
        "Arsiparis",
        "Simpan 10 prompt",
    ),
    ("Librarian", "Save 50 prompts"): (
        "Pustakawan",
        "Simpan 50 prompt",
    ),
    ("Master Archivist", "Save 100 prompts"): (
        "Arsiparis Master",
        "Simpan 100 prompt",
    ),
    ("Contributor", "Share 5 prompts"): (
        "Kontributor",
        "Bagikan 5 prompt",
    ),
    ("Community Leader", "Share 25 prompts"): (
        "Pemimpin Komunitas",
        "Bagikan 25 prompt",
    ),
    ("Legendary Contributor", "Share 50 prompts"): (
        "Kontributor Legendaris",
        "Bagikan 50 prompt",
    ),
    ("Explorer", "Try all prompt types"): (
        "Penjelajah",
        "Coba semua jenis prompt",
    ),
    ("Profile Complete", "Complete your profile"): (
        "Profil Lengkap",
        "Lengkapi profil Anda",
    ),
    ("Daily Visitor", "Login for 7 consecutive days"): (
        "Pengunjung Harian",
        "Masuk selama 7 hari berturut-turut",
    ),
    ("Weekly Warrior", "Login for 30 consecutive days"): (
        "Pejuang Mingguan",
        "Masuk selama 30 hari berturut-turut",
    ),
    ("Monthly Master", "Login for 100 consecutive days"): (
        "Master Bulanan",
        "Masuk selama 100 hari berturut-turut",
    ),
    ("Feedback Guru", "Give feedback on 5 prompts"): (
        "Guru Masukan",
        "Beri masukan pada 5 prompt",
    ),
    ("Quality Contributor", "Receive 10 positive ratings"): (
        "Kontributor Berkualitas",
        "Terima 10 penilaian positif",
    ),
    ("Critic", "Give detailed feedback on 25 prompts"): (
        "Kritikus",
        "Beri masukan rinci pada 25 prompt",
    ),
    ("Quality Master", "Receive 50 positive ratings"): (
        "Master Berkualitas",
        "Terima 50 penilaian positif",
    ),
    ("Style Explorer", "Try 5 different prompt styles"): (
        "Penjelajah Gaya",
        "Coba 5 gaya prompt berbeda",
    ),
    ("Technique Master", "Use 10 different prompt techniques"): (
        "Master Teknik",
        "Gunakan 10 teknik prompt berbeda",
    ),
    ("Category Collector", "Create prompts in 8 different categories"): (
        "Kolektor Kategori",
        "Buat prompt dalam 8 kategori berbeda",
    ),
    ("Format Specialist", "Use 6 different prompt formats"): (
        "Spesialis Format",
        "Gunakan 6 format prompt berbeda",
    ),
    ("Version Controller", "Create 10 different versions of a prompt"): (
        "Pengontrol Versi",
        "Buat 10 versi berbeda dari sebuah prompt",
    ),
    ("Template Creator", "Create 5 custom prompt templates"): (
        "Pembuat Templat",
        "Buat 5 templat prompt khusus",
    ),
    ("Batch Processor", "Generate prompts in batch mode"): (
        "Pemroses Massal",
        "Buat prompt dalam mode massal",
    ),
    ("Parameter Expert", "Use advanced parameters 25 times"): (
        "Pakar Parameter",
        "Gunakan parameter lanjutan 25 kali",
    ),
    ("Helpful Member", "Help 5 other users"): (
        "Anggota yang Membantu",
        "Bantu 5 pengguna lain",
    ),
    ("Mentor", "Provide guidance to 15 users"): (
        "Mentor",
        "Berikan bimbingan kepada 15 pengguna",
    ),
    ("Community Helper", "Participate in community discussions"): (
        "Penolong Komunitas",
        "Berpartisipasi dalam diskusi komunitas",
    ),
    ("Collaborator", "Work on shared projects with others"): (
        "Kolaborator",
        "Bekerja pada proyek bersama dengan orang lain",
    ),
    ("Steady Progress", "Login for 50 days total"): (
        "Kemajuan Stabil",
        "Masuk selama 50 hari total",
    ),
    ("Reliable User", "Login for 100 days total"): (
        "Pengguna Andal",
        "Masuk selama 100 hari total",
    ),
    ("Dedicated Member", "Maintain a 30-day login streak"): (
        "Anggota Berdedikasi",
        "Pertahankan 30 hari masuk berturut-turut",
    ),
    ("Loyal User", "Login for 200 days total"): (
        "Pengguna Setia",
        "Masuk selama 200 hari total",
    ),
    ("Feature Explorer", "Try all main features"): (
        "Penjelajah Fitur",
        "Coba semua fitur utama",
    ),
    ("Settings Expert", "Customize all profile settings"): (
        "Pakar Pengaturan",
        "Sesuaikan semua pengaturan profil",
    ),
    ("Tool Master", "Use all available tools"): (
        "Master Alat",
        "Gunakan semua alat yang tersedia",
    ),
    ("Discovery Seeker", "Find and use hidden features"): (
        "Pencari Penemuan",
        "Temukan dan gunakan fitur tersembunyi",
    ),
    ("Power User", "Generate 1000 prompts"): (
        "Pengguna Ahli",
        "Buat 1000 prompt",
    ),
    ("Library Master", "Save 250 prompts"): (
        "Master Pustaka",
        "Simpan 250 prompt",
    ),
    ("Community Legend", "Share 100 prompts"): (
        "Legenda Komunitas",
        "Bagikan 100 prompt",
    ),
    ("Year Round User", "Login for 365 consecutive days"): (
        "Pengguna Setahun",
        "Masuk selama 365 hari berturut-turut",
    ),
    ("Perfectionist", "Create 50 prompt versions"): (
        "Perfeksionis",
        "Buat 50 versi prompt",
    ),
    ("Innovation Leader", "Create 20 custom templates"): (
        "Pemimpin Inovasi",
        "Buat 20 templat khusus",
    ),
    ("Community Champion", "Help 50 other users"): (
        "Juara Komunitas",
        "Bantu 50 pengguna lain",
    ),
    ("Feature Pioneer", "Try 20 different features"): (
        "Perintis Fitur",
        "Coba 20 fitur berbeda",
    ),
    ("Early Adopter", "Be among the first 100 users"): (
        "Pengguna Awal",
        "Jadi salah satu dari 100 pengguna pertama",
    ),
    ("Reverse Engineer", "Use reverse image prompts"): (
        "Rekayasa Balik",
        "Gunakan prompt gambar terbalik",
    ),
    ("Advanced User", "Use advanced prompts"): (
        "Pengguna Lanjutan",
        "Gunakan prompt lanjutan",
    ),
    ("API Key Provider", "Add and validate your own Gemini API key"): (
        "Penyedia Kunci API",
        "Tambah dan validasi kunci API Gemini Anda sendiri",
    ),
}


_LANG_DICTS = {
    "id": ACHIEVEMENT_TRANSLATIONS_ID,
}


def translate_achievement(name_en: str, description_en: str, language: str) -> tuple[str, str]:
    """Return (name, description) translated for the given language.
    Falls back to the English strings if no translation is registered.
    """
    if not language or language == "en":
        return name_en, description_en
    table = _LANG_DICTS.get(language)
    if not table:
        return name_en, description_en
    pair = table.get((name_en, description_en))
    if not pair:
        return name_en, description_en
    return pair


def translate_achievement_row(row: tuple, language: str) -> tuple:
    """Translate a (id, name, desc, icon, points, category, unlocked_at) row."""
    ach_id, name, desc, icon, points, category, unlocked_at = row
    new_name, new_desc = translate_achievement(name, desc, language)
    return (ach_id, new_name, new_desc, icon, points, category, unlocked_at)
