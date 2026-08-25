"""
capture_and_send.py

Mengambil screenshot full-page dari dashboard provisioning (Looker Studio)
dan mengirimkannya ke Telegram.

Environment variables yang dibutuhkan (diset lewat GitHub Secrets):
- DASHBOARD_URL       : URL public dashboard yang mau di-capture
- TELEGRAM_BOT_TOKEN  : token bot Telegram (dari BotFather)
- TELEGRAM_CHAT_ID    : id grup/channel tujuan (boleh negatif, mis. -100xxxx)
"""

import os
import sys
from datetime import datetime, timezone, timedelta

import requests
from playwright.sync_api import sync_playwright

WIB = timezone(timedelta(hours=7))

DASHBOARD_URL = os.environ.get("DASHBOARD_URL")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

SCREENSHOT_PATH = "dashboard_capture.png"


def capture_dashboard(url: str, output_path: str) -> None:
    """Buka dashboard dengan headless browser dan simpan full-page screenshot."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 2000})

        # Catatan: sengaja TIDAK pakai wait_until="networkidle" di sini.
        # Dashboard Looker Studio biasanya terus melakukan polling data di
        # latar belakang (live update, analytics beacon), sehingga koneksi
        # network nyaris tidak pernah benar-benar "idle" dan goto() akan
        # selalu timeout kalau menunggu kondisi itu. Sebagai gantinya,
        # tunggu "load" (dokumen + resource utama selesai), lalu beri jeda
        # tetap supaya chart sempat selesai render.
        page.goto(url, wait_until="load", timeout=90_000)
        page.wait_for_timeout(15_000)

        page.screenshot(path=output_path, full_page=True)
        browser.close()


def send_photo_to_telegram(image_path: str, caption: str) -> None:
    """Kirim file gambar ke Telegram sebagai document (kualitas tetap tajam,
    tidak dikompres seperti sendPhoto)."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    with open(image_path, "rb") as f:
        response = requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption},
            files={"document": f},
            timeout=30,
        )
    response.raise_for_status()


def send_text_to_telegram(text: str) -> None:
    """Kirim pesan teks biasa ke Telegram — dipakai untuk notifikasi error."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=30)


def main() -> None:
    if not DASHBOARD_URL or not BOT_TOKEN or not CHAT_ID:
        print(
            "ERROR: pastikan DASHBOARD_URL, TELEGRAM_BOT_TOKEN, dan "
            "TELEGRAM_CHAT_ID sudah diset sebagai environment variable."
        )
        sys.exit(1)

    now_wib = datetime.now(WIB).strftime("%d %B %Y, %H:%M WIB")

    try:
        capture_dashboard(DASHBOARD_URL, SCREENSHOT_PATH)
        caption = f"Update Dashboard Provisioning Klojen\n{now_wib}"
        send_photo_to_telegram(SCREENSHOT_PATH, caption)
        print("Berhasil capture dan kirim ke Telegram.")
    except Exception as exc:
        error_message = f"Gagal capture dashboard ({now_wib}).\nDetail error: {exc}"
        print(error_message)
        try:
            send_text_to_telegram(error_message)
        except Exception:
            print("Gagal juga mengirim notifikasi error ke Telegram.")
        sys.exit(1)


if __name__ == "__main__":
    main()
