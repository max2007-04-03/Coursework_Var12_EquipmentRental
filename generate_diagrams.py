import os
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 11

root_dir = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(root_dir, "docs", "diagrams")
os.makedirs(out_dir, exist_ok=True)

def save_fig(fig, name):
    png_path = os.path.join(out_dir, f"{name}.png")
    svg_path = os.path.join(out_dir, f"{name}.svg")
    fig.savefig(png_path, dpi=260, bbox_inches="tight", facecolor="white")
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {name}.png & {name}.svg")

def draw_box(ax, x, y, w, h, text, bold=False, bg="#FFFFFF", ec="#000000", lw=1.2, fontsize=10.5, align="center"):
    rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.005",
                          facecolor="#FFFFFF", edgecolor="#000000", linewidth=lw)
    ax.add_patch(rect)
    tx = x + w / 2 if align == "center" else x + 0.02
    ha = "center" if align == "center" else "left"
    ax.text(tx, y + h / 2, text, ha=ha, va="center", fontsize=fontsize,
            fontweight="bold" if bold else "normal", color="#000000", wrap=True)

def draw_diamond(ax, cx, cy, w, h, text, fontsize=10):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    poly = patches.Polygon(pts, closed=True, facecolor="#FFFFFF", edgecolor="#0F172A", linewidth=1.4)
    ax.add_patch(poly)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fontsize, color="#0F172A")

def draw_arrow(ax, x1, y1, x2, y2, label=None, lx=None, ly=None, dashed=False):
    ls = "--" if dashed else "-"
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color="#0F172A", lw=1.3, linestyle=ls, mutation_scale=13))
    if label:
        tx = lx if lx is not None else (x1 + x2) / 2 + 0.02
        ty = ly if ly is not None else (y1 + y2) / 2
        ax.text(tx, ty, label, fontsize=9.5, color="#0F172A", fontweight="bold")

# ==============================================================================
# 1. UML Use Case Diagram (Рисунок 1.1)
# ==============================================================================
def make_use_case():
    fig, ax = plt.subplots(figsize=(10, 7.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7.5)
    ax.axis("off")

    # Межа системи
    sys_rect = patches.Rectangle((2.2, 0.5), 5.6, 6.6, fill=False, edgecolor="#0F172A", linewidth=1.6)
    ax.add_patch(sys_rect)
    ax.text(5.0, 6.82, "Вебсистема оренди обладнання з календарем доступності",
            ha="center", va="center", fontsize=11.5, fontweight="bold")

    use_cases = [
        (5.0, 6.1, "UC-01: Переглянути каталог і календар\nдоступності фізичних екземплярів"),
        (5.0, 5.15, "UC-02: Розрахувати вартість оренди,\nзаставу та межу технічної перерви"),
        (5.0, 4.2, "UC-03: Створити заявку на оренду\nобраного фізичного екземпляра"),
        (5.0, 3.25, "UC-04: Стати в чергу очікування (Waitlist)\nпри зайнятості екземпляра"),
        (5.0, 2.3, "UC-05: Продовжити або скасувати\nвласне активне бронювання"),
        (5.0, 1.35, "UC-06: Погодити/відхилити заявку, оформити\nвидачу та повернення з обліком прострочення"),
    ]

    for cx, cy, label in use_cases:
        ell = patches.Ellipse((cx, cy), 4.7, 0.72, facecolor="#F8FAFC", edgecolor="#0F172A", linewidth=1.3)
        ax.add_patch(ell)
        ax.text(cx, cy, label, ha="center", va="center", fontsize=9.5)

    def draw_actor(ax, x, y, name):
        head = patches.Circle((x, y + 0.45), 0.16, fill=False, edgecolor="#0F172A", lw=1.5)
        ax.add_patch(head)
        ax.plot([x, x], [y + 0.29, y - 0.1], color="#0F172A", lw=1.5)
        ax.plot([x - 0.25, x + 0.25], [y + 0.18, y + 0.18], color="#0F172A", lw=1.5)
        ax.plot([x, x - 0.22], [y - 0.1, y - 0.42], color="#0F172A", lw=1.5)
        ax.plot([x, x + 0.22], [y - 0.1, y - 0.42], color="#0F172A", lw=1.5)
        ax.text(x, y - 0.62, name, ha="center", va="center", fontsize=10.5, fontweight="bold")

    draw_actor(ax, 0.9, 5.7, "Гість")
    draw_actor(ax, 0.9, 3.2, "Клієнт\n(Орендар)")
    draw_actor(ax, 9.1, 2.8, "Менеджер\nпрокату")

    # Лінії асоціацій
    ax.plot([1.2, 2.65], [5.7, 6.1], color="#0F172A", lw=1.2)
    ax.plot([1.2, 2.65], [5.7, 5.15], color="#0F172A", lw=1.2)

    for target_y in [6.1, 5.15, 4.2, 3.25, 2.3]:
        ax.plot([1.2, 2.65], [3.2, target_y], color="#0F172A", lw=1.2)

    for target_y in [6.1, 4.2, 3.25, 2.3, 1.35]:
        ax.plot([8.8, 7.35], [2.8, target_y], color="#0F172A", lw=1.2)

    ax.text(5.0, 0.2, "Лінії позначають участь акторів у прецедентах (UML Use Case), а не порядок виконання.",
            ha="center", va="center", fontsize=9.5, style="italic")
    save_fig(fig, "fig_1_1_use_case")

# ==============================================================================
# 2. Блок-схема перевірки запиту на бронювання (Рисунок 2.1, за зразком Д.2)
# ==============================================================================
def make_flowchart_request():
    fig, ax = plt.subplots(figsize=(8.8, 10.5))
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 11)
    ax.axis("off")

    # Початок
    term_start = FancyBboxPatch((2.1, 10.1), 2.6, 0.55, boxstyle="round,pad=0.02,rounding_size=0.25",
                                facecolor="#FFFFFF", edgecolor="#0F172A", lw=1.4)
    ax.add_patch(term_start)
    ax.text(3.4, 10.37, "Початок", ha="center", va="center", fontweight="bold")

    draw_box(ax, 1.5, 9.0, 3.8, 0.72, "Отримати unitId, startsAt, endsAt,\npurpose та перевірену сесію")
    draw_arrow(ax, 3.4, 10.1, 3.4, 9.72)

    draw_diamond(ax, 3.4, 7.85, 3.8, 0.95, "Є дійсна сесія та\nправо створення?")
    draw_arrow(ax, 3.4, 9.0, 3.4, 8.33)
    draw_box(ax, 6.0, 7.5, 2.6, 0.7, "Повернути 401 / 403\n(Problem Details)")
    draw_arrow(ax, 5.3, 7.85, 6.0, 7.85, "Ні", 5.5, 7.98)

    draw_diamond(ax, 3.4, 6.3, 3.8, 0.95, "Формат полів коректний,\nendsAt > startsAt?")
    draw_arrow(ax, 3.4, 7.37, 3.4, 6.78, "Так", 3.55, 7.05)
    draw_box(ax, 6.0, 5.95, 2.6, 0.7, "Повернути 400\nEND_BEFORE_START")
    draw_arrow(ax, 5.3, 6.3, 6.0, 6.3, "Ні", 5.5, 6.43)

    draw_diamond(ax, 3.4, 4.75, 3.8, 0.95, "Екземпляр AVAILABLE,\nтривалість у межах тарифу?")
    draw_arrow(ax, 3.4, 5.82, 3.4, 5.23, "Так", 3.55, 5.5)
    draw_box(ax, 6.0, 4.4, 2.6, 0.7, "Повернути 400 / 404\nкеровану відмову")
    draw_arrow(ax, 5.3, 4.75, 6.0, 4.75, "Ні", 5.5, 4.88)

    # Підпрограма (подвійні вертикальні лінії за ГОСТ/ДСТУ)
    draw_box(ax, 1.5, 3.1, 3.8, 0.85, "Атомарне створення бронювання,\nрозрахунок вартості й запис історії\n(окрема блок-схема рис. 2.2)")
    ax.plot([1.7, 1.7], [3.1, 3.95], color="#0F172A", lw=1.3)
    ax.plot([5.1, 5.1], [3.1, 3.95], color="#0F172A", lw=1.3)
    draw_arrow(ax, 3.4, 4.27, 3.4, 3.95, "Так", 3.55, 4.08)

    draw_box(ax, 1.5, 1.8, 3.8, 0.75, "Повернути результат клієнтові:\n201 Created / 409 Conflict / помилка")
    draw_arrow(ax, 3.4, 3.1, 3.4, 2.55)

    # Об'єднання бічних гілок відмов до виходу
    ax.plot([8.6, 8.6], [7.85, 1.2], color="#0F172A", lw=1.3)
    ax.plot([8.6, 8.6], [7.85, 7.85], color="#0F172A", lw=1.3)
    for ry in [7.85, 6.3, 4.75]:
        ax.plot([8.6, 8.6], [ry, ry], color="#0F172A", lw=1.3)
    ax.plot([8.6, 8.6], [1.2, 7.85], color="#0F172A", lw=1.3)
    ax.plot([7.3, 7.3], [7.5, 7.2], color="#0F172A", lw=0) # dummy
    # З'єднання правих блоків із вертикальною шиною x=8.75
    for ry in [7.85, 6.3, 4.75]:
        ax.plot([8.6, 8.75], [ry, ry], color="#0F172A", lw=1.3)
    ax.plot([8.75, 8.75], [1.35, 7.85], color="#0F172A", lw=1.3)
    draw_arrow(ax, 8.75, 1.35, 3.4, 1.35)

    term_end = FancyBboxPatch((2.1, 0.55), 2.6, 0.55, boxstyle="round,pad=0.02,rounding_size=0.25",
                              facecolor="#FFFFFF", edgecolor="#0F172A", lw=1.4)
    ax.add_patch(term_end)
    ax.text(3.4, 0.82, "Кінець", ha="center", va="center", fontweight="bold")
    draw_arrow(ax, 3.4, 1.8, 3.4, 1.1)

    save_fig(fig, "fig_2_1_flowchart_request")

# ==============================================================================
# 3. Блок-схема атомарного створення бронювання (Рисунок 2.2, за зразком Д.3)
# ==============================================================================
def make_flowchart_atomic():
    fig, ax = plt.subplots(figsize=(9.0, 10.2))
    ax.set_xlim(0, 9.2)
    ax.set_ylim(0, 10.5)
    ax.axis("off")

    term_start = FancyBboxPatch((2.1, 9.6), 2.6, 0.52, boxstyle="round,pad=0.02,rounding_size=0.25",
                                facecolor="#FFFFFF", edgecolor="#0F172A", lw=1.4)
    ax.add_patch(term_start)
    ax.text(3.4, 9.86, "Початок", ha="center", va="center", fontweight="bold")

    draw_box(ax, 1.5, 8.55, 3.8, 0.65, "Почати транзакцію СКБД\n(BEGIN IMMEDIATE TRANSACTION)")
    draw_arrow(ax, 3.4, 9.6, 3.4, 9.2)

    draw_box(ax, 1.3, 7.25, 4.2, 0.85, "Обчислити bufferEndsAt = endsAt + Δt_buf;\nвибрати активні бронювання екземпляра\n(PENDING, CONFIRMED, ISSUED)")
    draw_arrow(ax, 3.4, 8.55, 3.4, 8.1)

    draw_diamond(ax, 3.4, 5.85, 4.2, 1.05, "Відсутній перетин інтервалів\nstartsAt < B.bufferEndsAt та\nB.startsAt < bufferEndsAt?")
    draw_arrow(ax, 3.4, 7.25, 3.4, 6.38)

    draw_box(ax, 6.1, 5.45, 2.7, 0.8, "Відкотити транзакцію;\nповернути 409 Conflict\n(INTERVAL_CONFLICT)")
    draw_arrow(ax, 5.5, 5.85, 6.1, 5.85, "Ні", 5.65, 5.98)

    draw_box(ax, 1.3, 4.1, 4.2, 0.85, "Обчислити billedUnits = ceil(Δt / U),\nbasePriceMinor, depositMinor;\nвставити запис у bookings та rental_events")
    draw_arrow(ax, 3.4, 5.32, 3.4, 4.95, "Так", 3.55, 5.1)

    draw_diamond(ax, 3.4, 2.8, 3.8, 0.9, "Запис у сховище\nвиконано успішно?")
    draw_arrow(ax, 3.4, 4.1, 3.4, 3.25)

    draw_box(ax, 6.1, 2.4, 2.7, 0.8, "Відкотити транзакцію\n(ROLLBACK); повернути\nкеровану помилку")
    draw_arrow(ax, 5.3, 2.8, 6.1, 2.8, "Ні", 5.55, 2.93)

    draw_box(ax, 1.5, 1.35, 3.8, 0.72, "Зафіксувати транзакцію (COMMIT);\nповернути 201 Created і DTO заявки")
    draw_arrow(ax, 3.4, 2.35, 3.4, 2.07, "Так", 3.55, 2.18)

    ax.plot([8.8, 8.95], [5.85, 5.85], color="#0F172A", lw=1.3)
    ax.plot([8.8, 8.95], [2.8, 2.8], color="#0F172A", lw=1.3)
    ax.plot([8.95, 8.95], [1.0, 5.85], color="#0F172A", lw=1.3)
    draw_arrow(ax, 8.95, 1.0, 3.4, 1.0)

    term_end = FancyBboxPatch((2.1, 0.25), 2.6, 0.52, boxstyle="round,pad=0.02,rounding_size=0.25",
                              facecolor="#FFFFFF", edgecolor="#0F172A", lw=1.4)
    ax.add_patch(term_end)
    ax.text(3.4, 0.51, "Кінець", ha="center", va="center", fontweight="bold")
    draw_arrow(ax, 3.4, 1.35, 3.4, 0.77)

    save_fig(fig, "fig_2_2_flowchart_atomic")

# ==============================================================================
# 4. Карта станів інтерфейсу (Рисунок 3.1, за зразком Д.4)
# ==============================================================================
def make_ui_state_map():
    fig, ax = plt.subplots(figsize=(9.5, 8.5))
    ax.set_xlim(0, 9.5)
    ax.set_ylim(0, 9.0)
    ax.axis("off")

    draw_box(ax, 0.8, 7.8, 3.6, 0.75, "UI-01: Каталог обладнання\nпошук, фільтр категорії та періоду", bold=True, bg="#F8FAFC")
    draw_box(ax, 0.8, 6.2, 3.6, 0.8, "UI-02: Картка позиції та\nкалендар фізичних екземплярів", bold=True, bg="#F8FAFC")
    draw_arrow(ax, 2.6, 7.8, 2.6, 7.0, "обрати позицію", 2.75, 7.38)

    draw_box(ax, 5.5, 6.2, 3.3, 0.8, "UI-06: Вхід до системи\nвибір облікового запису", bold=True, bg="#FEF3C7")
    draw_arrow(ax, 4.4, 6.75, 5.5, 6.75, "потрібен вхід", 4.6, 6.88)
    draw_arrow(ax, 5.5, 6.4, 4.4, 6.4, "повернення до слота", 4.5, 6.15)

    draw_box(ax, 0.8, 4.5, 3.6, 0.85, "UI-03: Форма бронювання\nвибір екземпляра, інтервалу, мети", bold=True, bg="#F8FAFC")
    draw_arrow(ax, 2.6, 6.2, 2.6, 5.35, "сесію перевірено", 2.75, 5.75)

    draw_box(ax, 0.8, 2.8, 3.6, 0.85, "Надсилання POST /api/bookings\nатомарна перевірка на сервері", bg="#EFF6FF")
    draw_arrow(ax, 2.6, 4.5, 2.6, 3.65, "підтвердити", 2.75, 4.05)

    draw_box(ax, 5.5, 2.8, 3.4, 0.9, "Стан помилки / Конфлікт 409\nпояснення причини без втрати полів", bg="#FEE2E2")
    draw_arrow(ax, 4.4, 3.22, 5.5, 3.22, "відмова 400/409", 4.55, 3.35)
    draw_arrow(ax, 7.2, 3.7, 7.2, 4.9)
    ax.plot([7.2, 4.4], [4.9, 4.9], color="#0F172A", lw=1.3)
    draw_arrow(ax, 5.0, 4.9, 4.4, 4.9, "виправити інтервал", 5.2, 5.05)

    draw_box(ax, 5.5, 0.9, 3.4, 0.95, "Запис у чергу очікування (Waitlist)\nPOST /api/waitlist → стан WAITING", bg="#FEF3C7")
    draw_arrow(ax, 7.2, 2.8, 7.2, 1.85, "при 409 INTERVAL_CONFLICT", 7.3, 2.3)

    draw_box(ax, 0.8, 0.9, 3.6, 0.95, "UI-04 / UI-05: Мої бронювання\nта панель менеджера (статус, події)", bold=True, bg="#DCFCE7")
    draw_arrow(ax, 2.6, 2.8, 2.6, 1.85, "201 Created", 2.75, 2.3)

    save_fig(fig, "fig_3_1_ui_state_map")

# ==============================================================================
# 5. Структурна схема вебсистеми (Logical View, Рисунок 3.2, за зразком Д.5)
# ==============================================================================
def make_logical_view():
    fig, ax = plt.subplots(figsize=(8.5, 7.8))
    ax.set_xlim(0, 8.5)
    ax.set_ylim(0, 8.0)
    ax.axis("off")

    draw_box(ax, 2.2, 6.8, 4.1, 0.8, "Користувач вебсистеми\n(Гість, Клієнт або Менеджер прокату)", bold=True, bg="#F8FAFC")
    draw_box(ax, 1.8, 5.2, 4.9, 0.9, "Клієнтський застосунок у браузері (React 19 SPA)\nКаталог, календар доступності, калькулятор, кабінети", bg="#EFF6FF")
    draw_arrow(ax, 4.25, 6.8, 4.25, 6.1, "Дія в інтерфейсі / Відображення стану", 4.4, 6.42)

    # Довірена серверна межа
    trust_rect = patches.Rectangle((0.9, 2.2), 6.7, 2.1, fill=False, edgecolor="#1E3A8A", lw=1.6, linestyle="--")
    ax.add_patch(trust_rect)
    ax.text(4.25, 4.05, "Довірена серверна частина (ASP.NET Core 10.0 Web API)",
            ha="center", va="center", fontweight="bold", color="#1E3A8A")

    draw_box(ax, 1.3, 2.45, 5.9, 1.3,
             "RentalApiController → RentalApplicationService → PricingAndAvailabilityRules\n"
             "Автентифікація сесії (HttpOnly Cookie), перевірка прав доступу й власника,\n"
             "розрахунок вартості у копійках, контроль перетину інтервалів і тех. перерв",
             bg="#FFFFFF")
    draw_arrow(ax, 4.25, 5.2, 4.25, 3.75, "HTTP/HTTPS JSON API (контракти DTO та RFC 9457)", 4.4, 4.65)

    draw_box(ax, 1.8, 0.5, 4.9, 1.0,
             "Приватне реляційне сховище даних (SQLite 3 WAL)\n"
             "Таблиці, зовнішні ключі, обмеження CHECK, транзакції, історія подій",
             bold=True, bg="#F0FDF4")
    draw_arrow(ax, 4.25, 2.45, 4.25, 1.5, "Параметризовані SQL-запити та BEGIN IMMEDIATE (Microsoft.Data.Sqlite)", 4.4, 1.88)

    save_fig(fig, "fig_3_2_logical_view")

# ==============================================================================
# 6. UML Deployment View (Рисунок 3.3, за зразком Д.6)
# ==============================================================================
def make_deployment_view():
    fig, ax = plt.subplots(figsize=(8.8, 7.6))
    ax.set_xlim(0, 9.0)
    ax.set_ylim(0, 7.8)
    ax.axis("off")

    # Вузол клієнта
    node1 = patches.Rectangle((1.0, 5.4), 7.0, 1.9, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.5)
    ax.add_patch(node1)
    ax.text(4.5, 7.02, "«device» Клієнтський пристрій користувача (ПК / Планшет / Смартфон)",
            ha="center", va="center", fontweight="bold")
    draw_box(ax, 1.8, 5.65, 5.4, 1.05,
             "«executionEnvironment» Веббраузер (Microsoft Edge / Chrome / Firefox)\n"
             "Артефакт: Клієнтський бандл React 19 + CSS Grid (порт 5173 / 5080)", bg="#FFFFFF")

    # Вузол сервера
    node2 = patches.Rectangle((1.0, 0.5), 7.0, 3.9, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.5)
    ax.add_patch(node2)
    ax.text(4.5, 4.12, "«node» Сервер застосунку / Навчальний стенд автора (Windows 11 x64)",
            ha="center", va="center", fontweight="bold")

    draw_box(ax, 1.6, 2.55, 5.8, 1.25,
             "«executionEnvironment» Середовище .NET 10.0 Runtime (Kestrel HTTP Server)\n"
             "Артефакти: EquipmentRental.WebApi.dll, Application.dll, Domain.dll, Infrastructure.dll\n"
             "Порт: http://localhost:5080 (конфігурація через змінні середовища)", bg="#FFFFFF")

    draw_box(ax, 1.6, 0.8, 5.8, 1.15,
             "«executionEnvironment» Реляційна СКБД SQLite 3 (режим журналювання WAL)\n"
             "Файл БД: Data/equipment_rental.db • Схема: sql/init.sql • Дані: sql/seed.sql", bg="#F0FDF4")

    draw_arrow(ax, 4.5, 5.4, 4.5, 3.8, "HTTP / HTTPS (REST JSON, Cookie equiprent_session)", 4.65, 4.8)
    draw_arrow(ax, 4.5, 2.55, 4.5, 1.95, "Внутрішнє з'єднання ADO.NET (Microsoft.Data.Sqlite)", 4.65, 2.22)

    save_fig(fig, "fig_3_3_deployment_view")

# ==============================================================================
# 7. Подання шарів і компонентів (Design View, Рисунок 3.4, за зразком Д.7)
# ==============================================================================
def make_design_layers():
    fig, ax = plt.subplots(figsize=(8.8, 7.6))
    ax.set_xlim(0, 9.0)
    ax.set_ylim(0, 7.8)
    ax.axis("off")

    draw_box(ax, 1.0, 6.1, 6.2, 1.15,
             "Шар подання (Presentation Layer — WebApi & React SPA)\n"
             "RentalApiController, SessionAuthManager, React-компоненти UI-01..UI-06, вхідні/вихідні DTO",
             bold=True, bg="#EFF6FF")

    draw_box(ax, 1.0, 4.3, 6.2, 1.15,
             "Прикладний шар (Application Layer — EquipmentRental.Application)\n"
             "RentalApplicationService, координація сценаріїв каталогу, календаря, попереднього розрахунку",
             bold=True, bg="#F8FAFC")

    draw_box(ax, 1.0, 2.5, 6.2, 1.15,
             "Шар предметних правил (Domain Layer — EquipmentRental.Domain)\n"
             "Сутності (EquipmentType, EquipmentUnit, Booking, Tariff, WaitlistEntry),\n"
             "PricingAndAvailabilityRules, Money (точні копійки), контракт IRentalRepository",
             bold=True, bg="#FEF3C7")

    draw_box(ax, 1.0, 0.6, 6.2, 1.15,
             "Інфраструктурний шар (Infrastructure Layer — EquipmentRental.Infrastructure)\n"
             "SqliteRentalRepository (транзакції BEGIN IMMEDIATE, параметризований SQL), PasswordHasher (PBKDF2)",
             bold=True, bg="#DCFCE7")

    draw_arrow(ax, 4.1, 6.1, 4.1, 5.45, "виклик сценарію", 4.25, 5.75)
    draw_arrow(ax, 4.1, 4.3, 4.1, 3.65, "перевірка інваріантів і правил", 4.25, 3.95)
    draw_arrow(ax, 4.1, 1.75, 4.1, 2.5, "реалізує IRentalRepository", 4.25, 2.08, dashed=True)

    # Бічна лінія звернення прикладного шару до інфраструктури через контракт
    ax.plot([7.2, 8.1], [4.85, 4.85], color="#0F172A", lw=1.3)
    ax.plot([8.1, 8.1], [1.18, 4.85], color="#0F172A", lw=1.3)
    draw_arrow(ax, 8.1, 1.18, 7.2, 1.18)
    ax.text(8.2, 3.0, "через інтерфейс\nIRentalRepository", fontsize=9.5, rotation=90, va="center")

    save_fig(fig, "fig_3_4_design_layers")

# ==============================================================================
# 8. UML Sequence Diagram (Process View, Рисунок 3.5, за зразком Д.8)
# ==============================================================================
def make_sequence_diagram():
    fig, ax = plt.subplots(figsize=(10.2, 8.8))
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 9.2)
    ax.axis("off")

    participants = [
        (1.3, "Браузер\n(React SPA)"),
        (3.8, "API Контролер\n(RentalApiController)"),
        (6.4, "Прикладний сервіс /\nДоменні правила"),
        (9.0, "Репозиторій та\nСКБД SQLite")
    ]

    for px, title in participants:
        draw_box(ax, px - 1.0, 8.2, 2.0, 0.72, title, bold=True, bg="#F1F5F9", fontsize=9.5)
        ax.plot([px, px], [0.4, 8.2], color="#64748B", lw=1.1, linestyle="--")

    draw_arrow(ax, 1.3, 7.6, 3.8, 7.6, "1: POST /api/bookings (unitId, startsAt, endsAt, purpose)", 1.45, 7.72)
    draw_arrow(ax, 3.8, 7.0, 6.4, 7.0, "2: Перевірка сесії, формату дат і виклик сценарію", 3.95, 7.12)
    draw_arrow(ax, 6.4, 6.4, 9.0, 6.4, "3: CreateBookingAtomic() -> BEGIN IMMEDIATE", 6.55, 6.52)
    draw_arrow(ax, 9.0, 5.75, 6.4, 5.75, "4: ValidateAndCheckAvailability(unit, tariff, activeBookings)", 4.6, 5.87)

    # Рамка alt
    alt_rect = patches.Rectangle((0.5, 0.7), 9.4, 4.6, fill=False, edgecolor="#0F172A", lw=1.4)
    ax.add_patch(alt_rect)
    ax.plot([0.5, 1.3, 1.5, 1.5], [4.95, 4.95, 5.1, 5.3], color="#0F172A", lw=1.3)
    ax.text(0.95, 5.12, "alt", fontweight="bold", fontsize=10)

    ax.text(1.7, 5.05, "[екземпляр доступний і перетин інтервалів та тех. перерв відсутній]", fontweight="bold", fontsize=9.5, color="#14532D")
    draw_arrow(ax, 6.4, 4.5, 9.0, 4.5, "5a: INSERT INTO bookings & rental_events; COMMIT", 6.5, 4.62)
    draw_arrow(ax, 9.0, 3.9, 3.8, 3.9, "6a: створений запис Booking (PENDING)", 5.2, 4.02, dashed=True)
    draw_arrow(ax, 3.8, 3.35, 1.3, 3.35, "7a: 201 Created (BookingResponseDto)", 1.6, 3.47, dashed=True)

    # Роздільник alt
    ax.plot([0.5, 9.9], [2.9, 2.9], color="#0F172A", lw=1.2, linestyle="--")
    ax.text(1.7, 2.62, "[виявлено накладання активної оренди або технічної перерви]", fontweight="bold", fontsize=9.5, color="#7F1D1D")
    draw_arrow(ax, 9.0, 2.1, 3.8, 2.1, "5b: ROLLBACK; DomainRuleException(INTERVAL_CONFLICT)", 4.4, 2.22, dashed=True)
    draw_arrow(ax, 3.8, 1.55, 1.3, 1.55, "6b: 409 Conflict (Problem Details + блок Waitlist)", 1.5, 1.67, dashed=True)
    draw_arrow(ax, 1.3, 0.95, 3.8, 0.95, "7b (опційно): POST /api/waitlist -> запис у чергу очікування", 1.45, 1.07)

    save_fig(fig, "fig_3_5_sequence_booking")

# ==============================================================================
# 9. ER-модель даних (Data View, Рисунок 3.6, за зразком Д.9)
# ==============================================================================
def make_er_diagram():
    fig, ax = plt.subplots(figsize=(11.0, 8.2))
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 8.4)
    ax.axis("off")

    def draw_entity(x, y, w, h, title, fields):
        rect = patches.Rectangle((x, y), w, h, facecolor="#FFFFFF", edgecolor="#0F172A", lw=1.5)
        ax.add_patch(rect)
        hdr = patches.Rectangle((x, y + h - 0.45), w, 0.45, facecolor="#E2E8F0", edgecolor="#0F172A", lw=1.2)
        ax.add_patch(hdr)
        ax.text(x + w / 2, y + h - 0.22, title, ha="center", va="center", fontweight="bold", fontsize=10)
        ax.text(x + 0.12, y + h - 0.58, fields, ha="left", va="top", fontsize=8.8, family="monospace")

    draw_entity(0.4, 6.0, 3.1, 2.0, "tariffs — тарифи",
                "PK id : TEXT\n   code : TEXT UNIQUE\n   name : TEXT\n   billing_unit : HOUR|DAY\n   rate_minor : INTEGER\n   deposit_minor : INTEGER\n   late_fee_per_hour_minor")

    draw_entity(4.1, 5.8, 3.3, 2.2, "equipment_types — типи",
                "PK id : TEXT\nFK tariff_id : TEXT\n   slug : TEXT UNIQUE\n   title, category : TEXT\n   brand_model : TEXT\n   maintenance_buffer_hours\n   active : INTEGER")

    draw_entity(8.0, 6.0, 2.9, 2.0, "users — користувачі",
                "PK id : TEXT\n   email : TEXT UNIQUE\n   full_name : TEXT\n   phone : TEXT\n   role : CLIENT|MANAGER\n   password_hash : TEXT\n   created_at : TEXT")

    draw_entity(0.4, 2.9, 3.1, 2.1, "equipment_units — екземпляри",
                "PK id : TEXT\nFK equipment_type_id : TEXT\n   inventory_code : UNIQUE\n   serial_number : UNIQUE\n   condition_status : TEXT\n   warehouse_location : TEXT\n   notes : TEXT")

    draw_entity(4.1, 2.3, 3.4, 2.8, "bookings — бронювання",
                "PK id : TEXT\n   booking_number : UNIQUE\nFK unit_id : TEXT\nFK client_user_id : TEXT\nFK tariff_id : TEXT\n   starts_at, ends_at : TEXT\n   buffer_ends_at : TEXT\n   status : PENDING..RETURNED\n   billed_units, total_price_minor\n   late_hours, late_fee_minor\n   version : INTEGER")

    draw_entity(8.1, 3.1, 2.8, 2.0, "waitlist_entries — черга",
                "PK id : TEXT\nFK equipment_type_id : TEXT\nFK preferred_unit_id : TEXT\nFK client_user_id : TEXT\n   desired_starts_at : TEXT\n   desired_ends_at : TEXT\n   status : WAITING|NOTIFIED")

    draw_entity(4.1, 0.2, 3.4, 1.5, "rental_events — події",
                "PK id : TEXT\nFK booking_id : TEXT\nFK actor_user_id : TEXT\n   event_type, new_status\n   occurred_at, penalty_added_minor")

    # Зв'язки та кратності
    ax.plot([3.5, 4.1], [7.0, 7.0], color="#0F172A", lw=1.3)
    ax.text(3.6, 7.1, "1", fontsize=9.5, fontweight="bold")
    ax.text(3.88, 7.1, "0..*", fontsize=9.5, fontweight="bold")

    ax.plot([4.1, 1.95], [6.4, 6.4], color="#0F172A", lw=0) # dummy
    ax.plot([4.1, 3.75, 3.75, 1.95, 1.95], [6.3, 6.3, 5.4, 5.4, 5.0], color="#0F172A", lw=1.3)
    ax.text(3.85, 6.4, "1", fontsize=9.5, fontweight="bold")
    ax.text(2.05, 5.1, "1..*", fontsize=9.5, fontweight="bold")

    ax.plot([3.5, 4.1], [3.9, 3.9], color="#0F172A", lw=1.3)
    ax.text(3.6, 4.0, "1", fontsize=9.5, fontweight="bold")
    ax.text(3.85, 4.0, "0..*", fontsize=9.5, fontweight="bold")

    ax.plot([8.0, 7.75, 7.75, 7.5], [6.8, 6.8, 4.4, 4.4], color="#0F172A", lw=1.3)
    ax.text(7.8, 6.9, "1", fontsize=9.5, fontweight="bold")
    ax.text(7.52, 4.5, "0..*", fontsize=9.5, fontweight="bold")

    ax.plot([5.8, 5.8], [2.3, 1.7], color="#0F172A", lw=1.3)
    ax.text(5.9, 2.1, "1", fontsize=9.5, fontweight="bold")
    ax.text(5.9, 1.78, "1..*", fontsize=9.5, fontweight="bold")

    ax.plot([7.4, 8.1], [6.3, 4.8], color="#0F172A", lw=1.2)
    ax.text(7.45, 6.35, "1", fontsize=9.5, fontweight="bold")
    ax.text(7.85, 4.95, "0..*", fontsize=9.5, fontweight="bold")

    save_fig(fig, "fig_3_6_er_diagram")

# ==============================================================================
# 10. Діаграма основних доменних класів та DTO (Рисунки 3.7, 3.8, 4.1)
# ==============================================================================
def make_domain_and_impl_diagrams():
    # Рисунок 3.7 — Доменні класи
    fig, ax = plt.subplots(figsize=(9.6, 6.8))
    ax.set_xlim(0, 9.8)
    ax.set_ylim(0, 7.0)
    ax.axis("off")

    draw_box(ax, 0.4, 4.4, 2.8, 2.1,
             "EquipmentType\n────────────────────\n+ Id: string\n+ Title: string\n+ MaintenanceBufferHours: int\n+ Active: bool",
             bg="#FFFFFF", fontsize=9.5)
    draw_box(ax, 3.6, 4.4, 2.8, 2.1,
             "EquipmentUnit\n────────────────────\n+ Id: string\n+ InventoryCode: string\n+ ConditionStatus: UnitStatus\n+ WarehouseLocation: string",
             bg="#FFFFFF", fontsize=9.5)
    draw_box(ax, 6.8, 4.4, 2.6, 2.1,
             "Tariff\n────────────────────\n+ BillingUnit: HOUR | DAY\n+ RateMinor: long\n+ DepositMinor: long\n+ LateFeePerHourMinor: long",
             bg="#FFFFFF", fontsize=9.5)

    draw_box(ax, 0.4, 1.0, 4.2, 2.4,
             "Booking\n────────────────────────────────\n+ Id, BookingNumber, UnitId: string\n+ StartsAt, EndsAt, BufferEndsAt: DateTimeOffset\n+ Status: BookingStatus\n+ BilledUnits: int, TotalPriceMinor: long\n────────────────────────────────\n+ IsActiveInCalendar(): bool",
             bg="#EFF6FF", fontsize=9.5)

    draw_box(ax, 5.2, 1.0, 4.2, 2.4,
             "PricingAndAvailabilityRules\n────────────────────────────────\n+ IntervalsOverlap(aStart, aBuf, bStart, bBuf): bool\n+ CalculatePrice(start, end, tariff, buf): Result\n+ ValidateAndCheckAvailability(...): CheckResult\n+ CalculateLateReturnPenalty(...): (int, long)\n+ ValidateStatusTransition(...): void",
             bg="#FEF3C7", fontsize=9.5)

    ax.plot([3.2, 3.6], [5.4, 5.4], color="#0F172A", lw=1.3)
    ax.text(3.25, 5.5, "1", fontweight="bold", fontsize=9)
    ax.text(3.42, 5.5, "1..*", fontweight="bold", fontsize=9)

    ax.plot([5.0, 2.5], [4.4, 3.4], color="#0F172A", lw=1.3)
    ax.plot([4.6, 5.2], [2.2, 2.2], color="#0F172A", lw=1.3, linestyle="--")

    save_fig(fig, "fig_3_7_domain_classes")

    # Рисунок 3.8 — Структури передавання даних (DTO)
    fig2, ax2 = plt.subplots(figsize=(9.4, 5.8))
    ax2.set_xlim(0, 9.6)
    ax2.set_ylim(0, 6.0)
    ax2.axis("off")

    draw_box(ax2, 0.4, 3.2, 4.1, 2.3,
             "«DTO» CreateBookingRequestDto\n─────────────────────────────\n+ unitId: string [Required]\n+ startsAt: string (ISO-8601)\n+ endsAt: string (ISO-8601)\n+ purpose: string [5..300]\n(clientUserId береться із сесії!)",
             bg="#F8FAFC", fontsize=9.5)

    draw_box(ax2, 5.0, 3.2, 4.2, 2.3,
             "«DTO» BookingResponseDto\n─────────────────────────────\n+ id, bookingNumber, inventoryCode\n+ startsAt, endsAt, bufferEndsAt\n+ status, billedUnits, totalPriceFormatted\n+ lateHours, lateFeeFormatted, version\n+ events: RentalEventDto[]",
             bg="#EFF6FF", fontsize=9.5)

    draw_box(ax2, 2.3, 0.4, 5.0, 2.2,
             "«DTO» ApiErrorResponse (RFC 9457 Problem Details)\n─────────────────────────────────────────\n+ type: string (URI проблеми)\n+ title, detail: string\n+ status: int (400 / 401 / 403 / 404 / 409)\n+ code: string, traceId: string\n+ fieldErrors: FieldErrorDto[]",
             bg="#FEE2E2", fontsize=9.5)

    save_fig(fig2, "fig_3_8_dto_contracts")

    # Рисунок 4.1 — Ключові класи реалізації
    fig3, ax3 = plt.subplots(figsize=(7.8, 8.2))
    ax3.set_xlim(0, 8.0)
    ax3.set_ylim(0, 8.5)
    ax3.axis("off")

    draw_box(ax3, 1.3, 6.8, 5.4, 1.2,
             "RentalApiController (EquipmentRental.WebApi)\n────────────────────────────────────────\n+ GetCatalog(...): ActionResult<IReadOnlyList<EquipmentTypeDto>>\n+ CreateBooking(request): ActionResult<BookingResponseDto>",
             bg="#EFF6FF", fontsize=9.5)

    draw_box(ax3, 1.3, 4.7, 5.4, 1.25,
             "RentalApplicationService (EquipmentRental.Application)\n────────────────────────────────────────\n+ GetCatalog(...): IReadOnlyList<EquipmentTypeDto>\n+ PreviewAvailabilityAndPrice(...): AvailabilityPreviewResponseDto",
             bg="#F8FAFC", fontsize=9.5)

    draw_box(ax3, 1.3, 2.5, 5.4, 1.35,
             "«interface» IRentalRepository (EquipmentRental.Domain)\n────────────────────────────────────────\n+ CreateBookingAtomic(clientId, unitId, startsAt, endsAt, ...): Booking\n+ ReturnEquipmentAtomic(bookingId, mgrId, notes, returnedAt): Booking\n+ AddWaitlistEntry(...): WaitlistEntry",
             bg="#FEF3C7", fontsize=9.5)

    draw_box(ax3, 1.3, 0.4, 5.4, 1.25,
             "SqliteRentalRepository (EquipmentRental.Infrastructure)\n────────────────────────────────────────\nРеалізує контракт збереження на базі Microsoft.Data.Sqlite,\nтранзакції BEGIN IMMEDIATE та оповіщення черги очікування",
             bg="#DCFCE7", fontsize=9.5)

    draw_arrow(ax3, 4.0, 6.8, 4.0, 5.95, "використовує", 4.15, 6.35, dashed=True)
    draw_arrow(ax3, 4.0, 4.7, 4.0, 3.85, "залежить від", 4.15, 4.25, dashed=True)
    draw_arrow(ax3, 4.0, 1.65, 4.0, 2.5, "реалізація контракту", 4.15, 2.05, dashed=True)

    save_fig(fig3, "fig_4_1_implementation_classes")

# ==============================================================================
# 11. Графіки експериментів обсягу даних та навантаження (Рисунок 5.1)
# ==============================================================================
def make_benchmarks_chart():
    results_path = os.path.join(root_dir, "evidence", "test_results.json")
    with open(results_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    vol = data["volumeBenchmarks"]
    load = data["loadBenchmarks"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.6))

    # Лівий графік: Тестування обсягом даних (100, 1 000, 10 000 записів)
    labels_v = [str(r["DatasetBookingsCount"]) for r in vol]
    idx_vals = [r["AtomicBookingCheckMs"] for r in vol]
    noidx_vals = [r["WithoutIndexCheckMs"] for r in vol]

    x = range(len(labels_v))
    w = 0.34
    b1 = ax1.bar([i - w / 2 for i in x], idx_vals, width=w, label="З індексом idx_bookings_unit_interval", color="#1D4ED8", edgecolor="#0F172A")
    b2 = ax1.bar([i + w / 2 for i in x], noidx_vals, width=w, label="Без складеного індексу (Повний перегляд)", color="#F59E0B", edgecolor="#0F172A")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels([f"{n} записів" for n in labels_v])
    ax1.set_ylabel("Час перевірки інтервалу та вартості, мс")
    ax1.set_title("а) Вплив обсягу даних та індексації (Д.2.3 / Д.5.7)", fontweight="bold", fontsize=11)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    ax1.legend(fontsize=9)
    for bar in list(b1) + list(b2):
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, h + 0.4, f"{h:.2f}", ha="center", va="bottom", fontsize=8.5)
    ax1.set_ylim(0, max(noidx_vals) * 1.22)

    # Правий графік: Навантажувальне тестування (5, 10, 25 VU)
    labels_l = [f"{r['VirtualUsers']} VU" for r in load]
    p50_vals = [r["P50Ms"] for r in load]
    p95_vals = [r["P95Ms"] for r in load]
    p99_vals = [r["P99Ms"] for r in load]

    xl = range(len(labels_l))
    wl = 0.25
    ax2.bar([i - wl for i in xl], p50_vals, width=wl, label="p50 (медіана, мс)", color="#10B981", edgecolor="#0F172A")
    ax2.bar(list(xl), p95_vals, width=wl, label="p95 (95-й перцентиль, мс)", color="#3B82F6", edgecolor="#0F172A")
    ax2.bar([i + wl for i in xl], p99_vals, width=wl, label="p99 (99-й перцентиль, мс)", color="#EF4444", edgecolor="#0F172A")
    ax2.set_xticks(list(xl))
    ax2.set_xticklabels(labels_l)
    ax2.set_ylabel("Час відповіді сценарію, мс")
    ax2.set_title("б) Затримки p50 / p95 / p99 під навантаженням (Д.5.6)", fontweight="bold", fontsize=11)
    ax2.grid(axis="y", linestyle="--", alpha=0.5)
    ax2.legend(fontsize=9)
    ax2.set_ylim(0, max(p99_vals) * 1.25)

    fig.tight_layout()
    save_fig(fig, "fig_5_1_benchmarks")

if __name__ == "__main__":
    make_use_case()
    make_flowchart_request()
    make_flowchart_atomic()
    make_ui_state_map()
    make_logical_view()
    make_deployment_view()
    make_design_layers()
    make_sequence_diagram()
    make_er_diagram()
    make_domain_and_impl_diagrams()
    make_benchmarks_chart()
    print("All diagrams generated successfully!")
