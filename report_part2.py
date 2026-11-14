import os
from report_helpers import (
    add_body_p, add_bullet_p, add_section_heading, add_subsection_heading,
    add_styled_table, add_figure, add_code_listing
)

def build_section_3(doc, root_dir):
    # ==========================================================================
    # РОЗДІЛ 3. ПРОЄКТУВАННЯ ВЕБСИСТЕМИ (Д.3.1–Д.3.12, с. 53–73)
    # ==========================================================================
    add_section_heading(doc, "3 ПРОЄКТУВАННЯ ВЕБСИСТЕМИ", page_break=True)

    # 3.1 Архітектурний архетип і проєктні обмеження (Д.3.1)
    add_subsection_heading(doc, "3.1 Архітектурний архетип і проєктні обмеження")
    add_body_p(doc, "Для реалізації вебсистеми оренди обладнання з календарем доступності обрано клієнт-серверний архітектурний архетип із чітким розмежуванням односторінкового клієнтського застосунку (React 19 SPA) та модульного монолітного серверного ядра (ASP.NET Core 10.0 Web API), організованого за принципами чистої пошарової архітектури (Clean / Layered Architecture). Такий вибір зумовлений тим, що перевірка перетину інтервалів із технічною перервою, тарифні розрахунки у копійках, переходи автомата станів бронювання та оповіщення черги очікування вимагають суворої транзакційної узгодженості (ACID) у єдиному реляційному сховищі даних без мережевих накладних витрат мікросервісної взаємодії.")
    add_body_p(doc, "Основні архітектурні обмеження (AC-01..AC-05) та прийняті проєктні компроміси наведено у таблиці 3.1.")

    add_styled_table(
        doc,
        table_num="3.1",
        table_title="Архітектурні обмеження та обґрунтування проєктних компромісів",
        headers=["Код", "Архітектурне обмеження", "Прийняте проєктне рішення", "Інженерний компроміс і наслідок"],
        rows=[
            ["AC-01", "Недопустимість довіри до клієнтських розрахунків і ролей", "Усі перевірки сесії, прав ролі, власника заявки та вартості виконуються на сервері", "Додатковий HTTP-запит при зміні параметрів, проте повний захист від підміни ціни або ID"],
            ["AC-02", "Виключення похибок рухомої коми у грошових розрахунках", "Зберігання та обробка всіх сум у цілих копійках (INTEGER / long)", "Необхідність форматування у гривні на межі DTO, але 100 % фінансова точність"],
            ["AC-03", "Заборона подвійного бронювання при конкурентних запитах", "Використання транзакцій BEGIN IMMEDIATE у SQLite 3 (режим WAL)", "Послідовна сериалізація записів на момент транзакції в обмін на гарантію відсутності колізій"],
            ["AC-04", "Незалежність доменного ядра від інфраструктури БД і HTTP", "Виділення проєкту EquipmentRental.Domain без зовнішніх NuGet-пакетів", "Потреба у мапінгу моделей між шарами, проте висока тестованість правил"],
            ["AC-05", "Простота локального відтворення на навчальному стенді", "Вбудована реляційна СКБД SQLite 3 з автоініціалізацією init.sql і seed.sql", "Обмеження горизонтального масштабування запису, але миттєвий запуск однією командою"],
        ],
        col_widths_mm=[18, 42, 55, 55],
        font_size=11
    )

    # 3.2 Подання користувацького інтерфейсу (UI View, Д.3.2)
    add_subsection_heading(doc, "3.2 Подання користувацького інтерфейсу (UI View)")
    add_body_p(doc, "Користувацький інтерфейс спроєктовано у мінімалістичному функціональному стилі з акцентом на читабельність табличних даних, поекземплярної матриці календаря та фінансових підсумків. Карту станів і переходів між екранами інтерфейсу наведено на рисунку 3.1, а паспорти екранів UI-01..UI-06 — у таблиці 3.2.")

    add_figure(
        doc,
        os.path.join(root_dir, "docs", "diagrams", "fig_3_1_ui_state_map.png"),
        "3.1",
        "Карта станів і переходів користувацького інтерфейсу вебсистеми",
        width_mm=148
    )

    add_styled_table(
        doc,
        table_num="3.2",
        table_title="Паспорти екранів та станів користувацького інтерфейсу вебсистеми",
        headers=["Код екрана", "Назва екрана / Подання", "Основні елементи керування", "Відображення станів (Завантаження / Порожньо / Помилка / Успіх)"],
        rows=[
            ["UI-01", "Каталог обладнання та інвентарний огляд", "Поле пошуку, селектори категорії та тарифу, фільтр часового вікна, картки позицій зі списком інвентарних кодів", "Індикатор завантаження; блок порожньої вибірки з кнопкою скидання; підсвічування доступних одиниць"],
            ["UI-02", "Поекземплярний календар доступності", "Селектор позиції, матриця «екземпляр × дні місяця», легенда станів, перелік активних слотів із буферами ТО", "Позначення комірок: Вільно, Видано, Підтв., Очікує, Буфер, ТО/Спис.; вибір екземпляра кліком по рядку"],
            ["UI-03", "Форма бронювання та тарифний калькулятор", "Вибір інвентарного коду, поля дат початку й кінця, поле мети оренди, блок попереднього розрахунку та Waitlist", "При 400/409 зберігаються введені поля і виводиться пояснення RFC 9457; при 409 відкривається форма Waitlist"],
            ["UI-04", "Особистий кабінет клієнта та черга очікування", "Таблиця власних заявок, кнопки перегляду деталей і скасування, таблиця записів у черзі очікування", "Для гостя — повідомлення 401; для клієнта — індикація статусів WAITING / NOTIFIED та штрафів"],
            ["UI-05", "Робоча панель менеджера та інспектор подій", "Фільтр за статусом, таблиця всіх заявок, кнопки погодження, відхилення, видачі, повернення і продовження, таймлайн подій", "Для ролі CLIENT — попередження 403 FORBIDDEN_ROLE; для MANAGER — повне керування життєвим циклом"],
            ["UI-06", "Панель керування сесією та вибору ролі", "Селектор тестових облікових записів (Гість, Клієнти, Менеджер), індикатор активної ролі у шапці", "Миттєве оновлення серверної сесії HttpOnly Cookie та перезавантаження дозволених даних"],
        ],
        col_widths_mm=[20, 38, 56, 56],
        font_size=11
    )

    # 3.3 Логічне подання (Logical View, Д.3.3)
    add_subsection_heading(doc, "3.3 Логічне подання (Logical View) та межа довіри")
    add_body_p(doc, "Логічне подання системи визначає розподіл функціональних підсистем та межу довіри (Trust Boundary) між клієнтським браузером і серверною частиною. Структурну схему вебсистеми зображено на рисунку 3.2. Браузерний застосунок розглядається як недовірене середовище, відповідальне лише за візуалізацію та зручність введення, тоді як уся перевірка прав доступу, цілісності часових інтервалів і фінансових розрахунків зосереджена всередині контуру ASP.NET Core 10.0 Web API.")

    add_figure(
        doc,
        os.path.join(root_dir, "docs", "diagrams", "fig_3_2_logical_view.png"),
        "3.2",
        "Структурна схема вебсистеми (Logical View) із позначенням серверної межі довіри",
        width_mm=142
    )

    # 3.4 Подання розгортання (Deployment View, Д.3.4)
    add_subsection_heading(doc, "3.4 Подання розгортання (Deployment View)")
    add_body_p(doc, "Топологію фізичного розгортання компонентів вебсистеми подано на UML-діаграмі розгортання (рисунок 3.3), а специфікацію вузлів, середовищ виконання та мережевих протоколів — у таблиці 3.3.")

    add_figure(
        doc,
        os.path.join(root_dir, "docs", "diagrams", "fig_3_3_deployment_view.png"),
        "3.3",
        "Діаграма розгортання (UML Deployment View) вебсистеми оренди обладнання",
        width_mm=145
    )

    add_styled_table(
        doc,
        table_num="3.3",
        table_title="Специфікація вузлів і середовищ розгортання вебсистеми",
        headers=["Вузол розгортання", "Середовище виконання", "Розгорнуті програмні артефакти", "Протокол та порт взаємодії"],
        rows=[
            ["Клієнтський пристрій користувача (ПК / Планшет / Смартфон)", "Сучасний веббраузер (Edge / Chrome / Firefox)", "Клієнтський бандл React 19 SPA (index.html, index.js, index.css)", "HTTP/1.1 або HTTPS (JSON REST API, Cookie equiprent_session)"],
            ["Сервер застосунку (ОС Windows 11 x64 / Linux)", ".NET 10.0 Runtime + вебсервер Kestrel", "EquipmentRental.WebApi.dll, Application.dll, Domain.dll, Infrastructure.dll", "Вхідний порт TCP 5080 (http://localhost:5080)"],
            ["Локальне файлове сховище сервера", "Вбудований рушій SQLite 3 (режим WAL)", "Файл БД Data/equipment_rental.db, скрипти sql/init.sql та sql/seed.sql", "Локальний файловий ввід/вивід через ADO.NET драйвер Microsoft.Data.Sqlite"],
        ],
        col_widths_mm=[42, 38, 52, 38],
        font_size=11
    )

    # 3.5 Подання шарів і компонентів (Design View, Д.3.5)
    add_subsection_heading(doc, "3.5 Подання шарів і компонентів (Design View)")
    add_body_p(doc, "Програмну систему розділено на чотири ізольовані шари з односпрямованим графом залежностей, спрямованим до доменного ядра (принцип інверсії залежностей SOLID). Схему взаємодії шарів наведено на рисунку 3.4, а матрицю їхньої відповідальності — у таблиці 3.4.")

    add_figure(
        doc,
        os.path.join(root_dir, "docs", "diagrams", "fig_3_4_design_layers.png"),
        "3.4",
        "Подання архітектурних шарів і компонентів (Design View) за принципом інверсії залежностей",
        width_mm=145
    )

    add_styled_table(
        doc,
        table_num="3.4",
        table_title="Матриця відповідальності архітектурних шарів та дозволених залежностей",
        headers=["Назва шару (Проєкт .NET / Клієнт)", "Основні класи та модулі", "Зона відповідальності шару", "Дозволені залежності"],
        rows=[
            ["Presentation Layer (EquipmentRental.WebApi + React SPA)", "RentalApiController, SessionAuthManager, Program.cs, client/src/app.jsx", "Приймання HTTP-запитів, перевірка сесії та ролі, формування відповідей RFC 9457, рендеринг UI", "Залежить від Application та Domain"],
            ["Application Layer (EquipmentRental.Application)", "RentalApplicationService, ContractsAndDtos.cs", "Координація прикладних сценаріїв каталогу, календаря, попереднього розрахунку та мапінг DTO", "Залежить лише від Domain"],
            ["Domain Layer (EquipmentRental.Domain)", "Entities.cs, Money, PricingAndAvailabilityRules.cs, IRentalRepository.cs", "Чисті предметні правила: перетин інтервалів з буфером ТО, калькуляція тарифів і пені, автомат станів", "Не має залежностей від інших шарів"],
            ["Infrastructure Layer (EquipmentRental.Infrastructure)", "SqliteRentalRepository.cs, PasswordHasher.cs", "Транзакційна робота з БД SQLite (BEGIN IMMEDIATE), параметризовані SQL-запити, хешування PBKDF2", "Реалізує IRentalRepository із шару Domain"],
        ],
        col_widths_mm=[42, 42, 54, 32],
        font_size=11
    )

    # 3.6 Подання процесів і взаємодії у часі (Process View, Д.3.6)
    add_subsection_heading(doc, "3.6 Подання процесів і взаємодії у часі (Process View)")
    add_body_p(doc, "Динаміку взаємодії компонентів у часі під час виконання основного наскрізного сценарію — оформлення заявки на оренду з транзакційною перевіркою календаря та альтернативним переходом до черги очікування — відображено на UML-діаграмі послідовності (Sequence Diagram) на рисунку 3.5. Використання команди BEGIN IMMEDIATE у SQLite гарантує, що з моменту початку перевірки інтервалу жодне паралельне з’єднання не може вклинитися із записом конкуруючої заявки до завершення поточної транзакції (COMMIT або ROLLBACK).")

    add_figure(
        doc,
        os.path.join(root_dir, "docs", "diagrams", "fig_3_5_sequence_booking.png"),
        "3.5",
        "Діаграма послідовності (UML Sequence Diagram) сценарію атомарного створення бронювання",
        width_mm=155
    )

    # 3.7 Подання даних (Data View, Д.3.7)
    add_subsection_heading(doc, "3.7 Подання даних (Data View): ER-модель, класи та DTO")
    add_body_p(doc, "Реляційна схема бази даних спроєктована у третій нормальній формі (3NF) і складається із 7 взаємопов’язаних таблиць: users, tariffs, equipment_types, equipment_units, bookings, rental_events та waitlist_entries. Фізичну діаграму «сутність-зв’язок» (ER-модель) наведено на рисунку 3.6, діаграму основних доменних класів — на рисунку 3.7, а діаграму структур передавання даних (DTO) — на рисунку 3.8. Відповідно до правил моделювання подання даних (рисунок Д.11 методичних вказівок), структури CreateBookingRequestDto, BookingResponseDto та ApiErrorResponse є пасивними контрактами вхідного та альтернативних вихідних пакетів HTTP-обміну (вони не викликають одна одну напряму), проте пов’язані з операцією POST /api/bookings і містять композитні зв’язки із вкладеними масивами подій RentalEventDto[] та помилок полів FieldErrorDto[].")

    add_figure(
        doc,
        os.path.join(root_dir, "docs", "diagrams", "fig_3_6_er_diagram.png"),
        "3.6",
        "Фізична ER-модель реляційної бази даних вебсистеми оренди обладнання (7 таблиць)",
        width_mm=158
    )

    add_figure(
        doc,
        os.path.join(root_dir, "docs", "diagrams", "fig_3_7_domain_classes.png"),
        "3.7",
        "Діаграма основних доменних класів та правил шару EquipmentRental.Domain",
        width_mm=148
    )

    add_figure(
        doc,
        os.path.join(root_dir, "docs", "diagrams", "fig_3_8_dto_contracts.png"),
        "3.8",
        "Діаграма контрактів передавання даних (DTO) та структури помилки RFC 9457",
        width_mm=145
    )

    add_body_p(doc, "Словник даних основних таблиць реляційного сховища разом із обмеженнями цілісності (PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK) та індексами подано у таблиці 3.5.")

    add_styled_table(
        doc,
        table_num="3.5",
        table_title="Словник даних таблиць реляційної бази даних SQLite",
        headers=["Таблиця БД", "Ключові поля та типи даних", "Обмеження цілісності (Constraints)", "Індекси та призначення"],
        rows=[
            ["users", "id (TEXT PK), email (TEXT UNIQUE), full_name, phone, role, password_hash, created_at", "CHECK (role IN ('CLIENT', 'MANAGER')); NOT NULL на всіх обов’язкових полях", "UNIQUE індекс за полем email для швидкого входу"],
            ["tariffs", "id (TEXT PK), code (UNIQUE), name, billing_unit, rate_minor (INT), deposit_minor (INT), min_units, max_units, late_fee_per_hour_minor", "CHECK (billing_unit IN ('HOUR','DAY')); CHECK (rate_minor > 0 AND deposit_minor >= 0); CHECK (max_units >= min_units)", "Зберігання ставок, застави та пені у цілих копійках"],
            ["equipment_types", "id (TEXT PK), slug (UNIQUE), title, category, brand_model, specs_json, tariff_id (FK), maintenance_buffer_hours (INT), active", "FK tariff_id -> tariffs(id); CHECK (maintenance_buffer_hours >= 0 AND maintenance_buffer_hours <= 72)", "idx_equipment_types_category (category, active) для фільтрації каталогу"],
            ["equipment_units", "id (TEXT PK), equipment_type_id (FK), inventory_code (UNIQUE), serial_number (UNIQUE), condition_status, warehouse_location", "FK equipment_type_id -> equipment_types(id) ON DELETE CASCADE; CHECK (condition_status IN ('AVAILABLE','IN_MAINTENANCE','RETIRED'))", "idx_equipment_units_type_status (equipment_type_id, condition_status)"],
            ["bookings", "id (TEXT PK), booking_number (UNIQUE), unit_id (FK), client_user_id (FK), tariff_id (FK), starts_at, ends_at, buffer_ends_at, status, billed_units, total_price_minor, late_hours, late_fee_minor, version", "CHECK (status IN ('PENDING','CONFIRMED','ISSUED','RETURNED','REJECTED','CANCELLED')); CHECK (billed_units > 0 AND total_price_minor >= 0)", "idx_bookings_unit_interval (unit_id, status, starts_at, buffer_ends_at); idx_bookings_client (client_user_id)"],
            ["rental_events", "id (TEXT PK), booking_id (FK), actor_user_id (FK), event_type, old_status, new_status, occurred_at, notes, penalty_added_minor", "FK booking_id -> bookings(id) ON DELETE CASCADE; CHECK (penalty_added_minor >= 0)", "idx_rental_events_booking (booking_id, occurred_at) для аудиту змін"],
            ["waitlist_entries", "id (TEXT PK), equipment_type_id (FK), preferred_unit_id (FK), client_user_id (FK), desired_starts_at, desired_ends_at, status, contact_note", "CHECK (status IN ('WAITING','NOTIFIED','FULFILLED','CANCELLED'))", "idx_waitlist_type_status (equipment_type_id, status, desired_starts_at)"],
        ],
        col_widths_mm=[28, 48, 48, 46],
        font_size=10.5
    )

    # 3.8 Подання інтерфейсів і контрактів обміну (Interface View, Д.3.8)
    add_subsection_heading(doc, "3.8 Подання інтерфейсів і контрактів обміну (Interface View)")
    add_body_p(doc, "Обмін даними між клієнтським застосунком і сервером здійснюється через типізований REST API у форматі JSON. Усі відповіді про помилки уніфіковано відповідно до міжнародного стандарту IETF RFC 9457 (Problem Details for HTTP APIs) [6]: кожна помилка містить поля type, title, status, detail, машиночитний код code, ідентифікатор трасування traceId та масив помилок окремих полів fieldErrors. Каталог HTTP-операцій REST API наведено у таблиці 3.6.")

    add_styled_table(
        doc,
        table_num="3.6",
        table_title="Каталог основних HTTP-операцій серверного REST API вебсистеми",
        headers=["Метод і маршрут URI", "Призначення операції", "Роль доступу", "Коди успіху", "Коди помилок (RFC 9457)"],
        rows=[
            ["GET /api/health", "Перевірка працездатності сервера та підключення до SQLite", "Публічний", "200 OK", "500 INTERNAL_ERROR"],
            ["POST /api/auth/login", "Автентифікація користувача та встановлення HttpOnly сесії", "Публічний", "200 OK", "400 VALIDATION_ERROR, 401 INVALID_CREDENTIALS"],
            ["GET /api/catalog", "Пошук і фільтрація каталогу обладнання та інвентарних одиниць", "Публічний", "200 OK", "400 END_BEFORE_START"],
            ["GET /api/catalog/{id}/calendar", "Отримання активних слотів і буферів ТО для календаря позиції", "Публічний", "200 OK", "404 TYPE_NOT_FOUND"],
            ["POST /api/bookings/preview", "Попередній розрахунок вартості, застави та перевірка інтервалу", "Публічний", "200 OK", "400, 404 UNIT_NOT_FOUND"],
            ["POST /api/bookings", "Атомарне створення нової заявки на оренду екземпляра", "CLIENT, MANAGER", "201 Created", "400, 401, 404, 409 INTERVAL_CONFLICT"],
            ["POST /api/bookings/{id}/confirm", "Погодження заявки менеджером (PENDING -> CONFIRMED)", "MANAGER", "200 OK", "400 INVALID_TRANSITION, 401, 403 FORBIDDEN_ROLE"],
            ["POST /api/bookings/{id}/reject", "Мотивоване відхилення заявки та оповіщення черги очікування", "MANAGER", "200 OK", "400 REJECTION_REASON_REQUIRED, 403"],
            ["POST /api/bookings/{id}/issue", "Реєстрація фактичної видачі обладнання (CONFIRMED -> ISSUED)", "MANAGER", "200 OK", "400 INVALID_TRANSITION, 403"],
            ["POST /api/bookings/{id}/return", "Приймання повернення з автоматичним розрахунком пені за прострочення", "MANAGER", "200 OK", "400 INVALID_RETURN_DATE, 403"],
            ["POST /api/bookings/{id}/extend", "Продовження активної оренди з перевіркою відсутності конфлікту", "Власник, MANAGER", "200 OK", "400, 403 NOT_OWNER, 409 INTERVAL_CONFLICT"],
            ["POST /api/bookings/{id}/cancel", "Скасування заявки та автоматичне сповіщення черги очікування", "Власник, MANAGER", "200 OK", "400, 403 NOT_OWNER"],
            ["POST /api/waitlist", "Постановка клієнта в чергу очікування на зайнятий інтервал", "CLIENT, MANAGER", "201 Created", "400 END_BEFORE_START, 401"],
        ],
        col_widths_mm=[42, 48, 26, 22, 32],
        font_size=10.5
    )

    # 3.9 Подання безпеки (Security View, Д.3.9)
    add_subsection_heading(doc, "3.9 Подання безпеки (Security View за OWASP та ASVS 5.0)")
    add_body_p(doc, "Проєктування механізмів захисту виконано відповідно до вимог стандартів OWASP Top 10:2025 [9], OWASP Application Security Verification Standard (ASVS 5.0.0) [10] та настанов цифрової автентифікації NIST SP 800-63B-4 [11]. Матрицю загроз і реалізованих контрзаходів наведено у таблиці 3.7.")

    add_styled_table(
        doc,
        table_num="3.7",
        table_title="Матриця загроз інформаційної безпеки та реалізованих захисних механізмів",
        headers=["Категорія OWASP Top 10:2025 / ASVS 5.0.0", "Потенційний вектор атаки у системі оренди", "Реалізований серверний контрзахід", "Метод перевірки"],
        rows=[
            ["A01:2025 Broken Access Control (ASVS V4)", "Спроба клієнта скасувати чужу заявку або викликати метод підтвердження / повернення", "Перевірка ролі RequireRole(MANAGER) та власника booking.ClientUserId != user.Id (403 Forbidden); clientUserId береться лише із сесії", "Автотести TC-IT-04, TC-IT-06"],
            ["A02:2025 Security Misconfiguration", "Витік внутрішніх стек-трейсів БД або секретів у відповідях сервера", "Уніфіковані відповіді RFC 9457 без розкриття структури БД; винесення шляхів у змінні середовища (.env.example)", "Перевірка заголовків і тіла помилок 400/409"],
            ["A04:2025 Cryptographic Failures (NIST 800-63B)", "Зберігання паролів у відкритому вигляді або зі слабким хешем без солі", "Хешування паролів алгоритмом PBKDF2-HMAC-SHA256 (100 000 ітерацій, випадкова 128-бітна сіль, порівняння FixedTimeEquals)", "Перевірка класу PasswordHasher"],
            ["A05:2025 Injection (SQLi / XSS, ASVS V5)", "Введення SQL-конструкцій у рядок пошуку каталогу або XSS-скриптів у поле мети оренди", "Виключно параметризовані запити ($param у Microsoft.Data.Sqlite); автоматичне екранування DOM у React 19", "Інтеграційне тестування спецсимволів"],
            ["A06:2025 Insecure Design (Race Conditions)", "Одночасне надсилання двох запитів на бронювання одного інвентарного номера", "Серіалізація перевірки та вставки у транзакції BEGIN IMMEDIATE + оптимістичне версіонування version", "Навантажувальний тест конкурентного бронювання"],
            ["A07:2025 Authentication Failures (ASVS V3)", "Викрадення сесійного токена через JavaScript або міжсайтові запити", "Зберігання токена у реп’яшку з прапорцями HttpOnly=true, SameSite=Lax та обмеженим часом життя 8 год", "Інспекція параметрів CookieOptions"],
        ],
        col_widths_mm=[38, 42, 56, 34],
        font_size=10.5
    )

    # 3.10 Операційне подання (Operational View, Д.3.10)
    add_subsection_heading(doc, "3.10 Операційне подання (Operational View)")
    add_body_p(doc, "Операційне подання визначає механізми спостережуваності, аудиту дій користувачів та резервного копіювання даних під час експлуатації системи (таблиця 3.8). Кожна зміна стану бронювання нерозривно в одній транзакції записує незмінний запис у таблицю rental_events із фіксацією виконавця (actor_user_id), старого й нового статусів, часової мітки UTC та нарахованої суми пені.")

    add_styled_table(
        doc,
        table_num="3.8",
        table_title="Регламент операційного моніторингу, журналювання та резервного копіювання",
        headers=["Операційний аспект", "Реалізований механізм у вебсистемі", "Цільовий показник / Регламент"],
        rows=[
            ["Перевірка життєздатності (Health Check)", "Ендпоінт GET /api/health перевіряє доступність вебсервера та з’єднання з SQLite", "Час відповіді <= 5 мс, статус 200 OK"],
            ["Предметний журнал аудиту (Audit Trail)", "Таблиця rental_events фіксує події CREATED, CONFIRMED, REJECTED, ISSUED, RETURNED, EXTENDED, CANCELLED", "100 % покриття всіх мутацій статусів бронювань"],
            ["Трасування помилок (Traceability)", "Кожна відповідь RFC 9457 містить унікальний ідентифікатор запиту HttpContext.TraceIdentifier", "Миттєва кореляція повідомлення клієнта із серверним логом"],
            ["Резервне копіювання та відновлення БД", "Гаряче копіювання файлу Data/equipment_rental.db у режимі WAL; повне відтворення схеми зі скриптів sql/init.sql та sql/seed.sql", "Час відновлення схеми та демонстраційних даних RTO <= 5 с"],
        ],
        col_widths_mm=[42, 82, 46],
        font_size=11
    )

    # 3.11 Інфраструктурне подання та 3.12 Стратегія доставки і паспорт стека (Д.3.11–Д.3.12)
    add_subsection_heading(doc, "3.11 Інфраструктурне подання (Infrastructure View)")
    add_body_p(doc, "Конфігурація вебсистеми відокремлена від вихідного коду і керується через змінні середовища операційної системи, перелік яких задокументовано у таблиці 3.9 та файлі .env.example.")

    add_styled_table(
        doc,
        table_num="3.9",
        table_title="Специфікація змінних середовища та параметрів інфраструктури",
        headers=["Змінна середовища / Параметр", "Значення за замовчуванням", "Призначення параметра"],
        rows=[
            ["ASPNETCORE_ENVIRONMENT", "Development", "Режим роботи середовища виконання ASP.NET Core"],
            ["ASPNETCORE_URLS", "http://localhost:5080", "Мережева адреса і TCP-порт прослуховування вебсервера Kestrel"],
            ["EQUIPRENT_DB_PATH", "./Data/equipment_rental.db", "Шлях до файлу реляційної бази даних SQLite 3"],
            ["PRAGMA journal_mode", "WAL (Write-Ahead Logging)", "Режим неблокуючого конкурентного читання та запису СКБД"],
            ["PRAGMA busy_timeout", "5000 (мс)", "Максимальний час очікування звільнення блокування таблиці при конкурентному записі"],
        ],
        col_widths_mm=[48, 46, 76],
        font_size=11
    )

    add_subsection_heading(doc, "3.12 Стратегія доставки та паспорт стека (Delivery View)")
    add_body_p(doc, "Стратегія доставки програмного продукту базується на єдиному відтворюваному конвеєрі збирання: клієнтський застосунок компілюється засобами Vite у статичні ресурси каталогу src/EquipmentRental.WebApi/wwwroot, після чого серверне рішення EquipmentRental.sln збирається компілятором .NET SDK 10.0 і проходить автоматизований набір модульних та інтеграційних тестів. Зведений паспорт технологічного стека наведено у таблиці 3.10.")

    add_styled_table(
        doc,
        table_num="3.10",
        table_title="Паспорт технологічного стека вебсистеми оренди обладнання",
        headers=["Рівень системи", "Технологія / Бібліотека", "Версія", "Обґрунтування вибору для Варіанта 12"],
        rows=[
            ["Серверна платформа", "C# 13 / .NET SDK & Runtime", "10.0.100", "Висока продуктивність, сувора статична типізація, підтримка Clean Architecture"],
            ["Вебфреймворк API", "ASP.NET Core Web API (Kestrel)", "10.0.0", "Вбудована валідація моделей, підтримка Problem Details (RFC 9457), високий RPS"],
            ["Реляційна СКБД і драйвер", "SQLite 3 + Microsoft.Data.Sqlite", "10.0.0", "Підтримка транзакцій BEGIN IMMEDIATE, режиму WAL, обмежень CHECK і складених індексів"],
            ["Клієнтський інтерфейс", "React + React DOM", "19.0.0", "Декларативне оновлення матриці календаря та калькулятора без перезавантаження сторінки"],
            ["Інструмент збирання SPA", "Vite", "6.2.0", "Швидке модульне збирання та мінімізація клієнтського бандла"],
            ["Контроль якості та E2E", "EquipmentRental.Tests + Playwright", "1.50+", "Автоматизована перевірка доменних інваріантів, навантаження та реального UI"],
        ],
        col_widths_mm=[36, 46, 22, 66],
        font_size=11
    )

    add_body_p(doc, "Висновки до розділу 3. Виконано повне проєктування вебсистеми за 12 архітектурними поданнями. Розроблено реляційну модель даних із 7 таблиць у 3NF, визначено контракти REST API з обробкою помилок за RFC 9457 та закладено багаторівневі механізми захисту за OWASP Top 10:2025 і ASVS 5.0.0.")
