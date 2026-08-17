#!/usr/bin/env python3
"""Rebuild web/translations/id/LC_MESSAGES/messages.po with proper Indonesian
translations for the current msgids, then compile to .mo.

PO files are line-oriented: a block has meta comments, then `msgid "..."` (with
optional continuation lines that start with `"..."`), then `msgstr "..."` (with
optional continuation lines that start with `"..."`). Blank line terminates.
"""
import re
import subprocess
from pathlib import Path

POT = Path("web/translations/messages.pot")
PO = Path("web/translations/id/LC_MESSAGES/messages.po")

# Header (indonesian language)
HEADER = """# Indonesian translations for Prompt Sanctuary.
# Copyright (C) 2026 Prompt Sanctuary
# This file is distributed under the same license as the Prompt Sanctuary project.
msgid ""
msgstr ""
"Project-Id-Version: Prompt Sanctuary 1.0\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2026-06-07 00:00+0000\\n"
"PO-Revision-Date: 2026-06-07 00:00+0000\\n"
"Last-Translator: Prompt Sanctuary <admin@promptsanctuary.com>\\n"
"Language-Team: Indonesian <LL@li.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=utf-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Language: id\\n"
"Plural-Forms: nplurals=1; plural=0;\\n"
"""

# Translation dictionary. Keys are msgids (English source strings).
# For context-disambiguation, use the same string but with a context marker (pgettext)
# — instead, we use disambiguated English source strings where conflicts exist.
TRANSLATIONS = {
    # ===== Brand + nav =====
    "Prompt Sanctuary": "Prompt Sanctuary",
    "Sanctuary": "Sanctuary",
    "Workspace": "Ruang Kerja",
    "Library": "Pustaka",
    "Account": "Akun",
    "Overview": "Ikhtisar",
    "Generate": "Buat",
    "Advanced": "Lanjutan",
    "Refinement": "Penyempurnaan",
    "My Library": "Pustaka Saya",
    "Community": "Komunitas",
    "Profile": "Profil",
    "Feedback": "Masukan",
    "Sign out": "Keluar",
    "Credits": "Kredit",
    "API status": "Status API",
    "Open menu": "Buka menu",
    "Close menu": "Tutup menu",
    "Skip to main content": "Lewati ke konten utama",
    "Primary navigation": "Navigasi utama",
    "Mobile": "Seluler",
    "Main": "Utama",
    "cr": "kr",
    # ===== Switcher + command palette =====
    "Interface language": "Bahasa antarmuka",
    "Open command palette": "Buka palet perintah",
    "Command palette": "Palet perintah",
    "Search actions, prompts, settings…": "Cari aksi, prompt, pengaturan…",
    "Search prompts…": "Cari prompt…",
    "navigate": "navigasi",
    "open": "buka",
    "close": "tutup",
    "Search": "Cari",
    "Clear": "Hapus",
    "Clear search": "Hapus pencarian",
    # ===== Common actions =====
    "Result": "Hasil",
    "Loading": "Memuat",
    "Close": "Tutup",
    "Copy": "Salin",
    "Save": "Simpan",
    "Share": "Bagikan",
    "Unshare": "Batalkan berbagi",
    "Delete": "Hapus",
    "Edit": "Sunting",
    "Refine": "Sempurnakan",
    "Preview": "Pratinjau",
    "History": "Riwayat",
    "Update": "Perbarui",
    "Open": "Buka",
    "Submit": "Kirim",
    "Cancel": "Batal",
    "Refresh": "Segarkan",
    "View": "Lihat",
    "Personal": "Pribadi",
    "Shared": "Dibagikan",
    "Yours": "Milik Anda",
    "Default": "Bawaan",
    "Add key →": "Tambah kunci →",
    "Browse →": "Jelajahi →",
    "Browse community →": "Jelajahi komunitas →",
    "Back home": "Kembali beranda",
    "Back to index": "Kembali ke beranda",
    # ===== Auth =====
    "Sign in": "Masuk",
    "Create account": "Buat akun",
    "Username": "Nama pengguna",
    "Password": "Kata sandi",
    "Email": "Surel",
    "optional": "opsional",
    "Confirm password": "Konfirmasi kata sandi",
    "Remember me": "Ingat saya",
    "Forgot password?": "Lupa kata sandi?",
    "New account": "Akun baru",
    "Three fields. Under ten seconds.": "Tiga kolom. Kurang dari sepuluh detik.",
    "Use your username and password.": "Gunakan nama pengguna dan kata sandi Anda.",
    "Welcome back.": "Selamat datang kembali.",
    "Start a new account.": "Mulai akun baru.",
    "Eighty credits to start. No card. No expiry on drafts.": "Delapan puluh kredit untuk memulai. Tanpa kartu. Tidak ada kedaluwarsa untuk draf.",
    "Pick up where you left off. Your library and refinement history are waiting.": "Lanjutkan dari terakhir kali. Pustaka dan riwayat penyempurnaan Anda menanti.",
    "I agree to the": "Saya menyetujui",
    "terms of service": "ketentuan layanan",
    "and": "dan",
    "privacy policy": "kebijakan privasi",
    "Letters, numbers, underscore. 3 to 32 characters.": "Huruf, angka, garis bawah. 3 hingga 32 karakter.",
    "Used only for security alerts. Never shared.": "Hanya untuk peringatan keamanan. Tidak pernah dibagikan.",
    "Six or more characters.": "Enam karakter atau lebih.",
    # ===== Home / overview =====
    "At a glance.": "Sekilas.",
    "Updated just now": "Baru diperbarui",
    "+ 80 on signup": "+ 80 saat daftar",
    "Saved": "Tersimpan",
    "Refinements": "Penyempurnaan",
    "prompts in your library": "prompt di pustaka Anda",
    "versioned edits": "suntingan versi",
    "with the community": "dengan komunitas",
    "Four ways to work.": "Empat cara bekerja.",
    "Generate, refine, share, and revisit — all from one place.": "Buat, sempurnakan, bagikan, dan tinjau ulang — semua dari satu tempat.",
    "Generate from a topic": "Buat dari topik",
    "Generate from a system prompt": "Buat dari prompt sistem",
    "Refine an existing prompt": "Sempurnakan prompt yang ada",
    "Browse your saved prompts": "Jelajahi prompt tersimpan",
    "Basic": "Dasar",
    "Workflow": "Alur kerja",
    "Getting started.": "Mulai dari sini.",
    "Bring your own API key": "Bawa kunci API Anda sendiri",
    "Share with the community": "Bagikan dengan komunitas",
    "Generate a prompt": "Buat prompt",
    "Advanced mode": "Mode lanjutan",
    # ===== Profile =====
    "Profile & settings.": "Profil & pengaturan.",
    "Manage your account, sessions, API key, achievements, and points.": "Kelola akun, sesi, kunci API, pencapaian, dan poin Anda.",
    "Member": "Anggota",
    "pts": "poin",
    "Click to view history": "Klik untuk melihat riwayat",
    "Total prompts": "Total prompt",
    "Achievements": "Pencapaian",
    "Active sessions": "Sesi aktif",
    "Account information": "Informasi akun",
    "Current username": "Nama pengguna saat ini",
    "New username": "Nama pengguna baru",
    "Only letters, numbers and underscores. 3–32 chars.": "Hanya huruf, angka, dan garis bawah. 3–32 karakter.",
    "Change username": "Ubah nama pengguna",
    "Update email": "Perbarui surel",
    "Danger zone": "Zona berbahaya",
    "Delete account": "Hapus akun",
    "Are you sure? This cannot be undone.": "Apakah Anda yakin? Tindakan ini tidak dapat dibatalkan.",
    "Security": "Keamanan",
    "Current password": "Kata sandi saat ini",
    "New password": "Kata sandi baru",
    "Confirm new password": "Konfirmasi kata sandi baru",
    "Update password": "Perbarui kata sandi",
    "Gemini API key": "Kunci API Gemini",
    "Use your own API key to avoid point consumption and earn 100 points.": "Gunakan kunci API Anda sendiri untuk menghindari konsumsi poin dan dapatkan 100 poin.",
    "Loading API key status…": "Memuat status kunci API…",
    "Your API key": "Kunci API Anda",
    "Enter your Gemini API key": "Masukkan kunci API Gemini Anda",
    "Validate & Save": "Validasi & Simpan",
    "Remove": "Hapus",
    "Get your API key from": "Dapatkan kunci API Anda dari",
    "Google AI Studio": "Google AI Studio",
    "Saved prompts": "Prompt tersimpan",
    "Shared prompts": "Prompt yang dibagikan",
    "No saved prompts yet": "Belum ada prompt tersimpan",
    "Start creating prompts to see them here.": "Mulai buat prompt untuk melihatnya di sini.",
    "No shared prompts yet": "Belum ada prompt yang dibagikan",
    "Share your prompts to help the community.": "Bagikan prompt Anda untuk membantu komunitas.",
    "No active sessions.": "Tidak ada sesi aktif.",
    "Unknown device": "Perangkat tidak dikenal",
    "N/A": "T/A",
    "Current": "Saat ini",
    "Revoke": "Cabut",
    "Revoked": "Dicabut",
    "Revoke this session?": "Cabut sesi ini?",
    "No achievements yet": "Belum ada pencapaian",
    "Start generating and sharing prompts to earn your first achievement.": "Mulai buat dan bagikan prompt untuk mendapatkan pencapaian pertama Anda.",
    "Point history": "Riwayat poin",
    "Loading point history…": "Memuat riwayat poin…",
    "No point history available yet.": "Belum ada riwayat poin.",
    "Points expire based on their source. Original points never expire.": "Poin kedaluwarsa berdasarkan sumbernya. Poin asli tidak pernah kedaluwarsa.",
    "Update shared": "Perbarui dibagikan",
    # ===== Feedback =====
    "Feedback log.": "Catatan masukan.",
    "Browse all feedback messages. Click an item to read the full text.": "Jelajahi semua pesan masukan. Klik item untuk membaca teks lengkap.",
    "All feedback": "Semua masukan",
    "View feedback #": "Lihat masukan #",
    "No feedback available": "Tidak ada masukan tersedia",
    "When users submit feedback, it will appear here.": "Saat pengguna mengirim masukan, itu akan muncul di sini.",
    # ===== Legal chrome =====
    "Terms of service.": "Ketentuan layanan.",
    "Privacy policy.": "Kebijakan privasi.",
    "Last updated %(date)s": "Terakhir diperbarui %(date)s",
    "%(minutes)s min read": "Membaca %(minutes)s menit",
    "Effective immediately": "Berlaku segera",
    "GDPR-aligned": "Sesuai GDPR",
    "Terms": "Ketentuan",
    "Privacy": "Privasi",
    # ===== Generator: basic =====
    "Step 02 · Topic mode": "Langkah 02 · Mode topik",
    "Generate from a topic.": "Buat dari topik.",
    "Describe what you need. The model expands it into a structured prompt with variables you can fill in later.": "Jelaskan apa yang Anda butuhkan. Model mengembangkannya menjadi prompt terstruktur dengan variabel yang bisa Anda isi nanti.",
    "Step": "Langkah",
    "Text": "Teks",
    "Image": "Gambar",
    "Generate a text prompt": "Buat prompt teks",
    'Describe what you need. Click "Generate" or "Random" for a surprise.': 'Jelaskan apa yang Anda butuhkan. Klik "Buat" atau "Acak" untuk kejutan.',
    "Toggle help": "Bantuan",
    "How this works": "Cara kerjanya",
    "Type a topic or task, hit Generate. The model crafts a structured prompt you can save, refine, or share.": "Ketik topik atau tugas, tekan Buat. Model akan membuat prompt terstruktur yang bisa Anda simpan, sempurnakan, atau bagikan.",
    "Topic or task": "Topik atau tugas",
    "Write a Python script that…": "Tulis skrip Python yang…",
    "The more specific, the better the result.": "Semakin spesifik, semakin baik hasilnya.",
    "Random": "Acak",
    "Generate an image prompt": "Buat prompt gambar",
    "Text-to-image, or reverse-engineer an image.": "Teks-ke-gambar, atau merekayasa-balik gambar.",
    "Two ways to start": "Dua cara untuk mulai",
    "Type a description for a text-to-image prompt, or upload an image to reverse-engineer it.": "Ketik deskripsi untuk prompt teks-ke-gambar, atau unggah gambar untuk merekayasa-baliknya.",
    "Input type": "Jenis input",
    "Describe a new image": "Jelaskan gambar baru",
    "File": "Berkas",
    "Reverse-engineer from an image": "Rekayasa-balik dari gambar",
    "Describe your image": "Jelaskan gambar Anda",
    "Whale on the desert": "Paus di padang pasir",
    "Click to choose an image": "Klik untuk memilih gambar",
    "Image preview": "Pratinjau gambar",
    "Generated prompt": "Prompt yang dibuat",
    "Save to library": "Simpan ke pustaka",
    "Generate again": "Buat lagi",
    # ===== Generator: advance =====
    "Advanced generator": "Pembuat lanjutan",
    "Step 03 · Pro mode": "Langkah 03 · Mode pro",
    "Generate from a system prompt.": "Buat dari prompt sistem.",
    "Configure use case, structure, safety, and style. Optional knowledge base for domain-specific prompts.": "Konfigurasikan kasus penggunaan, struktur, keamanan, dan gaya. Basis pengetahuan opsional untuk prompt spesifik domain.",
    "1.0 credit per generation": "1,0 kredit per pembuatan",
    "Image variants included": "Varian gambar disertakan",
    "Configure use case, structure, and safety in detail.": "Konfigurasikan kasus penggunaan, struktur, dan keamanan secara rinci.",
    "Use case": "Kasus penggunaan",
    "Write a README file": "Tulis berkas README",
    "Prompt type": "Jenis prompt",
    "Simple": "Sederhana",
    "Standard": "Standar",
    "Detailed": "Rinci",
    "Step by step": "Langkah demi langkah",
    "Harm content filter": "Filter konten berbahaya",
    "Unspecified": "Tidak ditentukan",
    "Block none": "Blokir tidak ada",
    "Block few": "Blokir sedikit",
    "Block some": "Blokir beberapa",
    "Block most": "Blokir sebagian besar",
    "Knowledge base": "Basis pengetahuan",
    "Enter the knowledge base if any": "Masukkan basis pengetahuan jika ada",
    "Up to 1,000 characters of context for the model.": "Hingga 1.000 karakter konteks untuk model.",
    "Pick a mode, mood, and style.": "Pilih mode, suasana hati, dan gaya.",
    "Image prompt mode": "Mode prompt gambar",
    "Generate from text": "Buat dari teks",
    "Enter your input, select the mood, and choose the primary and secondary styles.": "Masukkan input Anda, pilih suasana hati, dan pilih gaya utama dan sekunder.",
    "Reverse from image": "Balik dari gambar",
    "Upload an image and we will generate a prompt based on it, with optional mood and style.": "Unggah gambar dan kami akan membuat prompt berdasarkan itu, dengan suasana hati dan gaya opsional.",
    "Type a description": "Ketik deskripsi",
    "Upload and decode": "Unggah dan dekode",
    "Input": "Input",
    "Cat on the sky": "Kucing di langit",
    "Primary mood": "Suasana utama",
    "Primary style": "Gaya utama",
    "Secondary style": "Gaya sekunder",
    "— None —": "— Tidak ada —",
    "Positive": "Positif",
    "Negative": "Negatif",
    "Neutral": "Netral",
    "Other": "Lainnya",
    "Happy": "Bahagia",
    "Joyful": "Gembira",
    "Excited": "Bersemangat",
    "Cheerful": "Riang",
    "Content": "Puas",
    "Angry": "Marah",
    "Disgust": "Jijik",
    "Fear": "Takut",
    "Sad": "Sedih",
    "Depressed": "Murung",
    "Calm": "Tenang",
    "Relaxed": "Santai",
    "Serene": "Teduh",
    "Tranquil": "Damai",
    "Surprised": "Terkejut",
    "Curious": "Penasaran",
    "Mysterious": "Misterius",
    "Surreal": "Surealis",
    "Eerie": "Menakutkan",
    "Styles": "Gaya",
    "Techniques": "Teknik",
    "3D Model": "Model 3D",
    "Abstract": "Abstrak",
    "Analog Film": "Film Analog",
    "Anime": "Anime",
    "Cartoon": "Kartun",
    "Digital Art": "Seni Digital",
    "Fantasy Art": "Seni Fantasi",
    "Photographic": "Fotografis",
    "Pixel Art": "Seni Piksel",
    "Watercolor": "Cat Air",
    "Isometric": "Isometrik",
    "Low Poly": "Poli Rendah",
    "Cinematic": "Sinematik",
    "Cyberpunk": "Cyberpunk",
    "Steampunk": "Steampunk",
    "Vaporwave": "Vaporwave",
    "Line Art": "Seni Garis",
    "Generate image from text": "Buat gambar dari teks",
    "Upload image": "Unggah gambar",
    "Original": "Asli",
    "Generate prompt from image": "Buat prompt dari gambar",
    # ===== Refinement =====
    "Step 04 · Refine workflow": "Langkah 04 · Alur penyempurnaan",
    "Refine an existing prompt.": "Sempurnakan prompt yang ada.",
    "Pick a quick action or write custom instructions. Every refinement is versioned in your library.": "Pilih aksi cepat atau tulis instruksi khusus. Setiap penyempurnaan diberi versi di pustaka Anda.",
    "0.5 credits per refinement": "0,5 kredit per penyempurnaan",
    "Versioned": "Diberi versi",
    "Source": "Sumber",
    "Choose your prompt source": "Pilih sumber prompt Anda",
    "Manual input": "Input manual",
    "Your prompt": "Prompt Anda",
    "Paste or type the prompt you want to refine…": "Tempel atau ketik prompt yang ingin Anda sempurnakan…",
    "Save some prompts first to refine them.": "Simpan beberapa prompt terlebih dahulu untuk menyempurnakannya.",
    "No community prompts": "Tidak ada prompt komunitas",
    "Check back later for shared prompts.": "Cek lagi nanti untuk prompt yang dibagikan.",
    "Selected": "Terpilih",
    "Clear selection": "Hapus pilihan",
    "Action": "Aksi",
    "Choose how to refine": "Pilih cara menyempurnakan",
    "Quick actions": "Aksi cepat",
    "Shorten": "Persingkat",
    "Make the prompt more concise.": "Buat prompt lebih ringkas.",
    "Elaborate": "Perluas",
    "Add more details and context.": "Tambahkan lebih banyak detail dan konteks.",
    "Improve": "Tingkatkan",
    "Enhance clarity and effectiveness.": "Tingkatkan kejelasan dan efektivitas.",
    "Fix grammar": "Perbaiki tata bahasa",
    "Correct grammar and spelling.": "Perbaiki tata bahasa dan ejaan.",
    "Custom instructions": "Instruksi khusus",
    "Tell me how to refine your prompt": "Beri tahu saya cara menyempurnakan prompt Anda",
    "Example: Make it more professional, add technical details, change the tone to be more friendly, focus on specific aspects…": "Contoh: Buat lebih profesional, tambahkan detail teknis, ubah nadanya agar lebih ramah, fokuskan pada aspek tertentu…",
    "Tips for better refinements": "Tips untuk penyempurnaan yang lebih baik",
    "Be specific about what you want to change.": "Jelaskan secara spesifik apa yang ingin Anda ubah.",
    "Mention tone, style, or format preferences.": "Sebutkan preferensi nada, gaya, atau format.",
    "Specify target audience or use case.": "Tentukan audiens target atau kasus penggunaan.",
    "Refine prompt": "Sempurnakan prompt",
    "Costs 0.5 credits": "Biaya 0,5 kredit",
    "Refined prompt": "Prompt yang disempurnakan",
    "Save as new": "Simpan sebagai baru",
    "Refine again": "Sempurnakan lagi",
    # ===== Flash messages =====
    "Language changed to %(language)s": "Bahasa diubah ke %(language)s",
    "Language not supported": "Bahasa tidak didukung",
    # ===== Landing =====
    "Index 001": "Indeks 001",
    "Index 002": "Indeks 002",
    "A workshop for prompts.": "Bengkel untuk prompt.",
    "Generate, refine, and version your text prompts in one place. Built for makers who iterate.": "Buat, sempurnakan, dan kelola versi prompt teks Anda di satu tempat. Dibuat untuk pembuat yang berulang kali menyempurnakan.",
    "Two modes for two kinds of work. Describe a topic and let the model expand it, or paste a system prompt and iterate from there.": "Dua mode untuk dua jenis pekerjaan. Jelaskan topik dan biarkan model mengembangkannya, atau tempel prompt sistem dan ulangi dari situ.",
    "Tell the model what to change — tone, length, format, audience. Each refinement keeps a versioned history.": "Beri tahu model apa yang harus diubah — nada, panjang, format, audiens. Setiap penyempurnaan menyimpan riwayat versi.",
    "Personal saves stay private. Share with the community when you’re ready. Browse what others have shipped.": "Simpanan pribadi tetap privat. Bagikan ke komunitas saat Anda siap. Jelajahi apa yang telah dikirim orang lain.",
    "Built on three principles.": "Dibangun di atas tiga prinsip.",
    "Ready when you are.": "Siap saat Anda siap.",
    "Open the app": "Buka aplikasi",
    # ===== Common (with params) =====
    "by %(owner)s": "oleh %(owner)s",
    "%(count)s entries": "%(count)s entri",
    "%(count)s unlocked": "%(count)s terbuka",
    "Unlocked %(when)s": "Dibuka %(when)s",
    "Index 001 · Today": "Indeks 001 · Hari Ini",
    "Index 003": "Indeks 003",
    "Index 004": "Indeks 004",
    "Index 05 · Personal": "Indeks 05 · Pribadi",
    "Index 06 · Community": "Indeks 06 · Komunitas",
    "Index 07 · Account": "Indeks 07 · Akun",
    "Index 08 · Feedback": "Indeks 08 · Masukan",
    "Index 010 · Sign in": "Indeks 010 · Masuk",
    "Index 011 · Sign up": "Indeks 011 · Daftar",
    "Good day, %(username)s.": "Selamat datang, %(username)s.",
    "You have <span>%(points)s credits</span> available. Earn more by sharing prompts or add your own API key.": "Anda memiliki <span>%(points)s kredit</span>. Dapatkan lebih banyak dengan membagikan prompt atau tambahkan kunci API Anda sendiri.",
    "Add a Google Generative AI key in your profile. Or use the shared pool with your credits. Either way, generations route through your account.": "Tambahkan kunci Google Generative AI di profil Anda. Atau gunakan kolam bersama dengan kredit Anda. Bagaimanapun, pembuatan dirutekan melalui akun Anda.",
    "When a prompt is ready, share it. Browse what others have shipped. Fork anything you like into your own library.": "Saat prompt siap, bagikan. Jelajahi apa yang telah dikirim orang lain. Garpu apa pun yang Anda suka ke pustaka Anda sendiri.",
    "All your drafts, refinements, and shared prompts in one searchable list with side detail.": "Semua draf, penyempurnaan, dan prompt yang dibagikan dalam satu daftar yang bisa dicari dengan detail di samping.",
    "Describe what you want. The model expands it into a structured prompt with variables you can fill in later.": "Jelaskan apa yang Anda inginkan. Model mengembangkannya menjadi prompt terstruktur dengan variabel yang bisa Anda isi nanti.",
    "Paste a system prompt and the model writes a new one in the same voice. Optional image variants included.": "Tempel prompt sistem dan model akan menulis yang baru dengan nada yang sama. Varian gambar opsional disertakan.",
    "Tell the model what to change — tone, length, format, audience. Every refinement is versioned.": "Beri tahu model apa yang harus diubah — nada, panjang, format, audiens. Setiap penyempurnaan diberi versi.",
    # ===== Index section labels =====
    "Today": "Hari Ini",
    "Personal": "Pribadi",
    "Account": "Akun",
    "Feedback": "Masukan",
    # ===== Hero / index headings =====
    "Hello, %(username)s.": "Halo, %(username)s.",
    # ===== My library (personal.html) =====
    "Index 05 · Personal": "Indeks 05 · Pribadi",
    "Your prompt library.": "Pustaka prompt Anda.",
    "Edit, share, or refine any prompt. Search by title or content. All your drafts live here.": "Sunting, bagikan, atau sempurnakan prompt apa pun. Cari berdasarkan judul atau konten. Semua draf Anda ada di sini.",
    "New prompt": "Prompt baru",
    "Personal": "Pribadi",
    "Edit": "Sunting",
    "History": "Riwayat",
    "Generate a prompt and save it to build your library.": "Buat prompt dan simpan untuk membangun pustaka Anda.",
    "Open generator": "Buka pembuat",
    "Search by title or content…": "Cari berdasarkan judul atau konten…",
    # ===== {% trans %} block: index.html hero =====
    'You have <span class="t-accent"><strong id="heroPoints">%(points)s</strong> credits</span> available. Start a new prompt, refine a draft, or browse the community library.': 'Anda memiliki <span class="t-accent"><strong id="heroPoints">%(points)s</strong> kredit</span> yang tersedia. Buat prompt baru, sempurnakan draf, atau jelajahi pustaka komunitas.',
    # ===== {% trans %} block: basic.html help =====
    'Describe what you need. Click "Generate" or "Random" for a surprise.': 'Jelaskan apa yang Anda butuhkan. Klik "Buat" atau "Acak" untuk kejutan.',
    # ===== Library (community.html) =====
    "Community prompts.": "Prompt komunitas.",
    "System prompts and shared prompts from the community. Copy, save, or refine any of them.": "Prompt sistem dan prompt yang dibagikan dari komunitas. Salin, simpan, atau sempurnakan salah satunya.",
    # ===== Terms/Privacy browser title =====
    "Terms of Service": "Ketentuan Layanan",
    "Privacy Policy": "Kebijakan Privasi",
    "Legal · 09": "Legal · 09",
    "Legal · 10": "Legal · 10",
    "The rules that govern your use of Prompt Sanctuary. Plain language, no surprises. By creating an account or using the service, you agree to these terms.": "Aturan yang mengatur penggunaan Prompt Sanctuary Anda. Bahasa yang jelas, tanpa kejutan. Dengan membuat akun atau menggunakan layanan, Anda menyetujui ketentuan ini.",
    "What we collect, why, how long we keep it, and how to get it back. The short version: we keep what we need to run the service, nothing more, and you can delete your account at any time.": "Apa yang kami kumpulkan, mengapa, berapa lama kami menyimpannya, dan bagaimana mendapatkannya kembali. Versi singkat: kami menyimpan apa yang kami butuhkan untuk menjalankan layanan, tidak lebih, dan Anda dapat menghapus akun Anda kapan saja.",
    "Google AI Studio": "Google AI Studio",
    "Generate text prompt": "Buat prompt teks",
    "Enter your use case, select the prompt type, and configure other parameters to create a custom prompt with optional image variants.": "Masukkan kasus penggunaan Anda, pilih jenis prompt, dan konfigurasikan parameter lainnya untuk membuat prompt khusus dengan varian gambar opsional.",
    "Generate image prompt": "Buat prompt gambar",
    "Input": "Input",
    "Refine with structured feedback.": "Sempurnakan dengan masukan terstruktur.",
    "Keep everything in one library.": "Simpan semuanya dalam satu pustaka.",
    "Anime": "Anime",
    "Cyberpunk": "Cyberpunk",
    "Steampunk": "Steampunk",
    "Vaporwave": "Vaporwave",
    "Prompt Sanctuary": "Prompt Sanctuary",
    "Sanctuary": "Sanctuary",
    # ===== Eyebrow indices (long form) =====
    "Workflow / Refinement / Library": "Alur kerja / Penyempurnaan / Pustaka",
    "Generate from a topic or a system prompt.": "Buat dari topik atau prompt sistem.",
    # ===== Add a few more for the remaining empty ones =====
    "Refine a prompt": "Sempurnakan prompt",
    "New prompt": "Prompt baru",
    "Open the app": "Buka aplikasi",
    "Prompts": "Prompt",
    "Loading…": "Memuat…",
    "View details": "Lihat detail",
    "View all": "Lihat semua",
    "View more": "Lihat lebih",
    "View less": "Lihat lebih sedikit",
    "By": "Oleh",
    "With": "Dengan",
    "Edit prompt": "Sunting prompt",
    "Delete prompt?": "Hapus prompt?",
    "Delete this prompt? This cannot be undone.": "Hapus prompt ini? Tindakan ini tidak dapat dibatalkan.",
    "Delete this version? This cannot be undone.": "Hapus versi ini? Tindakan ini tidak dapat dibatalkan.",
    "Are you sure you want to delete this prompt?": "Apakah Anda yakin ingin menghapus prompt ini?",
    "Untitled": "Tanpa judul",
    "Unnamed": "Tanpa nama",
    "No description": "Tanpa deskripsi",
    "Untitled prompt": "Prompt tanpa judul",
    "Title": "Judul",
    "Description": "Deskripsi",
    "Optional": "Opsional",
    "Required": "Wajib",
    "Tags": "Tag",
    "Tag": "Tag",
    "Add tag": "Tambah tag",
    "Version": "Versi",
    "Versions": "Versi",
    "Original": "Asli",
    "Latest": "Terbaru",
    "From": "Dari",
    "Saved": "Tersimpan",
    "Shared": "Dibagikan",
    "Refined": "Disempurnakan",
    "Public": "Publik",
    "Private": "Privat",
    "System": "Sistem",
    "Member since": "Anggota sejak",
    "Last seen": "Terakhir terlihat",
    "Joined": "Bergabung",
    "Are you sure?": "Apakah Anda yakin?",
    "Confirm": "Konfirmasi",
    "Continue": "Lanjut",
    "Save changes": "Simpan perubahan",
    "Discard changes": "Buang perubahan",
    "Settings": "Pengaturan",
    "Notifications": "Notifikasi",
    "Privacy": "Privasi",
    "Help": "Bantuan",
    "Documentation": "Dokumentasi",
    "About": "Tentang",
    "Contact": "Kontak",
    "Report a bug": "Laporkan bug",
    "Send feedback": "Kirim masukan",
    "Rating": "Penilaian",
    "Rate": "Nilai",
    "Comment": "Komentar",
    "Add comment": "Tambah komentar",
    "Comments": "Komentar",
    "Like": "Suka",
    "Likes": "Suka",
    "Fork": "Garpu",
    "Forks": "Garpuan",
    "Favorite": "Favorit",
    "Favorites": "Favorit",
    "Star": "Bintang",
    "Stars": "Bintang",
    "Watch": "Pantau",
    "Watching": "Memantau",
    "Follow": "Ikuti",
    "Following": "Mengikuti",
    "Followers": "Pengikut",
    "Follower": "Pengikut",
    "Subscribe": "Berlangganan",
    "Subscribed": "Berlangganan",
    "Subscriptions": "Langganan",
    "Topic": "Topik",
    "Topics": "Topik",
    "Category": "Kategori",
    "Categories": "Kategori",
    "Featured": "Unggulan",
    "Trending": "Tren",
    "Recent": "Terbaru",
    "Popular": "Populer",
    "Top": "Teratas",
    "New": "Baru",
    "Old": "Lama",
    "All": "Semua",
    "None": "Tidak ada",
    "Any": "Apa saja",
    "Yes": "Ya",
    "No": "Tidak",
    "OK": "Oke",
    "Got it": "Mengerti",
    "Apply": "Terapkan",
    "Filter": "Saring",
    "Sort": "Urutkan",
    "Sort by": "Urutkan berdasarkan",
    "Ascending": "Naik",
    "Descending": "Turun",
    "Date": "Tanggal",
    "Name": "Nama",
    "Relevance": "Relevansi",
    "Reset": "Atur ulang",
    "Back": "Kembali",
    "Next": "Berikutnya",
    "Previous": "Sebelumnya",
    "First": "Pertama",
    "Last": "Terakhir",
    "Page": "Halaman",
    "of": "dari",
    "Showing": "Menampilkan",
    "results": "hasil",
    "No results": "Tidak ada hasil",
    "No matches": "Tidak ada kecocokan",
    "Found": "Ditemukan",
    "matches": "kecocokan",
    "Total": "Total",
    "Subtotal": "Subtotal",
    "Grand total": "Total keseluruhan",
    "Quantity": "Jumlah",
    "Price": "Harga",
    "Cost": "Biaya",
    "Free": "Gratis",
    "Paid": "Berbayar",
    "Premium": "Premium",
    "Pro": "Pro",
    "Beta": "Beta",
    "Alpha": "Alpha",
    "Stable": "Stabil",
    "Latest": "Terbaru",
    "Deprecated": "Tidak digunakan",
    "Experimental": "Eksperimental",
    "Coming soon": "Segera hadir",
    "New": "Baru",
    "Updated": "Diperbarui",
    "Beta feature": "Fitur beta",
    "Live": "Langsung",
    "Draft": "Draf",
    "Archived": "Diarsipkan",
    "Deleted": "Dihapus",
    "Active": "Aktif",
    "Inactive": "Tidak aktif",
    "Enabled": "Diaktifkan",
    "Disabled": "Dinonaktifkan",
    "On": "Aktif",
    "Off": "Nonaktif",
    "True": "Benar",
    "False": "Salah",
    "Required": "Wajib",
    "Optional": "Opsional",
    "Recommended": "Direkomendasikan",
    "Suggested": "Disarankan",
    "Example": "Contoh",
    "Examples": "Contoh",
    "Note": "Catatan",
    "Notes": "Catatan",
    "Tip": "Tips",
    "Tips": "Tips",
    "Warning": "Peringatan",
    "Caution": "Perhatian",
    "Important": "Penting",
    "Info": "Info",
    "Information": "Informasi",
    "Success": "Berhasil",
    "Error": "Kesalahan",
    "Failure": "Kegagalan",
    "Pending": "Menunggu",
    "In progress": "Sedang berlangsung",
    "Completed": "Selesai",
    "Failed": "Gagal",
    "Cancelled": "Dibatalkan",
    "Processing": "Memproses",
    "Saved successfully": "Berhasil disimpan",
    "Save failed": "Gagal menyimpan",
    "Delete failed": "Gagal menghapus",
    "Update failed": "Gagal memperbarui",
    "An error occurred": "Terjadi kesalahan",
    "Something went wrong": "Ada yang salah",
    "Try again": "Coba lagi",
    "Reload": "Muat ulang",
    "Refresh page": "Segarkan halaman",
    "Go back": "Kembali",
    "Go home": "Ke beranda",
    "Sign in required": "Masuk diperlukan",
    "You must be signed in to access this page.": "Anda harus masuk untuk mengakses halaman ini.",
    "You do not have permission to access this page.": "Anda tidak memiliki izin untuk mengakses halaman ini.",
    "Page not found": "Halaman tidak ditemukan",
    "The page you are looking for does not exist.": "Halaman yang Anda cari tidak ada.",
    "Server error": "Kesalahan server",
    "Service unavailable": "Layanan tidak tersedia",
    "Maintenance": "Pemeliharaan",
    "Under maintenance": "Sedang pemeliharaan",
    "Be back soon": "Akan segera kembali",
    "Welcome": "Selamat datang",
    "Welcome back": "Selamat datang kembali",
    "Goodbye": "Selamat tinggal",
    "See you soon": "Sampai jumpa lagi",
    "Hello": "Halo",
    "Hi": "Hai",
    "Hey": "Hai",
    "Thanks": "Terima kasih",
    "Thank you": "Terima kasih",
    "Please": "Mohon",
    "Sorry": "Maaf",
    "Apologies": "Mohon maaf",
    "Regards": "Hormat",
    "Best": "Terbaik",
    "Cheers": "Salam",
    "© 2026": "© 2026",
    "All rights reserved": "Hak cipta dilindungi",
}


def escape_po(s):
    """Escape a string for PO format: " → \\\\, \\\\n, etc."""
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    s = s.replace("\n", "\\n")
    s = s.replace("\t", "\\t")
    return s


def unescape_po(s):
    """Unescape a PO string: \\\" → \", \\n → \n, etc."""
    s = s.replace('\\"', '"')
    s = s.replace("\\n", "\n")
    s = s.replace("\\t", "\t")
    s = s.replace("\\\\", "\\")
    return s


def parse_pot(text):
    """Yield (meta_lines, msgid, msgstr) tuples from a POT/PO file.
    PO format: meta comments → msgid "..." (+ continuation lines) → msgstr "..." (+ continuation lines) → blank line.
    Continuation lines start with a double-quote on their own.
    """
    lines = text.split("\n")
    i = 0
    n = len(lines)
    while i < n:
        # Skip blank lines
        while i < n and lines[i].strip() == "":
            i += 1
        if i >= n:
            break

        # Collect meta: lines starting with # (including #:, #,, # )
        meta = []
        while i < n and lines[i].startswith("#"):
            meta.append(lines[i])
            i += 1
        if i >= n:
            break

        # Must be msgid (or msgid "")
        if not lines[i].startswith("msgid "):
            # Skip junk
            i += 1
            continue

        # Parse msgid line and continuation lines
        msgid_parts = []
        m = re.match(r'msgid\s+"(.*)"\s*$', lines[i])
        if m:
            msgid_parts.append(unescape_po(m.group(1)))
        i += 1
        while i < n and lines[i].startswith('"'):
            m = re.match(r'^\s*"(.*)"\s*$', lines[i])
            if m:
                msgid_parts.append(unescape_po(m.group(1)))
            i += 1

        msgid = "".join(msgid_parts)

        # Parse msgstr line and continuation lines
        msgstr_parts = []
        if i < n and lines[i].startswith("msgstr "):
            m = re.match(r'msgstr\s+"(.*)"\s*$', lines[i])
            if m:
                msgstr_parts.append(unescape_po(m.group(1)))
            i += 1
            while i < n and lines[i].startswith('"'):
                m = re.match(r'^\s*"(.*)"\s*$', lines[i])
                if m:
                    msgstr_parts.append(unescape_po(m.group(1)))
                i += 1
        msgstr = "".join(msgstr_parts)

        if msgid == "" and msgstr != "":
            # Header block — skip the existing header (we write our own).
            continue

        yield (meta, msgid, msgstr)


def main():
    pot_text = POT.read_text(encoding="utf-8")
    out = [HEADER.rstrip("\n"), ""]

    filled = 0
    total = 0
    fallback = 0
    for meta, msgid, _msgstr in parse_pot(pot_text):
        total += 1
        translated = TRANSLATIONS.get(msgid, msgid)
        if TRANSLATIONS.get(msgid):
            filled += 1
        else:
            fallback += 1
        for line in meta:
            out.append(line)
        out.append(f'msgid "{escape_po(msgid)}"')
        out.append(f'msgstr "{escape_po(translated)}"')
        out.append("")

    PO.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {PO}")
    print(f"Total msgids: {total}")
    print(f"Translated:   {filled}")
    print(f"Fallback to msgid: {fallback}")

    # Compile
    subprocess.run(
        ["pybabel", "compile", "-d", "web/translations"],
        check=True,
    )
    print("Compiled .mo")


if __name__ == "__main__":
    main()
