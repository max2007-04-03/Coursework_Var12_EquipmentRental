import os
from report_helpers import (
    add_body_p, add_bullet_p, add_structural_heading, add_section_heading,
    add_subsection_heading, add_styled_table, add_figure, add_screenshot_placeholder, add_code_listing
)

def build_section_4(doc, root_dir):
    # ==========================================================================
    # РОЗДІЛ 4. РЕАЛІЗАЦІЯ ВЕБСИСТЕМИ (Д.4, с. 74–76)
    # ==========================================================================
    add_section_heading(doc, "4 РЕАЛІЗАЦІЯ ВЕБСИСТЕМИ", page_break=True)

    add_subsection_heading(doc, "4.1 Структура проєкту та реалізація ключових серверних модулів")
    add_body_p(doc, "Програмна реалізація вебсистеми виконана у вигляді рішення EquipmentRental.sln, що об’єднує чотири проєкти серверної частини на платформі .NET 10.0, каталог клієнтського SPA-застосунку client/, каталог SQL-скриптів sql/ та тестовий стенд tests/EquipmentRental.Tests. Діаграму ключових класів реалізації наведено на рисунку 4.1, а призначення основних файлів вихідного коду — у таблиці 4.1.")

    add_figure(
        doc,
        os.path.join(root_dir, "docs", "diagrams", "fig_4_1_implementation_classes.png"),
        "4.1",
        "Діаграма ключових класів та інтерфейсів реалізації серверної частини",
        width_mm=138
    )

    add_styled_table(
        doc,
        table_num="4.1",
        table_title="Призначення основних модулів і файлів вихідного коду вебсистеми",
        headers=["Шлях до файлу у репозиторії", "Шар архітектури", "Основні класи / функції та їхнє призначення"],
        rows=[
            ["sql/init.sql, sql/seed.sql", "Database (DDL/DML)", "Створення 7 таблиць, обмежень CHECK/FK, 7 індексів і початкового набору даних (18 екземплярів)"],
            ["src/EquipmentRental.Domain/Entities.cs", "Domain Layer", "Доменні сутності EquipmentType, EquipmentUnit, Booking, Tariff, RentalEvent, WaitlistEntry, структура Money"],
            ["src/EquipmentRental.Domain/PricingAndAvailabilityRules.cs", "Domain Layer", "Чисті методи перевірки перетину інтервалів із буфером ТО, розрахунку вартості, пені та переходів статусів"],
            ["src/EquipmentRental.Domain/IRentalRepository.cs", "Domain Layer", "Контракт репозиторію для атомарного читання та збереження агрегатів"],
            ["src/EquipmentRental.Application/ContractsAndDtos.cs", "Application Layer", "Вхідні/вихідні DTO з атрибутами валідації та структура ApiErrorResponse (RFC 9457)"],
            ["src/EquipmentRental.Application/RentalApplicationService.cs", "Application Layer", "Прикладний сервіс каталогу, поекземплярного календаря та попереднього розрахунку оренди"],
            ["src/EquipmentRental.Infrastructure/PasswordHasher.cs", "Infrastructure Layer", "Криптографічне хешування та верифікація паролів за PBKDF2-HMAC-SHA256 (100 000 ітерацій)"],
            ["src/EquipmentRental.Infrastructure/SqliteRentalRepository.cs", "Infrastructure Layer", "Реалізація транзакцій BEGIN IMMEDIATE, параметризованих запитів SQLite та оповіщення черги Waitlist"],
            ["src/EquipmentRental.WebApi/SessionAuthManager.cs", "Presentation (API)", "Керування серверними сесіями в HttpOnly Cookie та перевірка прав ролей"],
            ["src/EquipmentRental.WebApi/Controllers/RentalApiController.cs", "Presentation (API)", "Контролер HTTP-маршрутів каталогу, календаря, бронювань, черги очікування та операцій менеджера"],
            ["client/src/app.jsx, client/src/api.js, client/src/style.css", "Presentation (SPA)", "Мінімалістичний клієнтський інтерфейс React 19 (екрани UI-01..UI-06) та клієнтський шар обміну з API"],
            ["tests/EquipmentRental.Tests/Program.cs", "Automated QA", "Набір модульних та інтеграційних автотестів (12 кейсів), стенд обсягу даних та навантаження"],
        ],
        col_widths_mm=[54, 32, 84],
        font_size=10.5
    )

    add_body_p(doc, "Реалізацію доменного ядра перевірки перетину інтервалів з урахуванням обов’язкової технічної перерви та розрахунку вартості у цілих копійках наведено у лістингу 4.1.")

    add_code_listing(
        doc,
        "4.1",
        "Фрагмент класу PricingAndAvailabilityRules.cs (шар EquipmentRental.Domain)",
        """public static bool IntervalsOverlap(
    DateTimeOffset aStart, DateTimeOffset aEffectiveEnd,
    DateTimeOffset bStart, DateTimeOffset bEffectiveEnd)
{
    return aStart < bEffectiveEnd && bStart < aEffectiveEnd;
}

public static PriceCalculationResult CalculatePrice(
    DateTimeOffset startsAt, DateTimeOffset endsAt,
    Tariff tariff, int maintenanceBufferHours)
{
    if (endsAt <= startsAt)
        throw new DomainRuleException("END_BEFORE_START",
            "Дата та час завершення оренди мають бути пізнішими за час початку.");

    TimeSpan duration = endsAt - startsAt;
    double totalMinutes = duration.TotalMinutes;
    int billedUnits = tariff.BillingUnit == BillingUnit.Hour
        ? (int)Math.Ceiling(totalMinutes / 60.0)
        : (int)Math.Ceiling(totalMinutes / (60.0 * 24.0));

    if (billedUnits < 1) billedUnits = 1;
    long basePriceMinor = checked((long)billedUnits * tariff.RateMinor);
    DateTimeOffset bufferEndsAt = endsAt.AddHours(Math.Max(0, maintenanceBufferHours));

    return new PriceCalculationResult(
        billedUnits, tariff.RateMinor, basePriceMinor,
        tariff.DepositMinor, basePriceMinor, bufferEndsAt);
}"""
    )

    add_body_p(doc, "Реалізацію транзакційного методу створення бронювання у класі SqliteRentalRepository.cs з використанням блокування BEGIN IMMEDIATE та параметризованих SQL-команд подано у лістингу 4.2.")

    add_code_listing(
        doc,
        "4.2",
        "Фрагмент транзакційного створення заявки у SqliteRentalRepository.cs",
        """public Booking CreateBookingAtomic(
    string clientUserId, string unitId,
    DateTimeOffset startsAt, DateTimeOffset endsAt, string purpose)
{
    using var conn = OpenConnection();
    using var cmdBegin = conn.CreateCommand();
    cmdBegin.CommandText = "BEGIN IMMEDIATE TRANSACTION;";
    cmdBegin.ExecuteNonQuery();

    try
    {
        var unit = GetEquipmentUnitByIdInternal(conn, unitId)
            ?? throw new DomainRuleException("UNIT_NOT_FOUND", "Екземпляр не знайдено.", 404);
        var eqType = GetEquipmentTypeByIdInternal(conn, unit.EquipmentTypeId)!;
        var tariff = GetTariffByIdInternal(conn, eqType.TariffId)!;
        var activeBookings = GetActiveBookingsForUnitInternal(conn, unitId);

        var check = PricingAndAvailabilityRules.ValidateAndCheckAvailability(
            unit, eqType, tariff, startsAt, endsAt, activeBookings);
        if (!check.IsAvailable)
            throw new DomainRuleException(check.ErrorCode!, check.ErrorMessage!,
                check.ErrorCode == "INTERVAL_CONFLICT" ? 409 : 400);

        var calc = check.Price!;
        // Вставка запису у таблицю bookings та події CREATED у rental_events
        // ...
        using var cmdCommit = conn.CreateCommand();
        cmdCommit.CommandText = "COMMIT;";
        cmdCommit.ExecuteNonQuery();
        return GetBookingByIdInternal(conn, bookingId)!;
    }
    catch
    {
        using var cmdRollback = conn.CreateCommand();
        cmdRollback.CommandText = "ROLLBACK;";
        try { cmdRollback.ExecuteNonQuery(); } catch { }
        throw;
    }
}"""
    )

    add_subsection_heading(doc, "4.2 Реалізація клієнтського інтерфейсу та сценаріїв роботи з даними")
    add_body_p(doc, "Клієнтська частина реалізована як односторінковий застосунок (SPA) на базі React 19 у мінімалістичному стилі без зайвих декоративних елементів. Інтерфейс забезпечує наочну роботу з каталогом позицій та фізичних екземплярів (рисунок 4.2), комбіновану фільтрацію за категорією і пошуковим запитом (рисунок 4.3), а також коректне опрацювання стану порожньої вибірки із можливістю миттєвого скидання фільтрів (рисунок 4.4).")

    fig_4_2_path = os.path.join(root_dir, "docs", "screenshots", "fig_4_2_catalog.png")
    if os.path.exists(fig_4_2_path):
        add_figure(
            doc,
            fig_4_2_path,
            "4.2",
            "Головний екран каталогу обладнання з переліком фізичних інвентарних екземплярів (1280px)",
            width_mm=160
        )
    else:
        add_screenshot_placeholder(
            doc,
            "4.2",
            "Головний екран каталогу обладнання з переліком фізичних інвентарних екземплярів (1280px)",
            "Вкладка «1. Каталог та огляд екземплярів» — загальний вигляд карток обладнання та інвентарних номерів"
        )

    fig_4_3_path = os.path.join(root_dir, "docs", "screenshots", "fig_4_3_filter.png")
    if os.path.exists(fig_4_3_path):
        add_figure(
            doc,
            fig_4_3_path,
            "4.3",
            "Робота комбінованого фільтра каталогу за категорією «Енергообладнання»",
            width_mm=160
        )
    else:
        add_screenshot_placeholder(
            doc,
            "4.3",
            "Робота комбінованого фільтра каталогу за категорією «Енергообладнання»",
            "Вкладка «1. Каталог» — у полі «Категорія обладнання» обрано «Енергообладнання»"
        )

    fig_4_4_path = os.path.join(root_dir, "docs", "screenshots", "fig_4_4_empty.png")
    if os.path.exists(fig_4_4_path):
        add_figure(
            doc,
            fig_4_4_path,
            "4.4",
            "Відображення стану порожньої вибірки при пошуку неіснуючого обладнання",
            width_mm=160
        )
    else:
        add_screenshot_placeholder(
            doc,
            "4.4",
            "Відображення стану порожньої вибірки при пошуку неіснуючого обладнання",
            "Вкладка «1. Каталог» — у полі пошуку введено неіснуючу назву (наприклад, «НеіснуючийПрилад999»)"
        )

    add_body_p(doc, "Екран поекземплярного календаря доступності та серверного калькулятора вартості (рисунок 4.5) відображає матрицю зайнятості кожної фізичної одиниці обраної позиції (наприклад, генератора Honda EU22i з екземплярами INV-GEN-001, INV-GEN-002 та INV-GEN-003) за днями місяця. При виборі часового інтервалу, який накладається на чинну оренду або її 4-годинну технічну перерву, сервер повертає структуровану відмову 409 Conflict (INTERVAL_CONFLICT), зберігаючи введені дані форми та відкриваючи блок запису в чергу очікування Waitlist (рисунок 4.6). У разі введення некоректного інтервалу (дата завершення раніше дати початку) клієнт отримує повідомлення валідації 400 Bad Request (END_BEFORE_START, рисунок 4.7), а при виборі вільного часового вікна — підтвердження успішного створення заявки 201 Created (рисунок 4.8).")

    add_screenshot_placeholder(
        doc,
        "4.5",
        "Екран поекземплярного календаря доступності, технічних перерв і тарифного калькулятора",
        "Вкладка «2. Календар доступності та оформлення оренди» (позиція «Інверторний генератор Honda EU22i»)"
    )

    add_screenshot_placeholder(
        doc,
        "4.6",
        "Відображення конфлікту накладання на технічну перерву (409 Conflict) та форми черги очікування (Waitlist)",
        "Вкладка «2. Календар» — натиснуто пресет «Накладання на тех. перерву (16.11 10:30)» та кнопку відправлення заявки"
    )

    add_screenshot_placeholder(
        doc,
        "4.7",
        "Відображення керованої помилки валідації дат (400 END_BEFORE_START) та успішного створення заявки (201 Created)",
        "Вкладка «2. Календар» — повідомлення про помилку дат або зелене повідомлення про успішне створення заявки"
    )

    add_body_p(doc, "Особистий кабінет клієнта зі списком власних бронювань і станом черги очікування подано на рисунку 4.8, а робочу панель менеджера прокату з інспектором подій rental_events та обліком пені за прострочення — на рисунку 4.9.")

    add_screenshot_placeholder(
        doc,
        "4.8",
        "Особистий кабінет клієнта: список власних бронювань та таблиця черги очікування (Waitlist)",
        "Вкладка «3. Кабінет клієнта та черга очікування» під обліковим записом клієнта"
    )

    add_screenshot_placeholder(
        doc,
        "4.9",
        "Робоча панель менеджера прокату: реєстр усіх заявок, картка керування статусом та історія подій (rental_events)",
        "Вкладка «4. Робоча панель менеджера» під обліковим записом Мельник Ірини Сергіївни з відкритою карткою подій"
    )

    add_subsection_heading(doc, "4.3 Керування вихідним кодом і версіями у Git")
    add_body_p(doc, "Керування конфігурацією проєкту здійснюється у системі контролю версій Git із дотриманням угоди Conventional Commits. Скомпільовані бінарні файли (bin/, obj/), зовнішні пакети (node_modules/) та тимчасові журнали СКБД (*.db-wal, *.db-shm) виключено через файл .gitignore. Фінальний стан кодової бази зафіксовано анотованим релізним тегом v1.0.0-release. Історію основних комітів репозиторію наведено у таблиці 4.2.")

    add_styled_table(
        doc,
        table_num="4.2",
        table_title="Історія комітів та етапів розробки у Git-репозиторії проєкту",
        headers=["Хеш коміту", "Автор", "Повідомлення коміту (Conventional Commits)", "Охоплені артефакти"],
        rows=[
            ["acd615b", "Maxym Slyvka", "feat(db): add SQLite DDL schema (7 tables, 7 indexes) and synthetic seed dataset", "sql/init.sql, sql/seed.sql, .gitignore, .env.example"],
            ["866defd", "Maxym Slyvka", "feat(domain): implement integer kopiyka Money, interval overlap with maintenance buffer, and application DTOs", "EquipmentRental.Domain, EquipmentRental.Application"],
            ["c731e4e", "Maxym Slyvka", "feat(api): implement SqliteRentalRepository (BEGIN IMMEDIATE), PBKDF2 auth, and REST controllers with RFC 9457", "EquipmentRental.Infrastructure, EquipmentRental.WebApi"],
            ["fdf1615", "Maxym Slyvka", "feat(ui): build React 19 SPA with availability calendar matrix, calculator, waitlist, and manager workspace", "client/src/app.jsx, api.js, style.css, vite.config.js"],
            ["8e1a06f", "Maxym Slyvka", "test(qa): add unit/integration test suite, volume/load benchmarks, diagrams, and E2E verification", "tests/EquipmentRental.Tests, evidence/test_results.json, README.md"],
        ],
        col_widths_mm=[24, 30, 68, 48],
        font_size=10.5
    )

    add_subsection_heading(doc, "4.4 Метрики коду та контроль дотримання архітектурних обмежень")
    add_body_p(doc, "Для оцінки структурної якості програмної реалізації проаналізовано кількісні метрики вихідного коду за шарами системи (таблиця 4.3) та перевірено дотримання проєктних обмежень (таблиця 4.4).")

    add_styled_table(
        doc,
        table_num="4.3",
        table_title="Кількісні метрики кодової бази розробленої вебсистеми за підсистемами",
        headers=["Підсистема / Проєкт", "Мова програмування", "Кількість файлів", "Рядків коду (LOC)", "Ключові показники складності та чистоти"],
        rows=[
            ["EquipmentRental.Domain", "C# 13 (.NET 10.0)", "3", "398", "0 зовнішніх залежностей, середня цикломатична складність методів <= 5"],
            ["EquipmentRental.Application", "C# 13 (.NET 10.0)", "2", "602", "Сувора типізація DTO (record), відсутність прямих звернень до БД"],
            ["EquipmentRental.Infrastructure", "C# 13 (.NET 10.0)", "2", "985", "100 % параметризованих SQL-запитів, транзакційна безпека BEGIN IMMEDIATE"],
            ["EquipmentRental.WebApi", "C# 13 (.NET 10.0)", "3", "618", "Уніфіковане перехоплення доменних винятків у формат RFC 9457"],
            ["Клієнтський SPA (client/src)", "JavaScript (JSX) + CSS", "4", "1 680", "Модульна структура екранів, 0 помилок лінтингу та збирання Vite"],
            ["SQL-скрипти та Автотести", "SQL + C# 13", "3", "865", "7 таблиць, 7 індексів, 12 автоматизованих тест-кейсів та 2 бенчмарки"],
            ["Разом по системі", "C# / JS / CSS / SQL", "17", "5 148", "Збирання dotnet build: 0 попереджень (Warnings), 0 помилок (Errors)"],
        ],
        col_widths_mm=[42, 32, 22, 24, 50],
        font_size=10.5
    )

    add_styled_table(
        doc,
        table_num="4.4",
        table_title="Результати контролю дотримання архітектурних та програмних обмежень",
        headers=["Обмеження проєкту", "Спосіб інструментальної перевірки", "Фактичний результат"],
        rows=[
            ["Відсутність типу double/float у грошових розрахунках", "Пошук за кодовою базою Domain/Application/Infrastructure", "Використано виключно тип long (цілі копійки) та структуру Money"],
            ["Незалежність шару Domain від інфраструктури", "Перевірка файлу EquipmentRental.Domain.csproj", "Жодних посилань на пакети БД або ASP.NET Core"],
            ["Серверна перевірка сесії та ролі на всіх закритих маршрутах", "Аудит методів RentalApiController.cs та інтеграційні тести", "Усі операції запису перевіряють RequireAuth / RequireRole(MANAGER)"],
        ],
        col_widths_mm=[54, 56, 60],
        font_size=11
    )

    add_body_p(doc, "Висновки до розділу 4. Програмно реалізовано всі серверні та клієнтські модулі вебсистеми відповідно до спроєктованої пошарової архітектури. Кодова база обсягом понад 5 100 рядків компілюється без жодного попередження чи помилки та повністю реалізує вимоги варіанта 12.")


def build_section_5(doc, root_dir):
    # ==========================================================================
    # РОЗДІЛ 5. ЗАБЕЗПЕЧЕННЯ ЯКОСТІ ВЕБСИСТЕМИ (Д.5, с. 77–82)
    # ==========================================================================
    add_section_heading(doc, "5 ЗАБЕЗПЕЧЕННЯ ЯКОСТІ ВЕБСИСТЕМИ", page_break=True)

    add_subsection_heading(doc, "5.1 План і середовище тестування")
    add_body_p(doc, "Верифікація якості розробленої вебсистеми проведена за комплексною програмою випробувань, що поєднує модульне тестування предметного ядра, інтеграційне тестування транзакційного сховища SQLite і серверної авторизації, наскрізні перевірки користувацьких сценаріїв у браузері, перевірку адаптивності й доступності інтерфейсу, а також експериментальне навантажувальне та об’ємне тестування. Параметри тестового стенда наведено у таблиці 5.1.")

    add_styled_table(
        doc,
        table_num="5.1",
        table_title="Конфігурація апаратно-програмного стенда та види проведених перевірок",
        headers=["Параметр середовища / Вид тестування", "Характеристики та інструментальні засоби стенда", "Обсяг вибірки / Умови запуску"],
        rows=[
            ["Апаратна конфігурація та ОС", "Процесор x64 (8 ядер), 16 ГБ ОЗП, NVMe SSD; ОС Windows 11 Pro x64", "Локальний ізольований стенд без фонового мережевого навантаження"],
            ["Середовище виконання", ".NET SDK 10.0.100, SQLite 3 (WAL mode, busy_timeout=5000), браузер Microsoft Edge 134", "Чиста ініціалізація БД перед кожним прогоном автотестів"],
            ["Модульні та інтеграційні тести", "Проєкт tests/EquipmentRental.Tests (12 автоматизованих тест-кейсів)", "Автоматичний запис протоколу у файл evidence/test_results.json"],
            ["Тестування обсягом даних", "Генерація 100, 1 000 та 10 000 записів у таблиці bookings", "Порівняння часу з індексом idx_bookings_unit_interval та без нього"],
            ["Навантажувальне тестування", "Багатопотоковий генератор конкурентних клієнтів (5, 10 та 25 VU)", "По 30 ітерацій змішаного профілю на кожного віртуального користувача"],
        ],
        col_widths_mm=[48, 68, 54],
        font_size=11
    )

    add_subsection_heading(doc, "5.2 Тест-кейси та протокол функціонального приймання")
    add_body_p(doc, "У таблиці 5.2 наведено повний реєстр автоматизованих модульних (TC-UT-01..05), інтеграційних (TC-IT-01..07) та наскрізних (TC-E2E-01..04) тест-кейсів із фактичними результатами їх виконання.")

    add_styled_table(
        doc,
        table_num="5.2",
        table_title="Специфікація тест-кейсів та фактичний протокол їх виконання",
        headers=["Код тесту", "Вимога", "Сценарій перевірки та вхідні дані", "Очікуваний результат", "Фактичний результат / Статус"],
        rows=[
            ["TC-UT-01", "FR-04, NFR-02", "Перетин інтервалів з урахуванням 4-годинної технічної перерви (оренда до 09:00, буфер до 13:00; нова заявка з 10:30 та з 13:00)", "О 10:30 — конфлікт (true); о 13:00 (стик у стик) — конфлікту немає (false)", "Співпадає (0,32 мс) — PASSED"],
            ["TC-UT-02", "FR-03, NFR-02", "Розрахунок добового тарифу у копійках за 26 годин оренди при ставці 85 000 коп./доба і заставі 300 000 коп.", "Округлення до 2 діб; базова сума = 170 000 коп. (1 700,00 грн)", "170 000 коп., 2 доби — PASSED"],
            ["TC-UT-03", "FR-08, NFR-02", "Розрахунок пені за прострочення повернення на 2 год 15 хв при штрафній ставці 15 000 коп./год", "Округлення до 3 штрафних годин; пеня = 45 000 коп. (450,00 грн)", "3 год, 45 000 коп. — PASSED"],
            ["TC-UT-04", "FR-04", "Валідація граничних помилок дат: час закінчення раніше початку (endsAt < startsAt) та перевищення max_units", "Виняток DomainRuleException з кодами END_BEFORE_START та DURATION_TOO_LONG", "Коди співпадають — PASSED"],
            ["TC-UT-05", "FR-07, FR-08", "Контроль переходів автомата станів: спроба перевести PENDING одразу в RETURNED оминаючи CONFIRMED та ISSUED", "Блокування переходу з кодом INVALID_TRANSITION", "Заблоковано — PASSED"],
            ["TC-IT-01", "FR-04, NFR-02", "Атомарне створення заявки у SQLite на вільний інтервал екземпляра INV-GEN-001 (22.11–24.11)", "Запис створено у статусі PENDING, створено подію CREATED у rental_events", "201 Created, подія є — PASSED"],
            ["TC-IT-02", "FR-04, NFR-02", "Відхилення конкуруючої заявки у SQLite при накладанні на технічну перерву існуючої оренди RN-2026-1001", "Транзакція відкочується, повертається код INTERVAL_CONFLICT (HTTP 409)", "409 INTERVAL_CONFLICT — PASSED"],
            ["TC-IT-03", "FR-09", "Блокування спроби бронювання екземпляра INV-GEN-003, що перебуває у стані IN_MAINTENANCE", "Відмова з кодом UNIT_NOT_AVAILABLE (HTTP 409)", "409 UNIT_NOT_AVAILABLE — PASSED"],
            ["TC-IT-04", "FR-06, NFR-03", "Захист від скасування чужого бронювання: клієнт usr-cli-02 намагається скасувати заявку клієнта usr-cli-01", "Відмова доступу 403 Forbidden з кодом FORBIDDEN_NOT_OWNER", "403 FORBIDDEN_NOT_OWNER — PASSED"],
            ["TC-IT-05", "FR-05", "Автоматичний перехід запису черги очікування wlt-01 у стан NOTIFIED після скасування конфліктної заявки", "Статус запису wlt-01 у таблиці waitlist_entries змінюється з WAITING на NOTIFIED", "Статус NOTIFIED — PASSED"],
            ["TC-IT-06", "FR-07, FR-08", "Повний цикл менеджера: PENDING -> CONFIRMED -> ISSUED -> RETURNED із запізненням на 2,5 год", "Нараховано 3 год пені (+450,00 грн), записано 4 події у rental_events", "Сума і події вірні — PASSED"],
            ["TC-IT-07", "FR-06", "Продовження активної оренди клієнтом на вільний час та блокування продовження при зіткненні з чужим слотом", "На вільний час — успіх (version+1); при зіткненні — 409 INTERVAL_CONFLICT", "Обидві гілки вірні — PASSED"],
        ],
        col_widths_mm=[20, 22, 54, 42, 32],
        font_size=10.0
    )

    add_subsection_heading(doc, "5.3 Модульні, інтеграційні та наскрізні перевірки")
    add_body_p(doc, "Усі 12 модульних та інтеграційних тест-кейсів реалізовано у проєкті tests/EquipmentRental.Tests/Program.cs і виконано із підсумковим результатом 12/12 PASSED (100 % успішності). Фрагмент коду автоматизованої перевірки життєвого циклу повернення із нарахуванням пені та оповіщення черги очікування наведено у лістингу 5.1.")

    add_code_listing(
        doc,
        "5.1",
        "Фрагмент інтеграційних автотестів у tests/EquipmentRental.Tests/Program.cs",
        """// TC-IT-05: Автоматичне оповіщення черги очікування (Waitlist) при звільненні слота
RunTest("TC-IT-05", "Автоматичний перехід Waitlist у NOTIFIED після скасування", () =>
{
    repo.CancelBookingAtomic("bkg-1001", "usr-cli-01", isManager: false, "Дострокове скасування");
    var waitlist = repo.GetWaitlistEntries(null);
    var entry = waitlist.First(w => w.Id == "wlt-01");
    Assert(entry.Status == WaitlistStatus.Notified,
        $"Очікувався статус Notified, отримано {entry.Status}");
});"""
    )

    add_subsection_heading(doc, "5.4 Перевірка адаптивності верстки та доступності інтерфейсу (WCAG 2.2 AA)")
    add_body_p(doc, "Перевірку адаптивності клієнтського інтерфейсу виконано на трьох нормативних контрольних точках ширини вікна перегляду: 360px (мобільний смартфон), 768px (планшет) та 1280px (настільний монітор). Перевірку поведінки макета на вузьких екранах проілюстровано на рисунку 5.1, а результати інструментального аудиту адаптивності й доступності за стандартом WCAG 2.2 (рівень AA) [8] зведено у таблиці 5.3.")

    add_screenshot_placeholder(
        doc,
        "5.1",
        "Перевірка адаптивної верстки інтерфейсу на контрольних точках 768px (планшет) та 360px (мобільний екран)",
        "Вікно браузера звужене до мобільної/планшетної ширини (через F12 -> Toggle Device Toolbar: 768px або 360px)"
    )

    add_styled_table(
        doc,
        table_num="5.3",
        table_title="Результати перевірки адаптивності верстки та доступності за критеріями WCAG 2.2 AA",
        headers=["Параметр перевірки / Критерій WCAG 2.2", "Вимога стандарту", "Фактична реалізація у вебсистемі", "Статус"],
        rows=[
            ["Контрольна точка 1280px (Desktop)", "Повноцінне багатоколонкове розміщення без перекриття блоків", "3-колонкова сітка карток каталогу, 2-колонкова робоча область бронювання і калькулятора", "Пройдено"],
            ["Контрольна точка 768px (Tablet)", "Перебудова панелі фільтрів і форми без втрати функціональності", "Фільтри перебудовуються у 2 колонки, форма і калькулятор вишиковуються вертикально", "Пройдено"],
            ["Контрольна точка 360px (Mobile)", "Відсутність горизонтального прокручування основної сторінки", "1-колонкова сітка карток, горизонтальне прокручування ізольоване всередині .table-responsive", "Пройдено"],
            ["Контрастність тексту (WCAG 1.4.3)", "Коефіцієнт контрасту основного тексту >= 4.5:1", "Текст #18181B на тлі #FFFFFF забезпечує контрастність 17.9:1 (перевищує рівень AAA)", "Пройдено"],
            ["Навігація з клавіатури та видимий фокус (WCAG 2.1.1, 2.4.7)", "Доступність усіх інтерактивних елементів через Tab і чіткий контур фокуса", "Усі кнопки, поля та перемикачі мають правило :focus-visible з контуром 2px solid #18181B", "Пройдено"],
            ["Семантичні мітки полів і живі області (WCAG 1.3.1, 4.1.3)", "Кожне поле вводу пов’язане з <label>, повідомлення мають role='alert'/'status'", "100 % полів форм мають явні атрибути id та htmlFor; банери помилок мають role='alert'", "Пройдено"],
        ],
        col_widths_mm=[42, 44, 62, 22],
        font_size=10.5
    )

    add_subsection_heading(doc, "5.5 Оцінка швидкодії клієнтського інтерфейсу (Core Web Vitals)")
    add_body_p(doc, "Під час виробничого збирання клієнтського застосунку засобами Vite 6 отримано мінімізований бандл: файл стилів становить 10,8 КБ (2,4 КБ у стисненому вигляді gzip), а основний скрипт застосунку — 264,8 КБ (80,4 КБ у gzip), що сумарно не перевищує 83 КБ мережевого трафіку. Завдяки відсутності важких сторонніх графічних бібліотек час відмальовування найбільшого змістового елемента (LCP) на локальному стенді становить 0,18 с (норматив <= 2,5 с), затримка реакції інтерфейсу на зміну параметрів калькулятора (INP) становить 14 мс (норматив <= 200 мс), а сукупне зміщення макета (CLS) дорівнює 0,00 (норматив <= 0,1).")

    add_subsection_heading(doc, "5.6 Навантажувальне тестування серверної частини")
    add_body_p(doc, "Для перевірки стійкості серверної частини та відсутності взаємних блокувань у СКБД SQLite під конкурентним навантаженням виконано серію випробувань при 5, 10 та 25 одночасних віртуальних користувачах (VU). Кожен віртуальний користувач у циклі з 30 ітерацій виконував змішаний профіль операцій: читання каталогу з фільтрацією, запит поекземплярного календаря та попередній розрахунок вартості й доступності. Результати навантажувального тестування наведено у таблиці 5.4.")

    add_styled_table(
        doc,
        table_num="5.4",
        table_title="Результати навантажувального тестування при 5, 10 та 25 віртуальних користувачах",
        headers=["Кількість конкурентних користувачів (VU)", "Загальна кількість запитів у сесії", "Пропускна здатність (RPS, запит/с)", "Медіана часу відповіді p50, мс", "Перцентиль p95, мс", "Перцентиль p99, мс", "Частка технічних помилок (5xx / SQLite busy)"],
        rows=[
            ["5 VU", "150", "801,4 запит/с", "0,69 мс", "2,70 мс", "6,80 мс", "0 % (0 помилок)"],
            ["10 VU", "300", "5 281,9 запит/с", "1,38 мс", "4,47 мс", "7,05 мс", "0 % (0 помилок)"],
            ["25 VU", "750", "5 908,3 запит/с", "1,43 мс", "4,55 мс", "9,05 мс", "0 % (0 помилок)"],
        ],
        col_widths_mm=[24, 24, 28, 24, 22, 22, 26],
        font_size=10.5
    )

    add_subsection_heading(doc, "5.7 Тестування обсягом даних та ефективність індексації")
    add_body_p(doc, "Під час тестування обсягом даних таблицю bookings послідовно заповнено синтетичними наборами зі 100, 1 000 та 10 000 записів оренд із реалістичним розподілом інвентарних одиниць і дат. Порівняльні результати часу виконання основних операцій зведено у таблиці 5.5, а графічну ілюстрацію результатів об’ємного та навантажувального експериментів подано на рисунку 5.2.")

    add_styled_table(
        doc,
        table_num="5.5",
        table_title="Зведені результати тестування вебсистеми обсягом даних (100, 1 000 та 10 000 записів)",
        headers=["Кількість записів у таблиці bookings", "Пошук і фільтрація каталогу, мс", "Завантаження календаря позиції, мс", "Перевірка інтервалу (з індексом), мс", "Перевірка інтервалу (без індексу), мс", "Висновок щодо вимоги NFR-01 (<= 15 мс)"],
        rows=[
            ["100 записів", "2,52 мс", "0,74 мс", "0,54 мс", "0,47 мс", "Виконано з запасом"],
            ["1 000 записів", "2,98 мс", "0,79 мс", "0,73 мс", "0,93 мс", "Виконано з запасом"],
            ["10 000 записів", "31,94 мс", "0,72 мс", "7,48 мс", "22,95 мс", "Виконано завдяки складеному індексу (7,48 <= 15 мс)"],
        ],
        col_widths_mm=[26, 26, 26, 28, 28, 36],
        font_size=10.5
    )

    add_figure(
        doc,
        os.path.join(root_dir, "docs", "diagrams", "fig_5_1_benchmarks.png"),
        "5.2",
        "Експериментальні графіки впливу обсягу даних та конкурентного навантаження на час відгуку системи",
        width_mm=158
    )

    add_subsection_heading(doc, "5.8 Журнал дефектів і підсумковий висновок про якість")
    add_body_p(doc, "У процесі ітеративної розробки та прогону автоматизованих тестів було виявлено та усунено три дефекти реалізації, зафіксовані у журналі дефектів (таблиця 5.6). На момент фінального релізу v1.0.0-release відкритих дефектів у системі немає.")

    add_styled_table(
        doc,
        table_num="5.6",
        table_title="Журнал виявлених і усунених дефектів під час розроблення та верифікації",
        headers=["Код дефекту", "Критичність", "Опис виявленої проблеми", "Спосіб усунення у вихідному коді", "Статус"],
        rows=[
            ["DEF-01", "Висока (Major)", "Хибний конфлікт при стикуванні початку нової оренди рівно у хвилину завершення технічної перерви попередньої (13:00 == 13:00)", "Замінено нестроге порівняння (<=) на строгу умову напіввідкритих інтервалів aStart < bEffectiveEnd && bStart < aEffectiveEnd", "Виправлено (TC-UT-01)"],
            ["DEF-02", "Середня (Medium)", "Відсутність автоматичного переведення запису черги очікування у NOTIFIED при відхиленні заявки менеджером (спрацьовувало лише при скасуванні клієнтом)", "Виклик методу RefreshWaitlistForUnitInternal() додано також у транзакцію RejectBookingAtomic()", "Виправлено (TC-IT-05)"],
            ["DEF-03", "Низька (Minor)", "Відносний шлях до каталогу sql/init.sql залежав від поточної робочої теки запуску процесу WebApi", "У Program.cs реалізовано рекурсивний пошук кореня репозиторію FindRepoRoot() та прив’язку WebRootPath", "Виправлено"],
        ],
        col_widths_mm=[20, 24, 52, 52, 22],
        font_size=10.5
    )

    add_body_p(doc, "Висновки до розділу 5. Проведене комплексне тестування підтвердило повне виконання всіх функціональних (FR-01..FR-09) і нефункціональних (NFR-01..NFR-08) вимог. Система витримує конкурентне навантаження 25 VU без жодної помилки при p95 = 4,55 мс та забезпечує 3,07-кратне прискорення перевірки інтервалів на 10 000 записів завдяки індексації.")


def build_conclusions_and_refs(doc):
    # ==========================================================================
    # ВИСНОВКИ
    # ==========================================================================
    add_structural_heading(doc, "ВИСНОВКИ", page_break=True)
    add_body_p(doc, "У результаті виконання курсової роботи з дисципліни «Веб-технології та веб-дизайн» спроєктовано, програмно реалізовано та всебічно протестовано клієнт-серверну вебсистему оренди обладнання з календарем доступності за варіантом 12. Основні науково-практичні та інженерні результати роботи полягають у такому:")
    add_bullet_p(doc, "1. Проаналізовано предметну область ", "прокату спеціалізованого обладнання, виявлено ключові проблеми поекземплярного планування розкладів і технічних перерв, розмежовано повноваження трьох ролей користувачів (Гість, Клієнт, Менеджер прокату) та сформульовано 9 функціональних (FR-01..FR-09) і 8 нефункціональних (NFR-01..NFR-08) вимог із прямим трасуванням до тест-кейсів.")
    add_bullet_p(doc, "2. Розроблено та досліджено алгоритмічне забезпечення ", "перевірки перетину напіввідкритих часових інтервалів з урахуванням індивідуального буфера технічного обслуговування (maintenance_buffer_hours), цілочисельної калькуляції тарифів і пені за прострочення у копійках, а також атомарного створення бронювання та оповіщення черги очікування. Експериментально доведено, що складений B-Tree індекс idx_bookings_unit_interval прискорює перевірку інтервалу на вибірці з 10 000 записів у 3,07 раза (із 22,95 мс до 7,48 мс).")
    add_bullet_p(doc, "3. Виконано повне архітектурне проєктування ", "вебсистеми за 12 взаємопов’язаними поданнями (архетип, UI View, Logical View, Deployment View, Design View, Process View, Data View у 3NF із 7 таблиць, Interface View за стандартом RFC 9457 Problem Details, Security View за OWASP Top 10:2025, ASVS 5.0.0 і NIST SP 800-63B-4, Operational, Infrastructure та Delivery Views).")
    add_bullet_p(doc, "4. Реалізовано програмну систему ", "обсягом понад 5 100 рядків коду на базі C# / ASP.NET Core 10.0 Web API, реляційної СКБД SQLite 3 (режим WAL, транзакції BEGIN IMMEDIATE) та мінімалістичного односторінкового клієнтського застосунку на React 19 (Vite).")
    add_bullet_p(doc, "5. Підтверджено високу якість програмного продукту: ", "успішно пройдено 12 із 12 модульних та інтеграційних автотестів, верифіковано адаптивність верстки на контрольних точках 360px, 768px і 1280px та відповідність критеріям доступності WCAG 2.2 AA. Під час навантажувального тестування при 25 одночасних віртуальних користувачах досягнуто пропускної здатності 5 908,3 запит/с при затримці p95 = 4,55 мс та нульовій частці технічних помилок.")

    # ==========================================================================
    # ПЕРЕЛІК ДЖЕРЕЛ (41 джерело за ДСТУ 8302:2015, с. 89–92 методички)
    # ==========================================================================
    add_structural_heading(doc, "ПЕРЕЛІК ДЖЕРЕЛ", page_break=True)
    refs = [
        "1. ДСТУ 3008:2015. Інформація та документація. Звіти у сфері науки і техніки. Структура та правила оформлювання. Чинний від 2017-07-01. Київ : ДП «УкрНДНЦ», 2016. 31 с.",
        "2. ДСТУ 8302:2015. Інформація та документація. Бібліографічне посилання. Загальні положення та правила складання. Чинний від 2016-07-01. Київ : ДП «УкрНДНЦ», 2016. 17 с.",
        "3. Методичні вказівки до виконання курсової роботи з дисципліни «Веб-технології та веб-дизайн» для здобувачів першого (бакалаврського) рівня вищої освіти спеціальності 122 «Комп’ютерні науки» / уклад.: П. П. Червоненко, О. Б. Бабійчук. Одеса : НУ «Одеська політехніка», 2026. 92 с.",
        "4. Fielding R., Nottingham M., Reschke J. HTTP Semantics : RFC 9110 / Internet Engineering Task Force (IETF). 2022. URL: https://www.rfc-editor.org/rfc/rfc9110 (дата звернення: 10.11.2026).",
        "5. Bray T. The JavaScript Object Notation (JSON) Data Interchange Format : RFC 8259 / Internet Engineering Task Force (IETF). 2017. URL: https://www.rfc-editor.org/rfc/rfc8259 (дата звернення: 10.11.2026).",
        "6. Nottingham M., Wilde E., Dalal S. Problem Details for HTTP APIs : RFC 9457 / Internet Engineering Task Force (IETF). 2023. URL: https://www.rfc-editor.org/rfc/rfc9457 (дата звернення: 10.11.2026).",
        "7. OMG Unified Modeling Language (OMG UML). Version 2.5.1 / Object Management Group. 2017. 796 p. URL: https://www.omg.org/spec/UML/2.5.1/ (дата звернення: 10.11.2026).",
        "8. Web Content Accessibility Guidelines (WCAG) 2.2 : W3C Recommendation / World Wide Web Consortium. 2023. URL: https://www.w3.org/TR/WCAG22/ (дата звернення: 10.11.2026).",
        "9. OWASP Top 10:2025. The Ten Most Critical Web Application Security Risks / OWASP Foundation. 2025. URL: https://owasp.org/www-project-top-ten/ (дата звернення: 10.11.2026).",
        "10. OWASP Application Security Verification Standard (ASVS). Version 5.0.0 / OWASP Foundation. 2025. URL: https://owasp.org/www-project-application-security-verification-standard/ (дата звернення: 10.11.2026).",
        "11. Grassi P. A., Fenton J. L., Newton E. M. Digital Identity Guidelines: Authentication and Lifecycle Management : NIST Special Publication 800-63B-4. Gaithersburg : National Institute of Standards and Technology, 2025. URL: https://pages.nist.gov/800-63-4/sp800-63b.html (дата звернення: 10.11.2026).",
        "12. ISO/IEC/IEEE 29148:2018. Systems and software engineering — Life cycle processes — Requirements engineering. Geneva : ISO, 2018. 104 p.",
        "13. ISO/IEC/IEEE 42010:2022. Software, systems and enterprise — Architecture description. Geneva : ISO, 2022. 74 p.",
        "14. ISO/IEC 25010:2023. Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE) — Product quality model. Geneva : ISO, 2023. 52 p.",
        "15. ISO/IEC/IEEE 29119-1:2022. Software and systems engineering — Software testing — Part 1: General concepts. Geneva : ISO, 2022. 68 p.",
        "16. Martin R. C. Clean Architecture: A Craftsman's Guide to Software Structure and Design. Boston : Prentice Hall, 2017. 432 p.",
        "17. Fowler M. Patterns of Enterprise Application Architecture. Boston : Addison-Wesley Professional, 2002. 560 p.",
        "18. Evans E. Domain-Driven Design: Tackling Complexity in the Heart of Software. Boston : Addison-Wesley, 2003. 560 p.",
        "19. Kleppmann M. Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems. Sebastopol : O'Reilly Media, 2017. 616 p.",
        "20. Freeman A. Pro ASP.NET Core 10. New York : Apress, 2025. 1180 p.",
        "21. Lock A. ASP.NET Core in Action. 3rd ed. Shelter Island : Manning Publications, 2023. 912 p.",
        "22. ASP.NET Core Documentation / Microsoft Learn. 2026. URL: https://learn.microsoft.com/en-us/aspnet/core/ (дата звернення: 11.11.2026).",
        "23. Handle errors in ASP.NET Core web APIs (Problem Details RFC 9457) / Microsoft Learn. 2026. URL: https://learn.microsoft.com/en-us/aspnet/core/web-api/handle-errors (дата звернення: 11.11.2026).",
        "24. Microsoft.Data.Sqlite Overview and Transactions / Microsoft Learn. 2026. URL: https://learn.microsoft.com/en-us/dotnet/standard/data/sqlite/ (дата звернення: 11.11.2026).",
        "25. SQLite Transactional SQL Engine Documentation : Write-Ahead Logging (WAL) and BEGIN IMMEDIATE. 2026. URL: https://www.sqlite.org/wal.html (дата звернення: 11.11.2026).",
        "26. SQLite Query Planner and Composite B-Tree Indexes. 2026. URL: https://www.sqlite.org/queryplanner.html (дата звернення: 11.11.2026).",
        "27. React 19 Official Documentation / Meta Open Source. 2026. URL: https://react.dev/ (дата звернення: 11.11.2026).",
        "28. Vite Next Generation Frontend Tooling Documentation. 2026. URL: https://vite.dev/guide/ (дата звернення: 11.11.2026).",
        "29. MDN Web Docs: CSS Grid Layout and Responsive Web Design / Mozilla Foundation. 2026. URL: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout (дата звернення: 11.11.2026).",
        "30. Web Vitals: Essential metrics for a healthy site (LCP, INP, CLS) / Google Developers. 2025. URL: https://web.dev/articles/vitals (дата звернення: 11.11.2026).",
        "31. Playwright End-to-End Testing Framework Documentation / Microsoft. 2026. URL: https://playwright.dev/ (дата звернення: 11.11.2026).",
        "32. Cormen T. H., Leiserson C. E., Rivest R. L., Stein C. Introduction to Algorithms. 4th ed. Cambridge : MIT Press, 2022. 1312 p.",
        "33. Allen J. F. Maintaining knowledge about temporal intervals // Communications of the ACM. 1983. Vol. 26, No. 11. P. 832–843.",
        "34. Snodgrass R. T. Developing Time-Oriented Database Applications in SQL. San Francisco : Morgan Kaufmann, 1999. 504 p.",
        "35. Goldberg D. What Every Computer Scientist Should Know About Floating-Point Arithmetic // ACM Computing Surveys. 1991. Vol. 23, No. 1. P. 5–48.",
        "36. Rfc2898DeriveBytes.Pbkdf2 Method (System.Security.Cryptography) / Microsoft Learn. 2026. URL: https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.rfc2898derivebytes.pbkdf2 (дата звернення: 11.11.2026).",
        "37. Booqable Rental Software Documentation: Inventory & Availability Calendar. 2025. URL: https://booqable.com/features/ (дата звернення: 11.11.2026).",
        "38. EZRentOut Equipment Rental Management System Overview. 2025. URL: https://ezo.io/ezrentout/ (дата звернення: 11.11.2026).",
        "39. Newman S. Monolith to Microservices: Evolutionary Patterns to Transform Your Monolith. Sebastopol : O'Reilly Media, 2019. 272 p.",
        "40. Richards M., Ford N. Fundamentals of Software Architecture: An Engineering Approach. Sebastopol : O'Reilly Media, 2020. 432 p.",
        "41. Chacon S., Straub B. Pro Git. 2nd ed. New York : Apress, 2014. 456 p. URL: https://git-scm.com/book/en/v2 (дата звернення: 11.11.2026).",
    ]
    for r in refs:
        add_body_p(doc, r, indent_mm=12.5, line_spacing=1.35)


def build_appendices(doc):
    # ==========================================================================
    # ДОДАТОК А. СУПРОВІДНА ДОКУМЕНТАЦІЯ ВЕБСИСТЕМИ (Д.6, с. 83)
    # ==========================================================================
    add_structural_heading(doc, "ДОДАТОК А\nСупровідна документація вебсистеми", page_break=True)

    add_subsection_heading(doc, "А.1 Інструкція користувача (Гість, Клієнт, Менеджер)")
    add_body_p(doc, "1. Перегляд каталогу та пошук обладнання. Після відкриття головної сторінки http://localhost:5080 користувач потрапляє на вкладку «1. Каталог та огляд екземплярів». Для пошуку потрібної позиції введіть назву або інвентарний код (наприклад, Honda або INV-GEN-001) у поле пошуку, оберіть категорію чи тип тарифікації. Щоб відібрати позиції, вільні на конкретні дати, увімкніть прапорець «Перевірити наявність у часовому вікні» та вкажіть початок і кінець періоду.")
    add_body_p(doc, "2. Робота з календарем доступності та оформлення заявки. Натисніть кнопку «Відкрити календар та забронювати» на картці обраної позиції. У таблиці поекземплярної шкали відображаються статуси кожної фізичної одиниці за днями: «Вільно», «Видано», «Підтв.», «Очікує», «Буфер» або «ТО». Оберіть інвентарний екземпляр, вкажіть дату й час початку та завершення оренди і мету використання (5–300 символів). У правій панелі сервер автоматично розрахує кількість оплачуваних одиниць, базову вартість, заставу та час завершення обов’язкової технічної перерви. Натисніть «Підтвердити та надіслати заявку на бронювання».")
    add_body_p(doc, "3. Запис у чергу очікування (Waitlist). Якщо обраний часовий інтервал перетинається з активною орендою або її технічною перервою, система виведе повідомлення 409 INTERVAL_CONFLICT і запропонує блок «Запис у чергу очікування (Waitlist)». Введіть контактну примітку та натисніть «Стати в чергу очікування на цей інтервал». У разі скасування або відхилення конфліктної заявки ваш запис у кабінеті клієнта автоматично отримає статус «СПОВІЩЕНО (СЛОТ ВІЛЬНИЙ)».")
    add_body_p(doc, "4. Операції менеджера прокату. Перемкніть обліковий запис у верхній панелі на «[МЕНЕДЖЕР] Мельник Ірина Сергіївна» та перейдіть на вкладку «4. Робоча панель менеджера». Для погодження нової заявки натисніть «Погодити», для передачі приладу клієнтові — «Видати». Для приймання повернення або відхилення заявки натисніть «Керувати / Події», вкажіть фактичний час повернення (якщо він перевищує плановий час завершення, система автоматично нарахує пеню за прострочення) і натисніть «Зафіксувати повернення (RETURNED)».")

    add_subsection_heading(doc, "А.2 Інструкція розробника та адміністратора")
    add_body_p(doc, "Системні вимоги: встановлений пакет .NET SDK 10.0 або новіший; операційна система Windows 10/11, Linux або macOS. Для запуску серверної частини та автоматичного розгортання бази даних SQLite виконайте у кореневій теці проєкту команди:")
    add_code_listing(
        doc,
        "А.1",
        "Команди компіляції, запуску вебсервера та виконання автотестів",
        """# 1. Компіляція всіх проєктів рішення
dotnet build EquipmentRental.sln

# 2. Запуск вебсервера на порту 5080 (автоматично виконує sql/init.sql та sql/seed.sql)
dotnet run --project src/EquipmentRental.WebApi/EquipmentRental.WebApi.csproj --urls http://localhost:5080

# 3. Запуск модульних, інтеграційних, об'ємних та навантажувальних тестів
dotnet run --project tests/EquipmentRental.Tests/EquipmentRental.Tests.csproj"""
    )

    # ==========================================================================
    # ДОДАТОК Б. МАТРИЦІ ВІДПОВІДНОСТІ, ПРОТОКОЛ ПРИЙМАННЯ ТА КОНТРОЛЬНІ ФОРМИ (Додаток Е, с. 84–88)
    # ==========================================================================
    add_structural_heading(doc, "ДОДАТОК Б\nМатриці відповідності, протокол приймання та контрольні форми", page_break=True)

    add_styled_table(
        doc,
        table_num="Б.1",
        table_title="Матриця відповідності вимог, архітектурних рішень, коду та тестів (за формою Додатка Е.1)",
        headers=["Код вимоги", "Архітектурне подання (Розділ 3)", "Модуль / Клас реалізації (Розділ 4)", "Код тест-кейсу (Розділ 5)", "Статус виконання"],
        rows=[
            ["FR-01", "UI View (UI-01), Interface View", "RentalApplicationService.GetCatalog(), app.jsx", "TC-E2E-01, Об’ємний стенд", "Виконано"],
            ["FR-02", "UI View (UI-02), Data View", "RentalApplicationService.GetEquipmentCalendar(), app.jsx", "TC-E2E-02, Об’ємний стенд", "Виконано"],
            ["FR-03", "Domain View, Interface View", "PricingAndAvailabilityRules.CalculatePrice()", "TC-UT-02, TC-UT-04", "Виконано"],
            ["FR-04", "Process View (рис. 3.5), Data View", "SqliteRentalRepository.CreateBookingAtomic()", "TC-UT-01, TC-IT-01, TC-IT-02", "Виконано"],
            ["FR-05", "Process View, Data View (waitlist_entries)", "SqliteRentalRepository.AddWaitlistEntry(), RefreshWaitlist()", "TC-IT-05", "Виконано"],
            ["FR-06", "Security View (ASVS V4), UI-04", "RentalApiController.CancelBooking(), ExtendBooking()", "TC-IT-04, TC-IT-07", "Виконано"],
            ["FR-07", "Security View, Operational View", "SqliteRentalRepository.ConfirmBookingAtomic(), RejectBookingAtomic()", "TC-UT-05, TC-IT-06", "Виконано"],
            ["FR-08", "Domain View (формули 2.5–2.6), Data View", "PricingAndAvailabilityRules.CalculateLateReturnPenalty()", "TC-UT-03, TC-IT-06", "Виконано"],
            ["FR-09", "Data View (equipment_units), Interface View", "SqliteRentalRepository.UpdateUnitCondition()", "TC-IT-03", "Виконано"],
            ["NFR-01..08", "Deployment, Security, Delivery Views", "Індекс idx_bookings_unit_interval, PasswordHasher, style.css", "Таблиці 5.3, 5.4, 5.5", "Виконано"],
        ],
        col_widths_mm=[22, 38, 48, 36, 26],
        font_size=10.5
    )

    add_styled_table(
        doc,
        table_num="Б.2",
        table_title="Зведений протокол приймання програмного продукту (за формою Додатка Е.2)",
        headers=["Категорія перевірки", "Кількість перевірок", "Успішно пройдено", "Виявлено помилок", "Підсумковий вердикт"],
        rows=[
            ["Модульні тести доменного ядра (TC-UT-01..05)", "5", "5 (100 %)", "0", "Прийнято"],
            ["Інтеграційні тести БД SQLite та авторизації (TC-IT-01..07)", "7", "7 (100 %)", "0", "Прийнято"],
            ["Перевірка адаптивності (360px, 768px, 1280px) та WCAG 2.2 AA", "6", "6 (100 %)", "0", "Прийнято"],
            ["Навантажувальне тестування (5, 10, 25 віртуальних користувачів)", "3 серії (1 200 запитів)", "3 (100 %)", "0 (0 % помилок)", "Прийнято"],
            ["Тестування обсягом даних (100, 1 000, 10 000 записів)", "3 серії", "3 (100 %)", "0", "Прийнято"],
        ],
        col_widths_mm=[62, 30, 28, 26, 24],
        font_size=10.5
    )

    add_styled_table(
        doc,
        table_num="Б.3",
        table_title="Контрольний список перевірки повноти курсової роботи перед поданням (за формою Додатка Е.3)",
        headers=["№", "Контрольний критерій (відповідно до розділу 1.10 та Додатка Е.3 методичних вказівок)", "Відмітка про виконання"],
        rows=[
            ["1", "Пояснювальна записка містить усі обов’язкові структурні елементи, 5 розділів, висновки, перелік джерел і додатки", "Виконано [Так]"],
            ["2", "Реалізовано всі вимоги паспорта Варіанта 12, включаючи буфери ТО, чергу очікування (Waitlist) та облік пені", "Виконано [Так]"],
            ["3", "Грошові розрахунки (ставка, застава, пеня) виконуються виключно у цілих копійках (long) без типу double", "Виконано [Так]"],
            ["4", "Захист від подвійного бронювання реалізовано на рівні транзакцій СКБД (BEGIN IMMEDIATE) та складеного індексу", "Виконано [Так]"],
            ["5", "Усі перевірки сесії, ролі (CLIENT / MANAGER) та належності ресурсу виконуються на серверній стороні", "Виконано [Так]"],
            ["6", "Помилки HTTP API повертаються у стандартизованому форматі RFC 9457 Problem Details", "Виконано [Так]"],
            ["7", "Репозиторій містить чистий вихідний код без bin/, obj/, node_modules/, скрипти init.sql, seed.sql та README.md", "Виконано [Так]"],
        ],
        col_widths_mm=[12, 126, 32],
        font_size=10.5
    )

    add_styled_table(
        doc,
        table_num="Б.4",
        table_title="Журнал змін і прозорого декларування використання допоміжних засобів (за формою Додатка Е.4)",
        headers=["Етап роботи", "Використані інструментальні та довідкові засоби", "Зміст власної інженерної роботи та перевірки здобувача"],
        rows=[
            ["Проєктування схеми БД та архітектури", "Офіційна документація SQLite 3, ASP.NET Core 10.0, стандарт RFC 9457", "Самостійне проєктування 7 таблиць, обмежень CHECK та складеного індексу інтервалів"],
            ["Реалізація серверного та клієнтського коду", "Середовище розробки, компілятор .NET SDK 10.0, збирач Vite 6, довідковий ШІ-асистент для генерації шаблонних конструкцій", "Повна розробка, налагодження і перевірка доменних правил PricingAndAvailabilityRules та транзакцій"],
            ["Тестування та оформлення документації", "Стенд EquipmentRental.Tests, пакет python-docx, Microsoft Word", "Проведення експериментів на 10 000 записів і 25 VU, аналіз результатів і підготовка записки"],
        ],
        col_widths_mm=[38, 62, 70],
        font_size=10.5
    )

    # ==========================================================================
    # ДОДАТОК В. ЛІСТИНГИ КЛЮЧОВИХ МОДУЛІВ ТА DDL-СХЕМИ БАЗИ ДАНИХ
    # ==========================================================================
    add_structural_heading(doc, "ДОДАТОК В\nЛістинги ключових модулів та DDL-схеми бази даних", page_break=True)

    add_code_listing(
        doc,
        "В.1",
        "DDL-схема реляційної бази даних SQLite (файл sql/init.sql)",
        """PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('CLIENT', 'MANAGER')),
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tariffs (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    billing_unit TEXT NOT NULL CHECK (billing_unit IN ('HOUR', 'DAY')),
    rate_minor INTEGER NOT NULL CHECK (rate_minor > 0),
    deposit_minor INTEGER NOT NULL CHECK (deposit_minor >= 0),
    min_units INTEGER NOT NULL CHECK (min_units >= 1),
    max_units INTEGER NOT NULL CHECK (max_units >= min_units),
    late_fee_per_hour_minor INTEGER NOT NULL CHECK (late_fee_per_hour_minor >= 0)
);

CREATE TABLE IF NOT EXISTS equipment_types (
    id TEXT PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    brand_model TEXT NOT NULL,
    description TEXT NOT NULL,
    specs_json TEXT NOT NULL DEFAULT '{}',
    tariff_id TEXT NOT NULL,
    maintenance_buffer_hours INTEGER NOT NULL DEFAULT 2 CHECK (maintenance_buffer_hours >= 0 AND maintenance_buffer_hours <= 72),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    image_tag TEXT NOT NULL DEFAULT 'default',
    FOREIGN KEY (tariff_id) REFERENCES tariffs(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS equipment_units (
    id TEXT PRIMARY KEY,
    equipment_type_id TEXT NOT NULL,
    inventory_code TEXT NOT NULL UNIQUE,
    serial_number TEXT NOT NULL UNIQUE,
    condition_status TEXT NOT NULL CHECK (condition_status IN ('AVAILABLE', 'IN_MAINTENANCE', 'RETIRED')),
    warehouse_location TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (equipment_type_id) REFERENCES equipment_types(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bookings (
    id TEXT PRIMARY KEY,
    booking_number TEXT NOT NULL UNIQUE,
    unit_id TEXT NOT NULL,
    client_user_id TEXT NOT NULL,
    tariff_id TEXT NOT NULL,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    buffer_ends_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'CONFIRMED', 'ISSUED', 'RETURNED', 'REJECTED', 'CANCELLED')),
    purpose TEXT NOT NULL,
    rejection_reason TEXT,
    billed_units INTEGER NOT NULL CHECK (billed_units > 0),
    unit_rate_minor INTEGER NOT NULL CHECK (unit_rate_minor > 0),
    base_price_minor INTEGER NOT NULL CHECK (base_price_minor > 0),
    deposit_minor INTEGER NOT NULL CHECK (deposit_minor >= 0),
    late_hours INTEGER NOT NULL DEFAULT 0 CHECK (late_hours >= 0),
    late_fee_minor INTEGER NOT NULL DEFAULT 0 CHECK (late_fee_minor >= 0),
    total_price_minor INTEGER NOT NULL CHECK (total_price_minor > 0),
    actual_issued_at TEXT,
    actual_returned_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    FOREIGN KEY (unit_id) REFERENCES equipment_units(id) ON DELETE RESTRICT,
    FOREIGN KEY (client_user_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (tariff_id) REFERENCES tariffs(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_bookings_unit_interval
    ON bookings(unit_id, status, starts_at, buffer_ends_at);"""
    )

    add_code_listing(
        doc,
        "В.2",
        "Фрагмент контролера REST API із серверною авторизацією та обробкою помилок RFC 9457 (RentalApiController.cs)",
        """[HttpPost("bookings")]
public ActionResult<BookingResponseDto> CreateBooking([FromBody] CreateBookingRequestDto request)
{
    var (user, authError) = RequireAuth();
    if (authError != null) return authError;

    try
    {
        if (!DateTimeOffset.TryParse(request.StartsAt, out var startsAt) ||
            !DateTimeOffset.TryParse(request.EndsAt, out var endsAt))
        {
            return BuildProblem(400, "INVALID_DATE_FORMAT",
                "Некоректний формат дати", "Дати початку та завершення мають бути у форматі ISO-8601.");
        }

        // Важливо: clientUserId береться виключно з серверної сесії, а не з тіла запиту клієнта
        var created = _repository.CreateBookingAtomic(
            user!.Id, request.UnitId, startsAt.ToUniversalTime(), endsAt.ToUniversalTime(), request.Purpose.Trim());

        var full = _repository.GetBookingById(created.Id)!;
        return StatusCode(201, RentalApplicationService.MapBookingToDto(full));
    }
    catch (DomainRuleException ex)
    {
        return BuildProblem(ex.HttpStatus, ex.Code, "Відмова у створенні бронювання", ex.Message);
    }
}"""
    )
