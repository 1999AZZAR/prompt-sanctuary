"""Add all the JS-rendered user-facing strings to the Indonesian .po
and update the runtime catalog.

These strings live in JS files (toasts, button labels, popup content).
They are translated at runtime via window._, which reads
`web/translations/<lang>/LC_MESSAGES/messages.mo`.

Run: docker exec prompt-sanctuary python3 /tmp/i18n_js.py
Or locally if babel is installed: python3 web/i18n_js_add.py
"""
import os
import re
from babel.messages.pofile import read_po, write_po
from babel.messages.mofile import write_mo

# ---- JS STRINGS TO TRANSLATE ----
# Each entry is (msgid, msgstr_id).
# Strings with %(name)s placeholders are kept verbatim.
JS_TRANSLATIONS = {
    # ===== community.js =====
    "Prompt copied to clipboard!": "Prompt disalin ke papan klip!",
    "Failed to copy prompt. Please try again.": "Gagal menyalin prompt. Silakan coba lagi.",
    "Confirm Save": "Konfirmasi Simpan",
    "Are you sure you want to save \"%(title)s\" to your personal library?": "Apakah Anda yakin ingin menyimpan \"%(title)s\" ke pustaka pribadi Anda?",
    "Save canceled.": "Penyimpanan dibatalkan.",
    "Prompt unshared successfully!": "Berhasil membatalkan berbagi prompt!",
    "Failed to unshare prompt: %(error)s": "Gagal membatalkan berbagi prompt: %(error)s",
    "Error unsharing prompt: %(message)s": "Kesalahan saat membatalkan berbagi prompt: %(message)s",
    "Confirm Unshare": "Konfirmasi Batalkan Berbagi",
    "Are you sure you want to unshare this prompt?": "Apakah Anda yakin ingin membatalkan berbagi prompt ini?",
    "Unshare canceled.": "Pembatalan berbagi dibatalkan.",
    "Failed to unshare prompt.": "Gagal membatalkan berbagi prompt.",
    "Prompt saved successfully!": "Prompt berhasil disimpan!",
    "Failed to save prompt.": "Gagal menyimpan prompt.",
    "Failed to save prompt: %(message)s": "Gagal menyimpan prompt: %(message)s",

    # ===== personal.js =====
    "Clipboard not available in this browser.": "Papan klip tidak tersedia di peramban ini.",
    "Failed to copy prompt.": "Gagal menyalin prompt.",
    "Missing prompt id.": "ID prompt tidak ada.",
    "No versions found for this prompt.": "Tidak ada versi ditemukan untuk prompt ini.",
    "Version History": "Riwayat Versi",
    "v%(n)s": "v%(n)s",
    "%(n)s version": "%(n)s versi",
    "%(n)s versions": "%(n)s versi",
    "current is v%(v)s": "saat ini v%(v)s",
    "Preview": "Pratinjau",
    "Restore": "Pulihkan",
    "Restored v%(v)s.": "Versi v%(v)s dipulihkan.",
    "Rollback failed": "Pemulihan gagal",
    "Failed to load history.": "Gagal memuat riwayat.",
    "Edit prompt": "Sunting prompt",
    "Editing": "Menyunting",
    "Prompt body": "Isi prompt",
    "Add a title before previewing.": "Tambahkan judul sebelum melihat pratinjau.",
    "Revert": "Kembalikan",
    "Reverted to the saved version.": "Dikembalikan ke versi tersimpan.",
    "Title cannot be empty.": "Judul tidak boleh kosong.",
    "Save changes": "Simpan perubahan",
    "Back to edit": "Kembali ke suntingan",
    "Save Prompt to Library": "Simpan Prompt ke Pustaka",
    "Enter a title for this prompt:": "Masukkan judul untuk prompt ini:",
    "Prompt Title": "Judul Prompt",
    "Save": "Simpan",
    "Prompt updated successfully!": "Prompt berhasil diperbarui!",
    "Failed to update prompt.": "Gagal memperbarui prompt.",
    "Error updating prompt: %(message)s": "Kesalahan memperbarui prompt: %(message)s",
    "Delete prompt": "Hapus prompt",
    "Are you sure you want to delete this prompt? This action cannot be undone.": "Apakah Anda yakin ingin menghapus prompt ini? Tindakan ini tidak dapat dibatalkan.",
    "Delete": "Hapus",
    "Prompt deleted successfully!": "Prompt berhasil dihapus!",
    "Failed to delete prompt.": "Gagal menghapus prompt.",
    "Error deleting prompt: %(message)s": "Kesalahan menghapus prompt: %(message)s",
    "Cannot share: critical data missing from button.": "Tidak dapat berbagi: data penting hilang dari tombol.",
    "Share": "Bagikan",
    "Unshare": "Batalkan Berbagi",
    "Prompt is already shared!": "Prompt sudah dibagikan!",
    "Shared prompt updated!": "Prompt bersama diperbarui!",
    "Prompt shared successfully!": "Prompt berhasil dibagikan!",
    "Failed to share prompt.": "Gagal membagikan prompt.",
    "Error sharing prompt: %(message)s": "Kesalahan membagikan prompt: %(message)s",
    "Cannot unshare: missing prompt ID.": "Tidak dapat membatalkan berbagi: ID prompt hilang.",
    "Cannot update: critical data missing from button.": "Tidak dapat memperbarui: data penting hilang dari tombol.",

    # ===== generator.js =====
    "An error occurred while generating the response.": "Terjadi kesalahan saat membuat respons.",
    "Error generating response. Please try again.": "Kesalahan membuat respons. Silakan coba lagi.",
    "Insufficient points! Visit your profile to see your current balance.": "Poin tidak cukup! Kunjungi profil Anda untuk melihat saldo saat ini.",
    "An error occurred while submitting the form.": "Terjadi kesalahan saat mengirim formulir.",
    "Generating response...": "Membuat respons...",
    "Nothing to save! Generate a prompt first.": "Tidak ada yang disimpan! Buat prompt terlebih dahulu.",
    "Generate": "Buat",
    "Random": "Acak",
    "Response copied to clipboard!": "Respons disalin ke papan klip!",
    "Failed to copy response.": "Gagal menyalin respons.",
    "Failed to copy response: content not found.": "Gagal menyalin respons: konten tidak ditemukan.",
    "An error occurred while saving the prompt. Check console for details.": "Terjadi kesalahan saat menyimpan prompt. Periksa konsol untuk detail.",

    # ===== feedback.js =====
    "Error": "Kesalahan",
    "Please enter your feedback before submitting.": "Silakan masukkan umpan balik Anda sebelum mengirim.",
    "An error occurred. Please try again.": "Terjadi kesalahan. Silakan coba lagi.",
    "Network error (status %(status)s). Please try again.": "Kesalahan jaringan (status %(status)s). Silakan coba lagi.",
    "An unexpected error occurred. Please try again.": "Terjadi kesalahan tak terduga. Silakan coba lagi.",

    # ===== login.js =====
    "An error occurred.": "Terjadi kesalahan.",
    "A network error occurred. Please try again.": "Terjadi kesalahan jaringan. Silakan coba lagi.",
    "Please wait…": "Harap tunggu…",
    "Username and password are required.": "Nama pengguna dan kata sandi wajib diisi.",
    "Username cannot contain spaces.": "Nama pengguna tidak boleh mengandung spasi.",
    "Username cannot be equal to password.": "Nama pengguna tidak boleh sama dengan kata sandi.",
    "Username cannot be one of: system, admin, consol, sysadmin, useradmin.": "Nama pengguna tidak boleh salah satu dari: system, admin, consol, sysadmin, useradmin.",
    "All fields are required.": "Semua kolom wajib diisi.",
    "Username must be 3 to 32 characters.": "Nama pengguna harus 3 hingga 32 karakter.",
    "Username may only contain letters, numbers, and underscores.": "Nama pengguna hanya boleh berisi huruf, angka, dan garis bawah.",
    "Password must be at least 6 characters.": "Kata sandi harus minimal 6 karakter.",
    "Passwords do not match.": "Kata sandi tidak cocok.",
    "Welcome! You earned %(bonus)s points for your daily login. You unlocked a new achievement: %(achievement)s! You earned %(points)s achievement points!": "Selamat datang! Anda mendapatkan %(bonus)s poin untuk masuk harian. Anda membuka pencapaian baru: %(achievement)s! Anda mendapatkan %(points)s poin pencapaian!",
    "Welcome! You earned %(bonus)s points for your daily login. You unlocked %(count)s new achievements! You earned %(points)s achievement points!": "Selamat datang! Anda mendapatkan %(bonus)s poin untuk masuk harian. Anda membuka %(count)s pencapaian baru! Anda mendapatkan %(points)s poin pencapaian!",
    "Welcome!": "Selamat datang!",
    "You earned %(bonus)s points for your daily login. ": "Anda mendapatkan %(bonus)s poin untuk masuk harian. ",
    "You unlocked a new achievement: %(achievement)s! ": "Anda membuka pencapaian baru: %(achievement)s! ",
    "You unlocked %(count)s new achievements! ": "Anda membuka %(count)s pencapaian baru! ",
    "You earned %(points)s achievement points!": "Anda mendapatkan %(points)s poin pencapaian!",

    # ===== api_key_manager.js =====
    "Failed to load API key status": "Gagal memuat status kunci API",
    "API key active": "Kunci API aktif",
    "Using your key: %(key)s": "Menggunakan kunci Anda: %(key)s",
    "Change": "Ubah",
    "Cancel": "Batal",
    "API key not validated": "Kunci API belum divalidasi",
    "Please validate your API key to use it.": "Silakan validasi kunci API Anda untuk menggunakannya.",
    "No API Key Set": "Kunci API Belum Diatur",
    "Add your Gemini API key to avoid point consumption.": "Tambahkan kunci API Gemini Anda untuk menghindari konsumsi poin.",
    "Please enter an API key": "Silakan masukkan kunci API",
    "Validating…": "Memvalidasi…",
    "Failed to validate API key": "Gagal memvalidasi kunci API",
    "+%(points)s points awarded!": "+%(points)s poin diberikan!",
    "New achievement unlocked: %(list)s": "Pencapaian baru terbuka: %(list)s",
    "Are you sure you want to remove your API key? You will start consuming points again.": "Apakah Anda yakin ingin menghapus kunci API Anda? Anda akan mulai mengonsumsi poin lagi.",
    "Failed to remove API key": "Gagal menghapus kunci API",

    # ===== notifications.js =====
    "OK": "OKE",
    "Yes": "Ya",
    "No": "Tidak",
    "Close": "Tutup",
    "Copy prompt": "Salin prompt",
    "Copied to clipboard!": "Disalin ke papan klip!",
    "Failed to copy.": "Gagal menyalin.",
    "characters": "karakter",
    "words": "kata",
    "lines": "baris",
    "Prompt": "Prompt",
}


def update_po(po_path: str, translations: dict) -> int:
    with open(po_path, "rb") as f:
        catalog = read_po(f)

    existing = {m.id: m for m in catalog}
    added = 0
    for msgid, msgstr in translations.items():
        if msgid in existing:
            m = existing[msgid]
            # Force the Indonesian translation
            if msgstr:
                m.string = msgstr
        else:
            from babel.messages.catalog import Message
            catalog.add(msgid, msgstr or msgid)
            added += 1

    with open(po_path, "wb") as f:
        write_po(f, catalog, omit_header=False)

    return added


def compile_mo(po_path: str, mo_path: str) -> None:
    with open(po_path, "rb") as f:
        catalog = read_po(f)
    with open(mo_path, "wb") as f:
        write_mo(f, catalog)


if __name__ == "__main__":
    import sys
    # Default to the script's directory's parent (i.e. web/) but allow override
    # when the script is copied to /tmp.
    if len(sys.argv) > 1:
        base = os.path.join(sys.argv[1], "translations")
    else:
        base = os.path.join(os.path.dirname(__file__), "translations")
    id_po = os.path.join(base, "id", "LC_MESSAGES", "messages.po")
    id_mo = os.path.join(base, "id", "LC_MESSAGES", "messages.mo")
    en_po = os.path.join(base, "en", "LC_MESSAGES", "messages.po")
    en_mo = os.path.join(base, "en", "LC_MESSAGES", "messages.mo")

    added_id = update_po(id_po, JS_TRANSLATIONS)
    compile_mo(id_po, id_mo)
    print(f"id: added {added_id} new msgids; recompiled {id_mo}")

    # For en, the msgstr is the msgid (English is the source), but
    # the catalog must still contain them so the runtime lookup works.
    EN = {k: "" for k in JS_TRANSLATIONS}
    added_en = update_po(en_po, EN)
    compile_mo(en_po, en_mo)
    print(f"en: added {added_en} new msgids (empty msgstrs); recompiled {en_mo}")
