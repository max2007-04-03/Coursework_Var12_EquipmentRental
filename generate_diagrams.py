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


def draw_box(ax, x, y, w, h, text, bold=False, bg="#FFFFFF", ec="#0F172A", lw=1.3, fontsize=10.0, align="center"):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.01,rounding_size=0.01",
        facecolor=bg, edgecolor=ec, linewidth=lw
    )
    ax.add_patch(rect)
    tx = x + w / 2 if align == "center" else x + 0.14
    ha = "center" if align == "center" else "left"
    ax.text(
        tx, y + h / 2, text,
        ha=ha, va="center", fontsize=fontsize,
        fontweight="bold" if bold else "normal",
        color="#000000", linespacing=1.25
    )


def draw_uml_box(ax, x, y, w, h, title, body_lines, footer_lines=None, bg="#FFFFFF", hdr_bg="#F1F5F9", fontsize=9.5):
    """Малює UML-блок класу або DTO з горизонтальними лініями-розділювачами всередині рамки."""
    rect = patches.Rectangle((x, y), w, h, facecolor=bg, edgecolor="#0F172A", linewidth=1.4)
    ax.add_patch(rect)

    hdr_h = 0.46 if "\n" not in title else 0.64
    hdr = patches.Rectangle((x, y + h - hdr_h), w, hdr_h, facecolor=hdr_bg, edgecolor="#0F172A", linewidth=1.2)
    ax.add_patch(hdr)
    ax.text(
        x + w / 2, y + h - hdr_h / 2, title,
        ha="center", va="center", fontweight="bold", fontsize=fontsize + 0.3, color="#000000", linespacing=1.15
    )

    if footer_lines:
        ftr_h = 0.42 + 0.22 * (len(footer_lines) - 1)
        div_y = y + ftr_h
        ax.plot([x, x + w], [div_y, div_y], color="#0F172A", lw=1.1)
        body_center_y = y + ftr_h + (h - hdr_h - ftr_h) / 2
        ax.text(
            x + 0.14, body_center_y, "\n".join(body_lines),
            ha="left", va="center", fontsize=fontsize, color="#000000", linespacing=1.25
        )
        ax.text(
            x + 0.14, y + ftr_h / 2, "\n".join(footer_lines),
            ha="left", va="center", fontsize=fontsize, color="#000000", linespacing=1.22
        )
    else:
        body_center_y = y + (h - hdr_h) / 2
        ax.text(
            x + 0.14, body_center_y, "\n".join(body_lines),
            ha="left", va="center", fontsize=fontsize, color="#000000", linespacing=1.28
        )


def draw_diamond(ax, cx, cy, w, h, text, fontsize=9.6):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    poly = patches.Polygon(pts, closed=True, facecolor="#FFFFFF", edgecolor="#0F172A", linewidth=1.4)
    ax.add_patch(poly)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fontsize, color="#0F172A", linespacing=1.18)


def draw_arrow(ax, x1, y1, x2, y2, label=None, lx=None, ly=None, dashed=False, ha="left", bg_label=False):
    ls = "--" if dashed else "-"
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color="#0F172A", lw=1.3, linestyle=ls, mutation_scale=13)
    )
    if label:
        tx = lx if lx is not None else (x1 + x2) / 2 + 0.05
        ty = ly if ly is not None else (y1 + y2) / 2
        bbox_cfg = dict(boxstyle="round,pad=0.12", facecolor="white", edgecolor="none") if bg_label else None
        ax.text(tx, ty, label, fontsize=9.3, color="#0F172A", fontweight="bold", ha=ha, va="center", bbox=bbox_cfg)


# ==============================================================================
# 1. UML Use Case Diagram (Рисунок 1.1)
# ==============================================================================
def make_use_case():
    fig, ax = plt.subplots(figsize=(10.2, 7.4))
    ax.set_xlim(0, 10.2)
    ax.set_ylim(0, 7.6)
    ax.axis("off")

    # Межа системи
    sys_rect = patches.Rectangle((2.15, 0.55), 5.9, 6.65, fill=False, edgecolor="#0F172A", linewidth=1.6)
    ax.add_patch(sys_rect)
    ax.text(
        5.1, 6.92, "Вебсистема оренди обладнання з календарем доступності",
        ha="center", va="center", fontsize=11.2, fontweight="bold"
    )

    use_cases = [
        (5.1, 6.15, "UC-01: Переглянути каталог і календар\nдоступності фізичних екземплярів"),
        (5.1, 5.20, "UC-02: Розрахувати вартість оренди,\nзаставу та межу технічної перерви"),
        (5.1, 4.25, "UC-03: Створити заявку на оренду\nобраного фізичного екземпляра"),
        (5.1, 3.30, "UC-04: Стати в чергу очікування (Waitlist)\nпри зайнятості екземпляра"),
        (5.1, 2.35, "UC-05: Продовжити або скасувати\nвласне активне бронювання"),
        (5.1, 1.40, "UC-06: Погодити/відхилити заявку, оформити\nвидачу та повернення з обліком прострочення"),
    ]

    for cx, cy, label in use_cases:
        ell = patches.Ellipse((cx, cy), 4.95, 0.74, facecolor="#F8FAFC", edgecolor="#0F172A", linewidth=1.3)
        ax.add_patch(ell)
        ax.text(cx, cy, label, ha="center", va="center", fontsize=9.5, linespacing=1.18)

    def draw_actor(ax, x, y, name):
        head = patches.Circle((x, y + 0.46), 0.16, fill=False, edgecolor="#0F172A", lw=1.5)
        ax.add_patch(head)
        ax.plot([x, x], [y + 0.30, y - 0.08], color="#0F172A", lw=1.5)
        ax.plot([x - 0.25, x + 0.25], [y + 0.18, y + 0.18], color="#0F172A", lw=1.5)
        ax.plot([x, x - 0.22], [y - 0.08, y - 0.40], color="#0F172A", lw=1.5)
        ax.plot([x, x + 0.22], [y - 0.08, y - 0.40], color="#0F172A", lw=1.5)
        ax.text(x, y - 0.72, name, ha="center", va="center", fontsize=10.2, fontweight="bold", linespacing=1.15)

    draw_actor(ax, 0.9, 5.75, "Гість")
    draw_actor(ax, 0.9, 3.25, "Клієнт\n(Орендар)")
    draw_actor(ax, 9.3, 2.85, "Менеджер\nпрокату")

    # Лінії асоціацій
    ax.plot([1.22, 2.63], [5.75, 6.15], color="#0F172A", lw=1.2)
    ax.plot([1.22, 2.63], [5.75, 5.20], color="#0F172A", lw=1.2)

    for target_y in [6.15, 5.20, 4.25, 3.30, 2.35]:
        ax.plot([1.22, 2.63], [3.25, target_y], color="#0F172A", lw=1.2)

    for target_y in [6.15, 4.25, 3.30, 2.35, 1.40]:
        ax.plot([8.98, 7.57], [2.85, target_y], color="#0F172A", lw=1.2)

    ax.text(
        5.1, 0.22,
        "Лінії позначають участь акторів у прецедентах (UML Use Case), а не порядок виконання.",
        ha="center", va="center", fontsize=9.5, style="italic"
    )
    save_fig(fig, "fig_1_1_use_case")


# ==============================================================================
# 2. Блок-схема перевірки запиту на бронювання (Рисунок 2.1, за зразком Д.2)
# ==============================================================================
def make_flowchart_request():
    fig, ax = plt.subplots(figsize=(9.0, 10.5))
    ax.set_xlim(0, 9.2)
    ax.set_ylim(0, 11.0)
    ax.axis("off")

    term_start = FancyBboxPatch(
        (2.1, 10.1), 2.6, 0.55,
        boxstyle="round,pad=0.02,rounding_size=0.25",
        facecolor="#FFFFFF", edgecolor="#0F172A", lw=1.4
    )
    ax.add_patch(term_start)
    ax.text(3.4, 10.37, "Початок", ha="center", va="center", fontweight="bold")

    draw_box(ax, 1.4, 9.0, 4.0, 0.72, "Отримати unitId, startsAt, endsAt,\npurpose та перевірену сесію")
    draw_arrow(ax, 3.4, 10.1, 3.4, 9.72)

    draw_diamond(ax, 3.4, 7.85, 4.0, 1.02, "Є дійсна сесія та\nправо створення?")
    draw_arrow(ax, 3.4, 9.0, 3.4, 8.36)
    draw_box(ax, 6.0, 7.5, 2.6, 0.7, "Повернути 401 / 403\n(Problem Details)")
    draw_arrow(ax, 5.4, 7.85, 6.0, 7.85, "Ні", 5.55, 8.02)

    draw_diamond(ax, 3.4, 6.3, 4.0, 1.02, "Формат полів коректний,\nendsAt > startsAt?")
    draw_arrow(ax, 3.4, 7.34, 3.4, 6.81, "Так", 3.55, 7.06)
    draw_box(ax, 6.0, 5.95, 2.6, 0.7, "Повернути 400\nEND_BEFORE_START")
    draw_arrow(ax, 5.4, 6.3, 6.0, 6.3, "Ні", 5.55, 6.47)

    draw_diamond(ax, 3.4, 4.75, 4.0, 1.02, "Екземпляр AVAILABLE,\nтривалість у межах тарифу?")
    draw_arrow(ax, 3.4, 5.79, 3.4, 5.26, "Так", 3.55, 5.51)
    draw_box(ax, 6.0, 4.4, 2.6, 0.7, "Повернути 400 / 404\nкеровану відмову")
    draw_arrow(ax, 5.4, 4.75, 6.0, 4.75, "Ні", 5.55, 4.92)

    # Підпрограма (подвійні вертикальні лінії за ГОСТ/ДСТУ)
    draw_box(
        ax, 1.3, 3.08, 4.2, 0.88,
        "Атомарне створення бронювання,\nрозрахунок вартості й запис історії\n(окрема блок-схема рис. 2.2)",
        fontsize=9.6
    )
    ax.plot([1.52, 1.52], [3.08, 3.96], color="#0F172A", lw=1.3)
    ax.plot([5.28, 5.28], [3.08, 3.96], color="#0F172A", lw=1.3)
    draw_arrow(ax, 3.4, 4.24, 3.4, 3.96, "Так", 3.55, 4.09)

    draw_box(ax, 1.4, 1.8, 4.0, 0.75, "Повернути результат клієнтові:\n201 Created / 409 Conflict / помилка")
    draw_arrow(ax, 3.4, 3.08, 3.4, 2.55)

    # Єдина чиста шина об'єднання правих блоків відмов із виходом
    for ry in [7.85, 6.3, 4.75]:
        ax.plot([8.6, 8.85], [ry, ry], color="#0F172A", lw=1.3)
    ax.plot([8.85, 8.85], [1.35, 7.85], color="#0F172A", lw=1.3)
    draw_arrow(ax, 8.85, 1.35, 3.4, 1.35)

    term_end = FancyBboxPatch(
        (2.1, 0.55), 2.6, 0.55,
        boxstyle="round,pad=0.02,rounding_size=0.25",
        facecolor="#FFFFFF", edgecolor="#0F172A", lw=1.4
    )
    ax.add_patch(term_end)
    ax.text(3.4, 0.82, "Кінець", ha="center", va="center", fontweight="bold")
    draw_arrow(ax, 3.4, 1.8, 3.4, 1.1)

    save_fig(fig, "fig_2_1_flowchart_request")


# ==============================================================================
# 3. Блок-схема атомарного створення бронювання (Рисунок 2.2, за зразком Д.3)
# ==============================================================================
def make_flowchart_atomic():
    fig, ax = plt.subplots(figsize=(9.2, 10.6))
    ax.set_xlim(0, 9.4)
    ax.set_ylim(0, 10.8)
    ax.axis("off")

    term_start = FancyBboxPatch(
        (2.1, 9.85), 2.6, 0.52,
        boxstyle="round,pad=0.02,rounding_size=0.25",
        facecolor="#FFFFFF", edgecolor="#0F172A", lw=1.4
    )
    ax.add_patch(term_start)
    ax.text(3.4, 10.11, "Початок", ha="center", va="center", fontweight="bold")

    draw_box(ax, 1.35, 8.75, 4.1, 0.68, "Почати транзакцію СКБД\n(BEGIN IMMEDIATE TRANSACTION)")
    draw_arrow(ax, 3.4, 9.85, 3.4, 9.43)

    draw_box(
        ax, 1.15, 7.42, 4.5, 0.88,
        "Обчислити bufferEndsAt = endsAt + Δt_buf;\nвибрати активні бронювання екземпляра\n(PENDING, CONFIRMED, ISSUED)"
    )
    draw_arrow(ax, 3.4, 8.75, 3.4, 8.30)

    # Збільшений ромб, щоб усі 3 рядки тексту були строго всередині контуру
    draw_diamond(
        ax, 3.4, 5.90, 4.7, 1.38,
        "Перетин інтервалів відсутній:\nstartsAt < B.bufferEndsAt та\nB.startsAt < bufferEndsAt ?",
        fontsize=9.2
    )
    draw_arrow(ax, 3.4, 7.42, 3.4, 6.59)

    draw_box(ax, 6.25, 5.50, 2.7, 0.80, "Відкотити транзакцію;\nповернути 409 Conflict\n(INTERVAL_CONFLICT)", fontsize=9.6)
    draw_arrow(ax, 5.75, 5.90, 6.25, 5.90, "Ні", 5.86, 6.06)

    draw_box(
        ax, 1.15, 4.02, 4.5, 0.88,
        "Обчислити billedUnits = ceil(Δt / U),\nbasePriceMinor, depositMinor;\nвставити запис у bookings та rental_events"
    )
    draw_arrow(ax, 3.4, 5.21, 3.4, 4.90, "Так", 3.55, 5.04)

    draw_diamond(ax, 3.4, 2.75, 4.0, 1.00, "Запис у сховище\nвиконано успішно?", fontsize=9.6)
    draw_arrow(ax, 3.4, 4.02, 3.4, 3.25)

    draw_box(ax, 6.25, 2.35, 2.7, 0.80, "Відкотити транзакцію\n(ROLLBACK); повернути\nкеровану помилку", fontsize=9.6)
    draw_arrow(ax, 5.4, 2.75, 6.25, 2.75, "Ні", 5.65, 2.91)

    draw_box(ax, 1.35, 1.30, 4.1, 0.72, "Зафіксувати транзакцію (COMMIT);\nповернути 201 Created і DTO заявки")
    draw_arrow(ax, 3.4, 2.25, 3.4, 2.02, "Так", 3.55, 2.12)

    ax.plot([8.95, 9.15], [5.90, 5.90], color="#0F172A", lw=1.3)
    ax.plot([8.95, 9.15], [2.75, 2.75], color="#0F172A", lw=1.3)
    ax.plot([9.15, 9.15], [0.98, 5.90], color="#0F172A", lw=1.3)
    draw_arrow(ax, 9.15, 0.98, 3.4, 0.98)

    term_end = FancyBboxPatch(
        (2.1, 0.22), 2.6, 0.52,
        boxstyle="round,pad=0.02,rounding_size=0.25",
        facecolor="#FFFFFF", edgecolor="#0F172A", lw=1.4
    )
    ax.add_patch(term_end)
    ax.text(3.4, 0.48, "Кінець", ha="center", va="center", fontweight="bold")
    draw_arrow(ax, 3.4, 1.30, 3.4, 0.74)

    save_fig(fig, "fig_2_2_flowchart_atomic")


# ==============================================================================
# 4. Карта станів інтерфейсу (Рисунок 3.1, за зразком Д.4)
# ==============================================================================
def make_ui_state_map():
    fig, ax = plt.subplots(figsize=(10.6, 8.6))
    ax.set_xlim(0, 10.8)
    ax.set_ylim(0, 9.0)
    ax.axis("off")

    # Ліва колонка: x=0.5, w=3.9 (правий край = 4.4)
    # Права колонка: x=6.3, w=4.0 (лівий край = 6.3, проміжок = 1.9!)
    draw_box(ax, 0.5, 7.8, 3.9, 0.80, "UI-01: Каталог обладнання\nпошук, фільтр категорії та періоду", bold=True, bg="#F8FAFC")
    draw_box(ax, 0.5, 6.15, 3.9, 0.82, "UI-02: Картка позиції та\nкалендар фізичних екземплярів", bold=True, bg="#F8FAFC")
    draw_arrow(ax, 2.45, 7.8, 2.45, 6.97, "обрати позицію", 2.62, 7.38)

    draw_box(ax, 6.3, 6.15, 4.0, 0.82, "UI-06: Вхід до системи\nвибір облікового запису (сесії)", bold=True, bg="#FEF3C7")
    draw_arrow(ax, 4.4, 6.72, 6.3, 6.72, "потрібен вхід", 5.35, 6.92, ha="center")
    draw_arrow(ax, 6.3, 6.38, 4.4, 6.38, "повернення до слота", 5.35, 6.14, ha="center")

    draw_box(ax, 0.5, 4.45, 3.9, 0.85, "UI-03: Форма бронювання\nвибір екземпляра, інтервалу, мети", bold=True, bg="#F8FAFC")
    draw_arrow(ax, 2.45, 6.15, 2.45, 5.30, "сесію перевірено", 2.62, 5.72)

    draw_box(ax, 0.5, 2.75, 3.9, 0.85, "Надсилання POST /api/bookings\nатомарна перевірка на сервері", bg="#EFF6FF")
    draw_arrow(ax, 2.45, 4.45, 2.45, 3.60, "підтвердити", 2.62, 4.02)

    draw_box(ax, 6.3, 2.75, 4.0, 0.88, "Стан помилки / Конфлікт 409\nпояснення причини без втрати полів", bg="#FEE2E2")
    draw_arrow(ax, 4.4, 3.18, 6.3, 3.18, "відмова 400 / 409", 5.35, 3.38, ha="center")

    # Лінія повернення до форми для виправлення інтервалу
    ax.plot([8.3, 8.3], [3.63, 4.88], color="#0F172A", lw=1.3)
    draw_arrow(ax, 8.3, 4.88, 4.4, 4.88, "виправити інтервал", 6.35, 5.08, ha="center")

    draw_box(ax, 6.3, 0.85, 4.0, 0.92, "Запис у чергу очікування (Waitlist)\nPOST /api/waitlist → стан WAITING", bg="#FEF3C7")
    draw_arrow(ax, 8.3, 2.75, 8.3, 1.77, "при 409 INTERVAL_CONFLICT", 8.45, 2.26)

    draw_box(ax, 0.5, 0.85, 3.9, 0.92, "UI-04 / UI-05: Мої бронювання\nта панель менеджера (статус, події)", bold=True, bg="#DCFCE7")
    draw_arrow(ax, 2.45, 2.75, 2.45, 1.77, "201 Created", 2.62, 2.26)

    save_fig(fig, "fig_3_1_ui_state_map")


# ==============================================================================
# 5. Структурна схема вебсистеми (Logical View, Рисунок 3.2, за зразком Д.5)
# ==============================================================================
def make_logical_view():
    fig, ax = plt.subplots(figsize=(9.6, 8.0))
    ax.set_xlim(0, 9.6)
    ax.set_ylim(0, 8.2)
    ax.axis("off")

    draw_box(
        ax, 2.1, 6.95, 5.4, 0.82,
        "Користувач вебсистеми\n(Гість, Клієнт або Менеджер прокату)",
        bold=True, bg="#F8FAFC", fontsize=10.2
    )
    draw_box(
        ax, 1.3, 5.30, 7.0, 0.92,
        "Клієнтський застосунок у браузері (React 19 SPA)\n"
        "Каталог позицій, поекземплярний календар доступності, калькулятор, кабінети",
        bg="#EFF6FF", fontsize=9.8
    )
    draw_arrow(ax, 4.8, 6.95, 4.8, 6.22, "Дія в інтерфейсі / Відображення стану", 4.98, 6.58)

    # Довірена серверна межа
    trust_rect = patches.Rectangle((0.6, 2.15), 8.4, 2.28, fill=False, edgecolor="#1E3A8A", lw=1.6, linestyle="--")
    ax.add_patch(trust_rect)
    ax.text(
        0.80, 4.18, "Довірена серверна межа (ASP.NET Core 10.0)",
        ha="left", va="center", fontweight="bold", color="#1E3A8A", fontsize=9.8
    )

    draw_box(
        ax, 1.0, 2.38, 7.6, 1.50,
        "Маршрутизація та бізнес-логіка: RentalApiController → RentalApplicationService →\n"
        "PricingAndAvailabilityRules (шар предметних правил Domain)\n"
        "Перевірка сесії (HttpOnly Cookie), ролі та власника заявки, розрахунок вартості\n"
        "у цілих копійках, контроль перетину інтервалів із буфером ТО",
        bg="#FFFFFF", fontsize=9.5
    )
    draw_arrow(ax, 4.8, 5.30, 4.8, 3.88, "HTTP / HTTPS JSON API (контракти DTO та RFC 9457)", 4.98, 4.76)

    draw_box(
        ax, 1.1, 0.45, 7.4, 1.02,
        "Приватне реляційне сховище даних (СКБД SQLite 3 у режимі WAL)\n"
        "7 таблиць, зовнішні ключі, обмеження CHECK, транзакції та історія подій",
        bold=True, bg="#F0FDF4", fontsize=9.8
    )
    draw_arrow(
        ax, 4.8, 2.38, 4.8, 1.47,
        "Параметризовані SQL-запити та BEGIN IMMEDIATE (Microsoft.Data.Sqlite)", 4.98, 1.82
    )

    save_fig(fig, "fig_3_2_logical_view")


# ==============================================================================
# 6. UML Deployment View (Рисунок 3.3, за зразком Д.6)
# ==============================================================================
def make_deployment_view():
    fig, ax = plt.subplots(figsize=(9.8, 7.8))
    ax.set_xlim(0, 9.8)
    ax.set_ylim(0, 8.0)
    ax.axis("off")

    # Вузол клієнта
    node1 = patches.Rectangle((0.6, 5.45), 8.6, 2.05, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.5)
    ax.add_patch(node1)
    ax.text(
        4.9, 7.20, "«device» Клієнтський пристрій користувача (ПК / Планшет / Смартфон)",
        ha="center", va="center", fontweight="bold", fontsize=10.4
    )
    draw_box(
        ax, 1.1, 5.70, 7.6, 1.18,
        "«executionEnvironment» Веббраузер (Microsoft Edge / Chrome / Firefox)\n"
        "Артефакт: Клієнтський бандл React 19 SPA + адаптивні стилі CSS Grid\n"
        "Взаємодія через захищені сесійні реп'яшки (HttpOnly Cookie)",
        bg="#FFFFFF", fontsize=9.6
    )

    # Вузол сервера
    node2 = patches.Rectangle((0.6, 0.45), 8.6, 4.05, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.5)
    ax.add_patch(node2)
    ax.text(
        0.85, 4.22, "«node» Сервер застосунку / Навчальний стенд автора (ОС Windows 11 x64)",
        ha="left", va="center", fontweight="bold", fontsize=10.0
    )

    draw_box(
        ax, 1.1, 2.62, 7.6, 1.32,
        "«executionEnvironment» Середовище .NET 10.0 Runtime (Kestrel HTTP Server)\n"
        "Артефакти: EquipmentRental.WebApi.dll, Application.dll, Domain.dll, Infrastructure.dll\n"
        "Мережевий порт: http://localhost:5080 (конфігурація через змінні середовища)",
        bg="#FFFFFF", fontsize=9.5
    )

    draw_box(
        ax, 1.1, 0.72, 7.6, 1.22,
        "«executionEnvironment» Реляційна СКБД SQLite 3 (режим журналювання WAL)\n"
        "Артефакти сховища: файл БД Data/equipment_rental.db,\n"
        "DDL-схема sql/init.sql (7 таблиць, 7 індексів) • Початкові дані sql/seed.sql",
        bg="#F0FDF4", fontsize=9.5
    )

    draw_arrow(
        ax, 4.9, 5.45, 4.9, 4.50,
        "HTTP / HTTPS (REST JSON, Cookie equiprent_session)", 5.08, 4.96, bg_label=True
    )
    draw_arrow(
        ax, 4.9, 2.62, 4.9, 1.94,
        "Локальне з'єднання ADO.NET (Microsoft.Data.Sqlite)", 5.08, 2.28, bg_label=True
    )

    save_fig(fig, "fig_3_3_deployment_view")


# ==============================================================================
# 7. Подання шарів і компонентів (Design View, Рисунок 3.4, за зразком Д.7)
# ==============================================================================
def make_design_layers():
    fig, ax = plt.subplots(figsize=(10.0, 8.0))
    ax.set_xlim(0, 10.2)
    ax.set_ylim(0, 8.2)
    ax.axis("off")

    # 4 широкі блоки (x=0.5, w=7.5 -> правий край 8.0), усі написи суворо всередині рамок
    draw_box(
        ax, 0.5, 6.45, 7.5, 1.32,
        "Шар подання (Presentation Layer — EquipmentRental.WebApi & React 19 SPA)\n"
        "Контролер RentalApiController, менеджер сесій SessionAuthManager,\n"
        "екрани інтерфейсу UI-01..UI-06, формування відповідей за стандартом RFC 9457",
        bold=True, bg="#EFF6FF", fontsize=9.5
    )

    draw_box(
        ax, 0.5, 4.50, 7.5, 1.32,
        "Прикладний шар (Application Layer — EquipmentRental.Application)\n"
        "Сервіс RentalApplicationService, координація сценаріїв каталогу, календаря\n"
        "доступності, попереднього розрахунку вартості та трансформація контрактів DTO",
        bold=True, bg="#F8FAFC", fontsize=9.5
    )

    draw_box(
        ax, 0.5, 2.55, 7.5, 1.32,
        "Шар предметних правил (Domain Layer — EquipmentRental.Domain)\n"
        "Сутності (EquipmentType, EquipmentUnit, Booking, Tariff, WaitlistEntry),\n"
        "правила PricingAndAvailabilityRules, тип Money (копійки), контракт IRentalRepository",
        bold=True, bg="#FEF3C7", fontsize=9.5
    )

    draw_box(
        ax, 0.5, 0.55, 7.5, 1.32,
        "Інфраструктурний шар (Infrastructure Layer — EquipmentRental.Infrastructure)\n"
        "Репозиторій SqliteRentalRepository (транзакції BEGIN IMMEDIATE,\n"
        "параметризовані SQL-запити, оповіщення Waitlist), криптографія PasswordHasher (PBKDF2)",
        bold=True, bg="#DCFCE7", fontsize=9.5
    )

    draw_arrow(ax, 4.25, 6.45, 4.25, 5.82, "виклик прикладного сценарію", 4.42, 6.13)
    draw_arrow(ax, 4.25, 4.50, 4.25, 3.87, "перевірка інваріантів і правил", 4.42, 4.18)
    draw_arrow(ax, 4.25, 1.87, 4.25, 2.55, "реалізує контракт IRentalRepository", 4.42, 2.20, dashed=True)

    # Бічна лінія та примітка (як на Рисунку Д.7 методички, с. 57)
    ax.plot([8.0, 9.0], [5.16, 5.16], color="#0F172A", lw=1.3)
    ax.plot([9.0, 9.0], [1.21, 5.16], color="#0F172A", lw=1.3)
    draw_arrow(ax, 9.0, 1.21, 8.0, 1.21)
    ax.text(
        9.45, 3.18,
        "Прикладний шар звертається\nдо інфраструктурних адаптерів\nчерез визначений у Domain\nконтракт IRentalRepository",
        fontsize=9.2, ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#F8FAFC", edgecolor="#64748B", lw=1.0)
    )

    save_fig(fig, "fig_3_4_design_layers")


# ==============================================================================
# 8. UML Sequence Diagram (Process View, Рисунок 3.5, за зразком Д.8)
# ==============================================================================
def make_sequence_diagram():
    fig, ax = plt.subplots(figsize=(11.0, 9.0))
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 9.3)
    ax.axis("off")

    participants = [
        (1.35, "Браузер клієнта\n(React 19 SPA)"),
        (4.10, "API Контролер\n(RentalApiController)"),
        (6.95, "Прикладний сервіс /\nДоменні правила"),
        (9.75, "Репозиторій та\nСКБД SQLite (WAL)")
    ]

    for px, title in participants:
        draw_box(ax, px - 1.15, 8.25, 2.3, 0.75, title, bold=True, bg="#F1F5F9", fontsize=9.4)
        ax.plot([px, px], [0.4, 8.25], color="#64748B", lw=1.1, linestyle="--")

    draw_arrow(
        ax, 1.35, 7.65, 4.10, 7.65,
        "1: POST /api/bookings (unitId, startsAt, endsAt)", 2.72, 7.86, ha="center", bg_label=True
    )
    draw_arrow(
        ax, 4.10, 7.05, 6.95, 7.05,
        "2: Перевірка сесії, дат і виклик сценарію", 5.52, 7.26, ha="center", bg_label=True
    )
    draw_arrow(
        ax, 6.95, 6.45, 9.75, 6.45,
        "3: CreateBookingAtomic() -> BEGIN IMMEDIATE", 8.35, 6.66, ha="center", bg_label=True
    )
    draw_arrow(
        ax, 9.75, 5.80, 6.95, 5.80,
        "4: ValidateAndCheckAvailability(unit, tariff, bookings)", 8.35, 6.01, ha="center", bg_label=True
    )

    # Рамка alt
    alt_rect = patches.Rectangle((0.45, 0.65), 10.3, 4.70, fill=False, edgecolor="#0F172A", lw=1.4)
    ax.add_patch(alt_rect)
    ax.plot([0.45, 1.25, 1.45, 1.45], [4.98, 4.98, 5.15, 5.35], color="#0F172A", lw=1.3)
    ax.text(0.88, 5.16, "alt", fontweight="bold", fontsize=10)

    ax.text(
        1.70, 5.10,
        "[екземпляр доступний і перетин інтервалів та тех. перерв відсутній]",
        fontweight="bold", fontsize=9.4, color="#14532D",
        bbox=dict(boxstyle="round,pad=0.1", facecolor="white", edgecolor="none")
    )
    draw_arrow(
        ax, 6.95, 4.50, 9.75, 4.50,
        "5a: INSERT INTO bookings & rental_events; COMMIT", 8.35, 4.71, ha="center", bg_label=True
    )
    draw_arrow(
        ax, 9.75, 3.88, 4.10, 3.88,
        "6a: створений агрегат Booking (статус PENDING)", 6.92, 4.09, dashed=True, ha="center", bg_label=True
    )
    draw_arrow(
        ax, 4.10, 3.30, 1.35, 3.30,
        "7a: HTTP 201 Created (BookingResponseDto)", 2.72, 3.51, dashed=True, ha="center", bg_label=True
    )

    # Роздільник alt
    ax.plot([0.45, 10.75], [2.85, 2.85], color="#0F172A", lw=1.2, linestyle="--")
    ax.text(
        1.70, 2.58,
        "[виявлено накладання активної оренди або технічної перерви]",
        fontweight="bold", fontsize=9.4, color="#7F1D1D",
        bbox=dict(boxstyle="round,pad=0.1", facecolor="white", edgecolor="none")
    )
    draw_arrow(
        ax, 9.75, 2.05, 4.10, 2.05,
        "5b: ROLLBACK; виняток INTERVAL_CONFLICT", 6.92, 2.26, dashed=True, ha="center", bg_label=True
    )
    draw_arrow(
        ax, 4.10, 1.48, 1.35, 1.48,
        "6b: HTTP 409 Conflict (Problem Details + Waitlist)", 2.72, 1.69, dashed=True, ha="center", bg_label=True
    )
    draw_arrow(
        ax, 1.35, 0.88, 4.10, 0.88,
        "7b (опційно): POST /api/waitlist -> запис у чергу", 2.72, 1.09, ha="center", bg_label=True
    )

    save_fig(fig, "fig_3_5_sequence_booking")


# ==============================================================================
# 9. ER-модель даних (Data View, Рисунок 3.6, за зразком Д.9)
# ==============================================================================
def make_er_diagram():
    fig, ax = plt.subplots(figsize=(11.6, 8.5))
    ax.set_xlim(0, 11.8)
    ax.set_ylim(0, 8.6)
    ax.axis("off")

    def draw_entity(x, y, w, h, title, fields):
        rect = patches.Rectangle((x, y), w, h, facecolor="#FFFFFF", edgecolor="#0F172A", lw=1.5)
        ax.add_patch(rect)
        hdr = patches.Rectangle((x, y + h - 0.45), w, 0.45, facecolor="#E2E8F0", edgecolor="#0F172A", lw=1.2)
        ax.add_patch(hdr)
        ax.text(x + w / 2, y + h - 0.22, title, ha="center", va="center", fontweight="bold", fontsize=9.8)
        ax.text(x + 0.12, y + h - 0.56, fields, ha="left", va="top", fontsize=8.4, family="monospace", linespacing=1.22)

    draw_entity(
        0.3, 6.1, 3.25, 2.1, "tariffs — тарифи",
        "PK id : TEXT\n   code : TEXT UNIQUE\n   name : TEXT\n   billing_unit : HOUR|DAY\n   rate_minor : INTEGER\n   deposit_minor : INTEGER\n   late_fee_per_hour_minor"
    )

    draw_entity(
        4.15, 5.9, 3.45, 2.3, "equipment_types — типи",
        "PK id : TEXT\nFK tariff_id : TEXT\n   slug : TEXT UNIQUE\n   title, category : TEXT\n   brand_model : TEXT\n   maintenance_buffer_hours\n   active : INTEGER"
    )

    draw_entity(
        8.25, 6.1, 3.25, 2.1, "users — користувачі",
        "PK id : TEXT\n   email : TEXT UNIQUE\n   full_name : TEXT\n   phone : TEXT\n   role : CLIENT|MANAGER\n   password_hash : TEXT\n   created_at : TEXT"
    )

    draw_entity(
        0.3, 2.85, 3.25, 2.15, "equipment_units — екземпляри",
        "PK id : TEXT\nFK equipment_type_id : TEXT\n   inventory_code : UNIQUE\n   serial_number : UNIQUE\n   condition_status : TEXT\n   warehouse_location : TEXT\n   notes : TEXT"
    )

    draw_entity(
        4.15, 2.25, 3.55, 2.85, "bookings — бронювання",
        "PK id : TEXT\n   booking_number : UNIQUE\nFK unit_id : TEXT\nFK client_user_id : TEXT\nFK tariff_id : TEXT\n   starts_at, ends_at : TEXT\n   buffer_ends_at : TEXT\n   status : PENDING..RETURNED\n   billed_units : INTEGER\n   total_price_minor : INT\n   late_hours, late_fee_minor\n   version : INTEGER"
    )

    draw_entity(
        8.25, 2.95, 3.25, 2.15, "waitlist_entries — черга",
        "PK id : TEXT\nFK equipment_type_id : TEXT\nFK preferred_unit_id : TEXT\nFK client_user_id : TEXT\n   desired_starts_at : TEXT\n   desired_ends_at : TEXT\n   status : WAITING|NOTIFIED"
    )

    draw_entity(
        4.15, 0.05, 3.55, 1.72, "rental_events — події",
        "PK id : TEXT\nFK booking_id : TEXT\nFK actor_user_id : TEXT\n   event_type, new_status\n   occurred_at : TEXT\n   penalty_added_minor : INT"
    )

    # Ортогональні лінії зв'язків та кратності
    # tariffs (1) --- (0..*) equipment_types
    ax.plot([3.55, 4.15], [7.15, 7.15], color="#0F172A", lw=1.3)
    ax.text(3.63, 7.25, "1", fontsize=9.2, fontweight="bold")
    ax.text(3.85, 7.25, "0..*", fontsize=9.2, fontweight="bold")

    # equipment_types (1) --- (1..*) equipment_units
    ax.plot([4.15, 3.80, 3.80, 1.92, 1.92], [6.40, 6.40, 5.45, 5.45, 5.00], color="#0F172A", lw=1.3)
    ax.text(3.90, 6.50, "1", fontsize=9.2, fontweight="bold")
    ax.text(2.02, 5.10, "1..*", fontsize=9.2, fontweight="bold")

    # equipment_units (1) --- (0..*) bookings
    ax.plot([3.55, 4.15], [3.90, 3.90], color="#0F172A", lw=1.3)
    ax.text(3.63, 4.00, "1", fontsize=9.2, fontweight="bold")
    ax.text(3.85, 4.00, "0..*", fontsize=9.2, fontweight="bold")

    # users (1) --- (0..*) bookings (через вільний коридор y=5.52 у верхню межу bookings x=6.85)
    ax.plot([8.25, 7.80, 7.80, 6.85, 6.85], [6.90, 6.90, 5.52, 5.52, 5.10], color="#0F172A", lw=1.3)
    ax.text(8.02, 7.02, "1", fontsize=9.0, fontweight="bold")
    ax.text(6.95, 5.20, "0..*", fontsize=9.0, fontweight="bold")

    # bookings (1) --- (1..*) rental_events
    ax.plot([5.92, 5.92], [2.25, 1.77], color="#0F172A", lw=1.3)
    ax.text(6.02, 2.06, "1", fontsize=9.2, fontweight="bold")
    ax.text(6.02, 1.83, "1..*", fontsize=9.2, fontweight="bold")

    # equipment_types (1) --- (0..*) waitlist_entries (входить у ліву стінку waitlist_entries на y=3.85)
    ax.plot([7.60, 8.02, 8.02, 8.25], [6.25, 6.25, 3.85, 3.85], color="#0F172A", lw=1.2)
    ax.text(7.66, 6.36, "1", fontsize=9.0, fontweight="bold")
    ax.text(7.85, 3.55, "0..*", fontsize=9.0, fontweight="bold")

    # users (1) --- (0..*) waitlist_entries
    ax.plot([9.85, 9.85], [6.10, 5.10], color="#0F172A", lw=1.2)
    ax.text(9.95, 5.90, "1", fontsize=9.2, fontweight="bold")
    ax.text(9.95, 5.20, "0..*", fontsize=9.2, fontweight="bold")

    save_fig(fig, "fig_3_6_er_diagram")


# ==============================================================================
# 10. Діаграма основних доменних класів, DTO та реалізації (Рисунки 3.7, 3.8, 4.1)
# ==============================================================================
def make_domain_and_impl_diagrams():
    # --------------------------------------------------------------------------
    # Рисунок 3.7 — Доменні класи (за зразком Д.10, с. 63)
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10.8, 7.2))
    ax.set_xlim(0, 11.0)
    ax.set_ylim(0, 7.4)
    ax.axis("off")

    draw_uml_box(
        ax, 0.3, 4.6, 3.1, 2.3,
        "EquipmentType",
        [
            "+ Id: string",
            "+ Title, Category: string",
            "+ TariffId: string",
            "+ MaintenanceBufferHours: int",
            "+ Active: bool"
        ],
        bg="#FFFFFF", hdr_bg="#E2E8F0", fontsize=9.2
    )

    draw_uml_box(
        ax, 4.1, 4.6, 3.1, 2.3,
        "EquipmentUnit",
        [
            "+ Id, EquipmentTypeId: string",
            "+ InventoryCode: string",
            "+ SerialNumber: string",
            "+ ConditionStatus: UnitStatus",
            "+ WarehouseLocation: string"
        ],
        bg="#FFFFFF", hdr_bg="#E2E8F0", fontsize=9.2
    )

    draw_uml_box(
        ax, 7.9, 4.6, 2.8, 2.3,
        "Tariff",
        [
            "+ Id, Code: string",
            "+ BillingUnit: HOUR | DAY",
            "+ RateMinor: long",
            "+ DepositMinor: long",
            "+ LateFeePerHourMinor: long"
        ],
        bg="#FFFFFF", hdr_bg="#E2E8F0", fontsize=9.2
    )

    draw_uml_box(
        ax, 0.3, 0.7, 4.5, 2.8,
        "Booking",
        [
            "+ Id, BookingNumber, UnitId, ClientUserId: string",
            "+ StartsAt, EndsAt, BufferEndsAt: DateTimeOffset",
            "+ Status: BookingStatus (PENDING..RETURNED)",
            "+ BilledUnits: int, TotalPriceMinor: long",
            "+ LateHours: int, LateFeeMinor: long, Version: int"
        ],
        footer_lines=["+ IsActiveInCalendar(): bool"],
        bg="#EFF6FF", hdr_bg="#DBEAFE", fontsize=9.0
    )

    draw_uml_box(
        ax, 5.85, 0.7, 4.85, 2.8,
        "PricingAndAvailabilityRules",
        [
            "+ IntervalsOverlap(aStart, aBuf, bStart, bBuf): bool",
            "+ CalculatePrice(start, end, tariff, buf): Result",
            "+ ValidateAndCheckAvailability(...): CheckResult",
            "+ CalculateLateReturnPenalty(...): (int, long)",
            "+ ValidateStatusTransition(current, target): void"
        ],
        bg="#FEF3C7", hdr_bg="#FDE68A", fontsize=9.0
    )

    # Зв'язки між доменними класами
    # EquipmentType (1) --- (1..*) EquipmentUnit
    ax.plot([3.4, 4.1], [5.75, 5.75], color="#0F172A", lw=1.3)
    ax.text(3.48, 5.86, "1", fontweight="bold", fontsize=9.2)
    ax.text(3.78, 5.86, "1..*", fontweight="bold", fontsize=9.2)

    # EquipmentType (0..*) --- (1) Tariff (через верхню шину)
    ax.plot([1.85, 1.85, 9.3, 9.3], [6.9, 7.22, 7.22, 6.9], color="#0F172A", lw=1.2)
    ax.text(1.95, 6.98, "0..*", fontweight="bold", fontsize=9.0)
    ax.text(9.38, 6.98, "1", fontweight="bold", fontsize=9.0)

    # EquipmentUnit (1) --- (0..*) Booking (ортогонально)
    ax.plot([5.1, 5.1, 2.55, 2.55], [4.6, 4.05, 4.05, 3.5], color="#0F172A", lw=1.3)
    ax.text(5.18, 4.38, "1", fontweight="bold", fontsize=9.2)
    ax.text(2.65, 3.62, "0..*", fontweight="bold", fontsize=9.2)

    # Залежність Booking від правил домену
    draw_arrow(ax, 5.85, 2.1, 4.8, 2.1, dashed=True)
    ax.text(5.32, 2.30, "перевіряє", fontsize=8.8, ha="center", style="italic")

    save_fig(fig, "fig_3_7_domain_classes")

    # --------------------------------------------------------------------------
    # Рисунок 3.8 — Структури передавання даних DTO (за зразком Д.11, с. 64)
    # із показом зв'язку з контрактом маршруту API та вкладеними DTO
    # --------------------------------------------------------------------------
    fig2, ax2 = plt.subplots(figsize=(10.8, 7.0))
    ax2.set_xlim(0, 11.0)
    ax2.set_ylim(0, 7.2)
    ax2.axis("off")

    # Верхній ряд: 3 головні структури DTO (відповідають Рисунку Д.11 методички)
    draw_uml_box(
        ax2, 0.3, 4.25, 3.25, 2.55,
        "«DTO»\nCreateBookingRequestDto",
        [
            "+ unitId: string [Required]",
            "+ startsAt: string (ISO-8601)",
            "+ endsAt: string (ISO-8601)",
            "+ purpose: string [5..300]",
            "(clientUserId із сесії!)"
        ],
        bg="#F8FAFC", hdr_bg="#E2E8F0", fontsize=9.0
    )

    draw_uml_box(
        ax2, 3.85, 4.25, 3.35, 2.55,
        "«DTO»\nBookingResponseDto",
        [
            "+ id, bookingNumber, unitId",
            "+ startsAt, endsAt, bufferEndsAt",
            "+ status, billedUnits, version",
            "+ totalPriceFormatted: string",
            "+ lateHours, lateFeeFormatted",
            "+ events: RentalEventDto[]"
        ],
        bg="#EFF6FF", hdr_bg="#DBEAFE", fontsize=8.9
    )

    draw_uml_box(
        ax2, 7.50, 4.25, 3.20, 2.55,
        "«DTO»\nApiErrorResponse (RFC 9457)",
        [
            "+ type: string (URI проблеми)",
            "+ title, detail: string",
            "+ status: int (400/401/403/409)",
            "+ code, traceId: string",
            "+ fieldErrors: FieldErrorDto[]"
        ],
        bg="#FEE2E2", hdr_bg="#FECACA", fontsize=8.9
    )

    # Нижній ряд: контракт операції API та вкладені структури DTO
    draw_box(
        ax2, 0.3, 1.35, 3.25, 1.75,
        "Контракт операції REST API\nPOST /api/bookings\n\n"
        "• Вхід: CreateBookingRequestDto\n"
        "• Успіх 201: BookingResponseDto\n"
        "• Відмова 4xx: ApiErrorResponse",
        bold=False, bg="#F0FDF4", fontsize=8.9
    )

    draw_uml_box(
        ax2, 3.85, 1.35, 3.35, 1.75,
        "«DTO» RentalEventDto",
        [
            "+ id, eventType: string",
            "+ oldStatus, newStatus: string",
            "+ occurredAt, notes: string",
            "+ penaltyAddedFormatted: string"
        ],
        bg="#FFFFFF", hdr_bg="#E2E8F0", fontsize=8.8
    )

    draw_uml_box(
        ax2, 7.50, 1.35, 3.20, 1.75,
        "«DTO» FieldErrorDto",
        [
            "+ field: string (назва поля)",
            "+ message: string (опис помилки)"
        ],
        bg="#FFFFFF", hdr_bg="#E2E8F0", fontsize=8.8
    )

    # Стрілки зв'язків та композиції вкладених DTO
    draw_arrow(ax2, 1.92, 4.25, 1.92, 3.10, "вхідне тіло JSON", 2.04, 3.68, dashed=True)
    draw_arrow(ax2, 5.52, 4.25, 5.52, 3.10, "містить 1..* подій", 5.64, 3.68)
    draw_arrow(ax2, 9.10, 4.25, 9.10, 3.10, "містить 0..* полів", 9.22, 3.68)

    # Примітка за зразком Рисунка Д.11 (с. 64 методички)
    draw_box(
        ax2, 0.3, 0.20, 10.4, 0.72,
        "Примітка (за Д.3.7): Запит не визначає власника — clientUserId отримують із перевіреної серверної сесії.\n"
        "Структури передавання даних (DTO) описують контракти HTTP-обміну і не є схемою зберігання таблиць у СКБД.",
        bg="#FEFCE8", fontsize=9.0
    )

    save_fig(fig2, "fig_3_8_dto_contracts")

    # --------------------------------------------------------------------------
    # Рисунок 4.1 — Ключові класи реалізації (за зразком Д.12, с. 75)
    # --------------------------------------------------------------------------
    fig3, ax3 = plt.subplots(figsize=(9.2, 8.4))
    ax3.set_xlim(0, 9.4)
    ax3.set_ylim(0, 8.6)
    ax3.axis("off")

    draw_uml_box(
        ax3, 0.8, 6.85, 7.8, 1.35,
        "RentalApiController (шар EquipmentRental.WebApi)",
        [
            "+ GetCatalog(search, category, ...): ActionResult<IReadOnlyList<EquipmentTypeDto>>",
            "+ CreateBooking(request): ActionResult<BookingResponseDto>",
            "+ ReturnBooking(id, request): ActionResult<BookingResponseDto>"
        ],
        bg="#EFF6FF", hdr_bg="#DBEAFE", fontsize=9.1
    )

    draw_uml_box(
        ax3, 0.8, 4.70, 7.8, 1.35,
        "RentalApplicationService (шар EquipmentRental.Application)",
        [
            "+ GetCatalog(...): IReadOnlyList<EquipmentTypeDto>",
            "+ GetEquipmentCalendar(typeId, from, to): EquipmentCalendarResponseDto",
            "+ PreviewAvailabilityAndPrice(request): AvailabilityPreviewResponseDto"
        ],
        bg="#F8FAFC", hdr_bg="#E2E8F0", fontsize=9.1
    )

    draw_uml_box(
        ax3, 0.8, 2.50, 7.8, 1.40,
        "«interface» IRentalRepository (шар EquipmentRental.Domain)",
        [
            "+ CreateBookingAtomic(clientId, unitId, startsAt, endsAt, purpose): Booking",
            "+ ReturnEquipmentAtomic(bookingId, managerId, notes, returnedAt): Booking",
            "+ AddWaitlistEntry(clientId, typeId, unitId, start, end, note): WaitlistEntry"
        ],
        bg="#FEF3C7", hdr_bg="#FDE68A", fontsize=9.1
    )

    draw_uml_box(
        ax3, 0.8, 0.35, 7.8, 1.35,
        "SqliteRentalRepository (шар EquipmentRental.Infrastructure)",
        [
            "Реалізує контракт IRentalRepository на базі драйвера Microsoft.Data.Sqlite:",
            "виконує транзакції BEGIN IMMEDIATE, параметризовані SQL-запити та",
            "автоматичне оповіщення черги очікування RefreshWaitlistForUnitInternal()"
        ],
        bg="#DCFCE7", hdr_bg="#BBF7D0", fontsize=9.1
    )

    draw_arrow(ax3, 4.7, 6.85, 4.7, 6.05, "використовує", 4.88, 6.45, dashed=True)
    draw_arrow(ax3, 4.7, 4.70, 4.7, 3.90, "залежить від контракту", 4.88, 4.30, dashed=True)
    draw_arrow(ax3, 4.7, 1.70, 4.7, 2.50, "реалізує інтерфейс", 4.88, 2.10, dashed=True)

    save_fig(fig3, "fig_4_1_implementation_classes")


# ==============================================================================
# 11. Графіки експериментів обсягу даних та навантаження (Рисунок 5.2)
# ==============================================================================
def make_benchmarks_chart():
    results_path = os.path.join(root_dir, "evidence", "test_results.json")
    with open(results_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    vol = data["volumeBenchmarks"]
    load = data["loadBenchmarks"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.6))

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
    ax1.set_ylim(0, max(noidx_vals) * 1.24)

    labels_l = [f"{r['VirtualUsers']} VU" for r in load]
    p50_vals = [r["P50Ms"] for r in load]
    p95_vals = [r["P95Ms"] for r in load]
    p99_vals = [r["P99Ms"] for r in load]

    xl = range(len(labels_l))
    wl = 0.25
    b_p50 = ax2.bar([i - wl for i in xl], p50_vals, width=wl, label="p50 (медіана, мс)", color="#10B981", edgecolor="#0F172A")
    b_p95 = ax2.bar(list(xl), p95_vals, width=wl, label="p95 (95-й перцентиль, мс)", color="#3B82F6", edgecolor="#0F172A")
    b_p99 = ax2.bar([i + wl for i in xl], p99_vals, width=wl, label="p99 (99-й перцентиль, мс)", color="#EF4444", edgecolor="#0F172A")
    ax2.set_xticks(list(xl))
    ax2.set_xticklabels(labels_l)
    ax2.set_ylabel("Час відповіді сценарію, мс")
    ax2.set_title("б) Затримки p50 / p95 / p99 під навантаженням (Д.5.6)", fontweight="bold", fontsize=11)
    ax2.grid(axis="y", linestyle="--", alpha=0.5)
    ax2.legend(fontsize=9)
    for bar in list(b_p50) + list(b_p95) + list(b_p99):
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, h + 0.18, f"{h:.2f}", ha="center", va="bottom", fontsize=8.0)
    ax2.set_ylim(0, max(p99_vals) * 1.26)

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
