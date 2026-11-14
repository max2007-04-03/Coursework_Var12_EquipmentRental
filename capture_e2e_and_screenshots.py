import os
import sys
import time
import subprocess
from playwright.sync_api import sync_playwright

root_dir = os.path.dirname(os.path.abspath(__file__))
screenshots_dir = os.path.join(root_dir, "docs", "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)

db_path = os.path.join(root_dir, "Data", "equipment_rental.db")
if os.path.exists(db_path):
    os.remove(db_path)

env = os.environ.copy()
env["EQUIPRENT_DB_PATH"] = db_path

print("Starting ASP.NET Core WebApi server on http://127.0.0.1:5085 ...")
exe_path = os.path.join(root_dir, "src", "EquipmentRental.WebApi", "bin", "Debug", "net10.0", "EquipmentRental.WebApi.exe")
server_proc = subprocess.Popen(
    [exe_path, "--urls", "http://127.0.0.1:5085"],
    cwd=os.path.join(root_dir, "src", "EquipmentRental.WebApi"),
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
)

try:
    # Очікуємо готовності сервера
    import urllib.request
    ready = False
    for _ in range(30):
        try:
            with urllib.request.urlopen("http://127.0.0.1:5085/api/health", timeout=1) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except Exception:
            time.sleep(0.5)

    if not ready:
        out = server_proc.stdout.read().decode("utf-8", errors="ignore") if server_proc.stdout else ""
        raise RuntimeError(f"Server did not start on http://127.0.0.1:5085 in time. Output:\n{out}")

    print("Server is UP! Running Playwright E2E scenarios and capturing screenshots...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)

        # 1. Desktop 1280px: Головний екран каталогу з фізичними екземплярами
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        page.goto("http://127.0.0.1:5085")
        page.wait_for_selector(".equipment-card")
        time.sleep(0.8)
        page.screenshot(path=os.path.join(screenshots_dir, "ui_01_catalog_desktop.png"), full_page=False)
        print("Captured ui_01_catalog_desktop.png")

        # 2. Фільтрація каталогу за категорією та пошуком
        page.select_option("#f-category", "Енергообладнання")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(screenshots_dir, "ui_02_catalog_filtered.png"), full_page=False)
        print("Captured ui_02_catalog_filtered.png")

        # 3. Стан порожньої вибірки каталогу
        page.fill("#f-search", "НеіснуючийПрилад999")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(screenshots_dir, "ui_03_empty_search.png"), full_page=False)
        print("Captured ui_03_empty_search.png")

        # Скидаємо фільтри та переходимо на екран Календаря доступності генератора Honda EU22i
        page.click('button:has-text("Скинути")')
        time.sleep(0.5)
        page.click('button.nav-btn >> nth=1')
        page.wait_for_selector(".availability-grid-table")
        page.select_option(".details-switch-eq select", "eqt-01")
        time.sleep(0.7)
        page.screenshot(path=os.path.join(screenshots_dir, "ui_04_calendar_and_calculator.png"), full_page=True)
        print("Captured ui_04_calendar_and_calculator.png")

        # 4. Демонстрація конфлікту накладання на технічну перерву (409 Conflict) + пропозиція Черги очікування (Waitlist)
        page.click('button:has-text("Накладання на тех. перерву")')
        time.sleep(0.6)
        page.click('button[type="submit"]')
        time.sleep(0.6)
        page.screenshot(path=os.path.join(screenshots_dir, "ui_05_conflict_and_waitlist.png"), full_page=True)
        print("Captured ui_05_conflict_and_waitlist.png")

        # 5. Демонстрація помилки валідації (кінець раніше початку - 400 END_BEFORE_START)
        page.click('button:has-text("Кінець раніше початку")')
        time.sleep(0.5)
        page.click('button[type="submit"]')
        time.sleep(0.5)
        page.screenshot(path=os.path.join(screenshots_dir, "ui_06_validation_error.png"), full_page=True)
        print("Captured ui_06_validation_error.png")

        # 6. Успішне створення нового бронювання на вільний інтервал (201 Created)
        page.click('button:has-text("Вільний інтервал")')
        time.sleep(0.5)
        page.click('button[type="submit"]')
        time.sleep(0.7)
        page.screenshot(path=os.path.join(screenshots_dir, "ui_07_booking_created_success.png"), full_page=True)
        print("Captured ui_07_booking_created_success.png")

        # 7. Особистий кабінет клієнта та черга очікування
        page.click('button.nav-btn >> nth=2')
        time.sleep(0.6)
        page.screenshot(path=os.path.join(screenshots_dir, "ui_08_client_cabinet.png"), full_page=True)
        print("Captured ui_08_client_cabinet.png")

        # 8. Спроба відкрити панель менеджера під роллю КЛІЄНТ (попередження 403 FORBIDDEN_ROLE)
        page.click('button.nav-btn >> nth=3')
        time.sleep(0.5)
        page.screenshot(path=os.path.join(screenshots_dir, "ui_09_forbidden_role_403.png"), full_page=False)
        print("Captured ui_09_forbidden_role_403.png")

        # 9. Перемикання на роль МЕНЕДЖЕР (Мельник Ірина Сергіївна) та відкриття картки подій і повернення
        page.select_option("#role-select", "manager@equiprent.op.edu.ua")
        time.sleep(0.7)
        page.click('button:has-text("Керувати / Події") >> nth=0')
        time.sleep(0.6)
        page.screenshot(path=os.path.join(screenshots_dir, "ui_10_manager_panel_and_events.png"), full_page=True)
        print("Captured ui_10_manager_panel_and_events.png")

        # 10. Перевірка адаптивності на контрольній точці 768px (Планшет)
        page.set_viewport_size({"width": 768, "height": 900})
        page.click('button.nav-btn >> nth=1')
        time.sleep(0.5)
        page.screenshot(path=os.path.join(screenshots_dir, "ui_11_responsive_768px.png"), full_page=False)
        print("Captured ui_11_responsive_768px.png")

        # 11. Перевірка адаптивності на контрольній точці 360px (Мобільний екран)
        page.set_viewport_size({"width": 360, "height": 1150})
        page.click('button.nav-btn >> nth=0')
        time.sleep(0.5)
        page.screenshot(path=os.path.join(screenshots_dir, "ui_12_responsive_360px.png"), full_page=False)
        print("Captured ui_12_responsive_360px.png")

        browser.close()
        print("All 12 real UI & E2E screenshots captured successfully!")

finally:
    server_proc.terminate()
    try:
        server_proc.wait(timeout=5)
    except Exception:
        server_proc.kill()
