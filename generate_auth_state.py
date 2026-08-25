"""
generate_auth_state.py

Jalankan sekali secara LOKAL di laptop kamu (BUKAN di GitHub Actions) untuk
login manual dan menyimpan sesi login ke file auth.json. File inilah yang
nanti dipakai capture_and_send.py supaya tidak perlu login ulang tiap kali
jalan otomatis.

Cara pakai:
1. Jalankan: python generate_auth_state.py
2. Jendela Chrome akan terbuka otomatis (bukan headless, supaya kamu bisa
   login dan menyelesaikan verifikasi 2 langkah kalau diminta).
3. Login dengan akun Google yang PUNYA akses viewer ke dashboard.
4. Buka URL dashboard-nya di tab yang sama, pastikan dashboard benar-benar
   tampil (bukan diminta login lagi / minta akses).
5. Kembali ke terminal ini, tekan Enter untuk menyimpan sesi ke auth.json.

PENTING: auth.json yang dihasilkan setara dengan "kunci masuk" akun Google
itu. Jangan pernah di-commit ke repo publik, jangan ditempel ke chat mana
pun — isinya nanti hanya ditempel ke kotak Secret di GitHub (yang tidak
bisa dibaca ulang setelah disimpan).
"""

from playwright.sync_api import sync_playwright

AUTH_FILE = "auth.json"


def main() -> None:
    dashboard_url = input("Tempel URL dashboard yang mau dicek aksesnya: ").strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://accounts.google.com/")
        print("\nSilakan login manual di jendela Chrome yang baru terbuka.")
        if dashboard_url:
            print("Setelah login, buka juga tab baru ke URL dashboard untuk memastikan aksesnya benar:")
            print(dashboard_url)
        input("\nSetelah selesai login (dan dashboard tampil normal), tekan Enter di sini...")

        context.storage_state(path=AUTH_FILE)
        print(f"\nSesi login tersimpan di {AUTH_FILE}")
        print("Buka file itu, salin seluruh isinya, tempel sebagai isi GitHub Secret PLAYWRIGHT_STORAGE_STATE.")

        browser.close()


if __name__ == "__main__":
    main()
