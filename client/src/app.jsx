import React, { useState, useEffect, useCallback } from "react";
import { requestJson, setAuthSession } from "./api.js";

const CALENDAR_DAYS = [
  "2026-11-12", "2026-11-13", "2026-11-14", "2026-11-15", "2026-11-16",
  "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20", "2026-11-21",
  "2026-11-22", "2026-11-23"
];

function formatDateTimeShort(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(d.getUTCDate())}.${pad(d.getUTCMonth() + 1)}.${d.getUTCFullYear()} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
}

function statusBadgeInfo(status) {
  switch (status) {
    case "PENDING":
      return { label: "ОЧІКУЄ ПОГОДЖЕННЯ", cls: "badge-pending", symbol: "" };
    case "CONFIRMED":
      return { label: "ПІДТВЕРДЖЕНО", cls: "badge-confirmed", symbol: "" };
    case "ISSUED":
      return { label: "ВИДАНО В ОРЕНДУ", cls: "badge-issued", symbol: "" };
    case "RETURNED":
      return { label: "ПОВЕРНУТО", cls: "badge-returned", symbol: "" };
    case "REJECTED":
      return { label: "ВІДХИЛЕНО", cls: "badge-rejected", symbol: "" };
    case "CANCELLED":
      return { label: "СКАСОВАНО", cls: "badge-cancelled", symbol: "" };
    default:
      return { label: status, cls: "badge-neutral", symbol: "" };
  }
}

function unitConditionBadge(status) {
  switch (status) {
    case "AVAILABLE":
      return { label: "Доступний", cls: "unit-avail", icon: "" };
    case "IN_MAINTENANCE":
      return { label: "На ТО", cls: "unit-maint", icon: "" };
    case "RETIRED":
      return { label: "Списаний", cls: "unit-retired", icon: "" };
    default:
      return { label: status, cls: "unit-maint", icon: "" };
  }
}

export function EquipmentRentalApp() {
  const [activeTab, setActiveTab] = useState("catalog"); // catalog | details | mybookings | manager
  const [demoUsers, setDemoUsers] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);

  // Каталог та фільтри
  const [catalog, setCatalog] = useState([]);
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [billingFilter, setBillingFilter] = useState("ALL");
  const [filterFrom, setFilterFrom] = useState("2026-11-15T09:00");
  const [filterTo, setFilterTo] = useState("2026-11-17T09:00");
  const [usePeriodFilter, setUsePeriodFilter] = useState(false);
  const [catalogError, setCatalogError] = useState(null);

  // Обраний тип обладнання, його календар і форма бронювання
  const [selectedEquipment, setSelectedEquipment] = useState(null);
  const [calendarSlots, setCalendarSlots] = useState([]);
  const [selectedUnitId, setSelectedUnitId] = useState("");
  const [bookingStart, setBookingStart] = useState("2026-11-18T09:00");
  const [bookingEnd, setBookingEnd] = useState("2026-11-20T09:00");
  const [bookingPurpose, setBookingPurpose] = useState("Лабораторні випробування автономного стенда кафедри ІС");
  const [previewData, setPreviewData] = useState(null);
  const [bookingSubmitting, setBookingSubmitting] = useState(false);
  const [bookingAlert, setBookingAlert] = useState(null);
  const [waitlistNote, setWaitlistNote] = useState("Повідомте телефоном або email при звільненні слота");

  // Особистий кабінет та панель менеджера
  const [bookingsList, setBookingsList] = useState([]);
  const [waitlistEntries, setWaitlistEntries] = useState([]);
  const [statusFilterMgr, setStatusFilterMgr] = useState("ALL");
  const [selectedBookingDetails, setSelectedBookingDetails] = useState(null);
  const [actionAlert, setActionAlert] = useState(null);
  const [mgrNotesInput, setMgrNotesInput] = useState("");
  const [mgrReturnTimeInput, setMgrReturnTimeInput] = useState("2026-11-16T09:00");
  const [extendDateInput, setExtendDateInput] = useState("2026-11-17T09:00");

  // Завантаження користувачів стенда та поточної сесії
  useEffect(() => {
    requestJson("GET", "/api/auth/users")
      .then((users) => {
        setDemoUsers(users || []);
        // За замовчуванням для зручності демонстрації авторизуємо клієнта Коваленка О.І., якщо сесія ще не вибрана
        return requestJson("GET", "/api/auth/me").then((me) => ({ users, me }));
      })
      .then(({ users, me }) => {
        if (me?.authenticated && me.user) {
          setCurrentUser(me.user);
        } else if (users && users.length > 0) {
          const defaultClient = users.find((u) => u.role === "CLIENT") || users[0];
          handleQuickSwitchUser(defaultClient.email);
        }
      })
      .catch(() => {});
  }, []);

  const loadCatalog = useCallback(() => {
    setLoadingCatalog(true);
    setCatalogError(null);
    const params = new URLSearchParams();
    if (searchQuery.trim()) params.set("search", searchQuery.trim());
    if (categoryFilter !== "ALL") params.set("category", categoryFilter);
    if (billingFilter !== "ALL") params.set("billingUnit", billingFilter);
    if (usePeriodFilter && filterFrom && filterTo) {
      params.set("availableFrom", filterFrom + ":00Z");
      params.set("availableTo", filterTo + ":00Z");
    }

    requestJson("GET", `/api/catalog?${params.toString()}`)
      .then((data) => {
        setCatalog(data || []);
        if (data && data.length > 0 && !selectedEquipment) {
          setSelectedEquipment(data[0]);
          const firstAvailUnit = data[0].units.find((u) => u.conditionStatus === "AVAILABLE") || data[0].units[0];
          if (firstAvailUnit) setSelectedUnitId(firstAvailUnit.id);
        }
      })
      .catch((err) => {
        setCatalogError(err);
      })
      .finally(() => setLoadingCatalog(false));
  }, [searchQuery, categoryFilter, billingFilter, usePeriodFilter, filterFrom, filterTo, selectedEquipment]);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  const loadEquipmentCalendarAndPreview = useCallback((eq, unitId, startStr, endStr) => {
    if (!eq) return;
    requestJson("GET", `/api/catalog/${eq.id}/calendar?from=2026-11-11T00:00:00Z&to=2026-11-25T23:59:59Z`)
      .then((slots) => setCalendarSlots(slots || []))
      .catch(() => setCalendarSlots([]));

    if (unitId && startStr && endStr) {
      requestJson("POST", "/api/bookings/preview", {
        unitId,
        startsAt: startStr.endsWith("Z") ? startStr : startStr + ":00Z",
        endsAt: endStr.endsWith("Z") ? endStr : endStr + ":00Z"
      })
        .then((res) => setPreviewData(res))
        .catch((err) => {
          setPreviewData({
            isAvailable: false,
            errorCode: err.code,
            errorMessage: err.detail
          });
        });
    }
  }, []);

  useEffect(() => {
    if (selectedEquipment && selectedUnitId) {
      loadEquipmentCalendarAndPreview(selectedEquipment, selectedUnitId, bookingStart, bookingEnd);
    }
  }, [selectedEquipment, selectedUnitId, bookingStart, bookingEnd, loadEquipmentCalendarAndPreview]);

  const loadBookingsAndWaitlist = useCallback(() => {
    if (!currentUser) {
      setBookingsList([]);
      setWaitlistEntries([]);
      return;
    }
    const statusParam = currentUser.role === "MANAGER" && statusFilterMgr !== "ALL"
      ? `?status=${encodeURIComponent(statusFilterMgr)}`
      : "";
    requestJson("GET", `/api/bookings${statusParam}`)
      .then((list) => setBookingsList(list || []))
      .catch(() => setBookingsList([]));

    requestJson("GET", "/api/waitlist")
      .then((w) => setWaitlistEntries(w || []))
      .catch(() => setWaitlistEntries([]));
  }, [currentUser, statusFilterMgr]);

  useEffect(() => {
    loadBookingsAndWaitlist();
  }, [loadBookingsAndWaitlist]);

  function handleQuickSwitchUser(email) {
    if (!email || email === "GUEST") {
      requestJson("POST", "/api/auth/logout").finally(() => {
        setAuthSession("", "");
        setCurrentUser(null);
        setBookingsList([]);
        setWaitlistEntries([]);
      });
      return;
    }
    requestJson("POST", "/api/auth/login", { email, password: "" })
      .then((res) => {
        setAuthSession(res.sessionToken, res.user.id);
        setCurrentUser(res.user);
        setActionAlert({
          type: "success",
          text: `Виконано вхід: ${res.user.fullName} (Роль: ${res.user.role})`
        });
      })
      .catch((err) => {
        setActionAlert({ type: "error", text: err.detail });
      });
  }

  function handleSelectEquipmentCard(eq) {
    setSelectedEquipment(eq);
    const firstUnit = eq.units.find((u) => u.conditionStatus === "AVAILABLE") || eq.units[0];
    if (firstUnit) setSelectedUnitId(firstUnit.id);
    setBookingAlert(null);
    setActiveTab("details");
  }

  function handleCreateBooking(e) {
    e.preventDefault();
    if (bookingSubmitting) return;
    setBookingSubmitting(true);
    setBookingAlert(null);

    requestJson("POST", "/api/bookings", {
      unitId: selectedUnitId,
      startsAt: bookingStart.endsWith("Z") ? bookingStart : bookingStart + ":00Z",
      endsAt: bookingEnd.endsWith("Z") ? bookingEnd : bookingEnd + ":00Z",
      purpose: bookingPurpose
    })
      .then((created) => {
        setBookingAlert({
          type: "success",
          code: "CREATED_201",
          title: `Заявку ${created.bookingNumber} успішно створено!`,
          detail: `Екземпляр ${created.inventoryCode} заброньовано у статусі PENDING. Сума оренди: ${created.totalPriceFormatted}, застава: ${created.depositFormatted}, тех. перерва до ${formatDateTimeShort(created.bufferEndsAt)}.`
        });
        loadEquipmentCalendarAndPreview(selectedEquipment, selectedUnitId, bookingStart, bookingEnd);
        loadBookingsAndWaitlist();
        loadCatalog();
      })
      .catch((err) => {
        setBookingAlert({
          type: "error",
          code: err.code,
          title: err.title,
          detail: err.detail
        });
      })
      .finally(() => setBookingSubmitting(false));
  }

  function handleJoinWaitlist() {
    if (!selectedEquipment) return;
    setBookingAlert(null);
    requestJson("POST", "/api/waitlist", {
      equipmentTypeId: selectedEquipment.id,
      preferredUnitId: selectedUnitId || null,
      desiredStartsAt: bookingStart.endsWith("Z") ? bookingStart : bookingStart + ":00Z",
      desiredEndsAt: bookingEnd.endsWith("Z") ? bookingEnd : bookingEnd + ":00Z",
      contactNote: waitlistNote
    })
      .then((entry) => {
        setBookingAlert({
          type: "success",
          code: "WAITLIST_201",
          title: `Додано в чергу очікування (${entry.id})!`,
          detail: `Коли екземпляр «${selectedEquipment.title}» звільниться у періоді ${formatDateTimeShort(entry.desiredStartsAt)} – ${formatDateTimeShort(entry.desiredEndsAt)}, статус зміниться на NOTIFIED.`
        });
        loadBookingsAndWaitlist();
      })
      .catch((err) => {
        setBookingAlert({
          type: "error",
          code: err.code,
          title: err.title,
          detail: err.detail
        });
      });
  }

  function handleInspectBooking(bookingId) {
    requestJson("GET", `/api/bookings/${bookingId}`)
      .then((full) => {
        setSelectedBookingDetails(full);
        setExtendDateInput(full.endsAt.slice(0, 16));
        setMgrReturnTimeInput(full.endsAt.slice(0, 16));
      })
      .catch((err) => {
        setActionAlert({ type: "error", text: `${err.code}: ${err.detail}` });
      });
  }

  function handleBookingTransition(bookingId, action, payload = {}) {
    setActionAlert(null);
    requestJson("POST", `/api/bookings/${bookingId}/${action}`, payload)
      .then((updated) => {
        setSelectedBookingDetails(updated);
        loadBookingsAndWaitlist();
        loadCatalog();
        if (selectedEquipment) {
          loadEquipmentCalendarAndPreview(selectedEquipment, selectedUnitId, bookingStart, bookingEnd);
        }
        setActionAlert({
          type: "success",
          text: `Операцію «${action.toUpperCase()}» для заявки ${updated.bookingNumber} виконано. Новий статус: ${updated.status} (версія v${updated.version}).`
        });
      })
      .catch((err) => {
        setActionAlert({
          type: "error",
          text: `[HTTP ${err.status} / ${err.code}] ${err.detail}`
        });
      });
  }

  // Підсумкові показники для каталогу
  const totalTypesCount = catalog.length;
  const totalUnitsInCatalog = catalog.reduce((acc, item) => acc + item.totalUnitsCount, 0);
  const availUnitsInCatalog = catalog.reduce((acc, item) => acc + item.availableUnitsCount, 0);

  return (
    <div className="app-shell">
      {/* Шапка системи з перемикачем ролей та навігацією */}
      <header className="top-header" role="banner">
        <div className="brand-block">
          <div>
            <h1 className="brand-title">Оренда обладнання з календарем доступності</h1>
            <p className="brand-subtitle">
              Варіант 12 | Сливка М. О., гр. АІ-243
            </p>
          </div>
        </div>

        <div className="auth-switcher" aria-label="Панель автентифікації та вибору ролі">
          <label htmlFor="role-select" className="auth-label">Активний обліковий запис (сесія):</label>
          <select
            id="role-select"
            className="auth-select"
            value={currentUser ? currentUser.email : "GUEST"}
            onChange={(e) => handleQuickSwitchUser(e.target.value)}
          >
            <option value="GUEST">Гість (Неавтентифікований перегляд)</option>
            {demoUsers.map((u) => (
              <option key={u.id} value={u.email}>
                [{u.role === "MANAGER" ? "МЕНЕДЖЕР" : "КЛІЄНТ"}] {u.fullName} ({u.email})
              </option>
            ))}
          </select>
          {currentUser ? (
            <span className={`role-pill role-${currentUser.role.toLowerCase()}`}>
              {currentUser.role === "MANAGER" ? "Роль: МЕНЕДЖЕР" : "Роль: КЛІЄНТ"}
            </span>
          ) : (
            <span className="role-pill role-guest">Роль: ГІСТЬ</span>
          )}
        </div>
      </header>

      {/* Головне навігаційне меню (доступне з клавіатури Tab/Enter) */}
      <nav className="main-nav" aria-label="Основна навігація системи">
        <button
          type="button"
          className={`nav-btn ${activeTab === "catalog" ? "active" : ""}`}
          onClick={() => setActiveTab("catalog")}
        >
          1. Каталог та огляд екземплярів ({totalTypesCount})
        </button>
        <button
          type="button"
          className={`nav-btn ${activeTab === "details" ? "active" : ""}`}
          onClick={() => setActiveTab("details")}
        >
          2. Календар доступності та оформлення оренди
          {selectedEquipment ? `: ${selectedEquipment.title.slice(0, 28)}…` : ""}
        </button>
        <button
          type="button"
          className={`nav-btn ${activeTab === "mybookings" ? "active" : ""}`}
          onClick={() => setActiveTab("mybookings")}
        >
          3. Кабінет клієнта та черга очікування ({bookingsList.length})
        </button>
        <button
          type="button"
          className={`nav-btn ${activeTab === "manager" ? "active" : ""}`}
          onClick={() => setActiveTab("manager")}
        >
          4. Робоча панель менеджера (Видача / Повернення / ТО)
        </button>
      </nav>

      {actionAlert && (
        <div
          className={`global-banner banner-${actionAlert.type}`}
          role="status"
          aria-live="polite"
        >
          <span>{actionAlert.text}</span>
          <button type="button" className="banner-close" onClick={() => setActionAlert(null)}>✕</button>
        </div>
      )}

      <main className="main-content" role="main">
        {/* ==================== ЕКРАН 1: КАТАЛОГ ОБЛАДНАННЯ ==================== */}
        {activeTab === "catalog" && (
          <section aria-labelledby="catalog-heading" className="view-section">
            <div className="section-header-row">
              <div>
                <h2 id="catalog-heading" className="section-title">
                  Каталог обладнання та інвентарний облік фізичних екземплярів
                </h2>
                <p className="section-desc">
                  Кожна товарна позиція має власний тариф, обов’язкову технічну перерву на обслуговування між орендами та набір окремих фізичних екземплярів з індивідуальним графіком доступності.
                </p>
              </div>
              <div className="summary-kpi-group">
                <div className="kpi-box">
                  <span className="kpi-val">{totalTypesCount}</span>
                  <span className="kpi-lbl">Типів у вибірці</span>
                </div>
                <div className="kpi-box">
                  <span className="kpi-val">{totalUnitsInCatalog}</span>
                  <span className="kpi-lbl">Фізичних екземплярів</span>
                </div>
                <div className="kpi-box kpi-highlight">
                  <span className="kpi-val">{availUnitsInCatalog}</span>
                  <span className="kpi-lbl">Вільних для замовлення</span>
                </div>
              </div>
            </div>

            {/* Панель пошуку та комбінованої фільтрації */}
            <form
              className="filter-bar"
              onSubmit={(e) => {
                e.preventDefault();
                loadCatalog();
              }}
              aria-label="Фільтри каталогу обладнання"
            >
              <div className="filter-field">
                <label htmlFor="f-search">Пошук за назвою, моделлю або інвентарним кодом:</label>
                <input
                  id="f-search"
                  type="text"
                  placeholder="Напр.: Honda, Sony, INV-GEN-001..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              <div className="filter-field">
                <label htmlFor="f-category">Категорія обладнання:</label>
                <select
                  id="f-category"
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                >
                  <option value="ALL">Усі категорії</option>
                  <option value="Енергообладнання">Енергообладнання</option>
                  <option value="Фото та відео">Фото та відео</option>
                  <option value="Будівельний інструмент">Будівельний інструмент</option>
                  <option value="Вимірювальні прилади">Вимірювальні прилади</option>
                </select>
              </div>

              <div className="filter-field">
                <label htmlFor="f-billing">Одиниця тарифікації:</label>
                <select
                  id="f-billing"
                  value={billingFilter}
                  onChange={(e) => setBillingFilter(e.target.value)}
                >
                  <option value="ALL">Усі тарифи ( доба + година )</option>
                  <option value="DAY">Подобовий тариф (DAY)</option>
                  <option value="HOUR">Погодинний тариф (HOUR)</option>
                </select>
              </div>

              <div className="filter-field period-toggle-field">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={usePeriodFilter}
                    onChange={(e) => setUsePeriodFilter(e.target.checked)}
                  />
                  <span>Перевірити наявність у часовому вікні:</span>
                </label>
                {usePeriodFilter && (
                  <div className="period-inputs">
                    <input
                      type="datetime-local"
                      aria-label="Початок періоду фільтрації"
                      value={filterFrom}
                      onChange={(e) => setFilterFrom(e.target.value)}
                    />
                    <span>—</span>
                    <input
                      type="datetime-local"
                      aria-label="Завершення періоду фільтрації"
                      value={filterTo}
                      onChange={(e) => setFilterTo(e.target.value)}
                    />
                  </div>
                )}
              </div>

              <div className="filter-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    setSearchQuery("");
                    setCategoryFilter("ALL");
                    setBillingFilter("ALL");
                    setUsePeriodFilter(false);
                  }}
                >
                  Скинути
                </button>
              </div>
            </form>

            {catalogError && (
              <div className="alert-box alert-error" role="alert">
                <strong>[{catalogError.code}] {catalogError.title}:</strong> {catalogError.detail}
              </div>
            )}

            {loadingCatalog ? (
              <div className="empty-state-box">Завантаження каталогу обладнання...</div>
            ) : catalog.length === 0 ? (
              <div className="empty-state-box" role="status">
                <h3>За вказаними критеріями обладнання не знайдено</h3>
                <p>Спробуйте змінити пошуковий запит або скинути фільтри категорії та періоду.</p>
              </div>
            ) : (
              <div className="catalog-grid">
                {catalog.map((eq) => {
                  let specs = {};
                  try {
                    specs = JSON.parse(eq.specsJson);
                  } catch {
                    specs = {};
                  }
                  return (
                    <article key={eq.id} className="equipment-card">
                      <div className="eq-card-top">
                        <span className="eq-category-tag">{eq.category}</span>
                        <span className="eq-buffer-tag" title="Обов'язкова технічна перерва між орендами">
                          Тех. перерва: +{eq.maintenanceBufferHours} год
                        </span>
                      </div>

                      <h3 className="eq-title">{eq.title}</h3>
                      <p className="eq-brand">{eq.brandModel}</p>
                      <p className="eq-desc">{eq.description}</p>

                      <div className="eq-specs-list">
                        {Object.entries(specs).map(([k, v]) => (
                          <span key={k} className="spec-chip">
                            <strong>{k}:</strong> {v}
                          </span>
                        ))}
                      </div>

                      <div className="eq-tariff-box">
                        <div>
                          <div className="tariff-rate">
                            {eq.tariff.rateFormatted} / {eq.tariff.billingUnit === "HOUR" ? "год" : "доба"}
                          </div>
                          <div className="tariff-sub">
                            Застава: {eq.tariff.depositFormatted} • Прострочення: {eq.tariff.lateFeeFormatted}/год
                          </div>
                        </div>
                        <div className="tariff-limits">
                          Мін/макс: {eq.tariff.minUnits}–{eq.tariff.maxUnits}{" "}
                          {eq.tariff.billingUnit === "HOUR" ? "год" : "діб"}
                        </div>
                      </div>

                      <div className="eq-units-section">
                        <div className="units-header">
                          <span>Фізичні екземпляри ({eq.units.length} шт.):</span>
                          <span className="units-avail-count">
                            Доступно: {eq.availableUnitsCount} з {eq.totalUnitsCount}
                          </span>
                        </div>
                        <ul className="units-mini-list">
                          {eq.units.map((u) => {
                            const b = unitConditionBadge(u.conditionStatus);
                            return (
                              <li key={u.id} className={`unit-mini-item ${b.cls}`}>
                                <span className="unit-code">{b.icon} {u.inventoryCode}</span>
                                <span className="unit-loc">{u.warehouseLocation}</span>
                                <span className="unit-state-lbl">
                                  {u.conditionStatus !== "AVAILABLE"
                                    ? b.label
                                    : u.isAvailableInSelectedPeriod
                                    ? "Вільний"
                                    : "Зайнятий у періоді"}
                                </span>
                              </li>
                            );
                          })}
                        </ul>
                      </div>

                      <div className="eq-card-footer">
                        <button
                          type="button"
                          className="btn-primary full-width"
                          onClick={() => handleSelectEquipmentCard(eq)}
                        >
                          Відкрити календар та забронювати
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        )}

        {/* ==================== ЕКРАН 2 & 3: КАЛЕНДАР ДОСТУПНОСТІ ТА ФОРМА БРОНЮВАННЯ ==================== */}
        {activeTab === "details" && selectedEquipment && (
          <section aria-labelledby="calendar-heading" className="view-section">
            <div className="details-header-bar">
              <div>
                <span className="eq-category-tag">{selectedEquipment.category}</span>
                <h2 id="calendar-heading" className="section-title">
                  {selectedEquipment.title} ({selectedEquipment.brandModel})
                </h2>
                <p className="section-desc">
                  Тариф: <strong>{selectedEquipment.tariff.rateFormatted} / {selectedEquipment.tariff.billingUnit === "HOUR" ? "год" : "доба"}</strong> •
                  Навчальна застава: <strong>{selectedEquipment.tariff.depositFormatted}</strong> •
                  Технічна перерва після повернення: <strong>+{selectedEquipment.maintenanceBufferHours} год</strong> •
                  Пеня за прострочення: <strong>{selectedEquipment.tariff.lateFeeFormatted}/год</strong>
                </p>
              </div>
              <div className="details-switch-eq">
                <label htmlFor="switch-eq-select">Швидкий перехід до іншої позиції:</label>
                <select
                  id="switch-eq-select"
                  value={selectedEquipment.id}
                  onChange={(e) => {
                    const found = catalog.find((c) => c.id === e.target.value);
                    if (found) handleSelectEquipmentCard(found);
                  }}
                >
                  {catalog.map((c) => (
                    <option key={c.id} value={c.id}>{c.title}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Візуальний календар доступності за фізичними екземплярами */}
            <div className="calendar-panel">
              <div className="calendar-panel-header">
                <h3>Поекземплярна шкала доступності та технічних перерв (листопад 2026 р.)</h3>
                <div className="calendar-legend" aria-label="Умовні позначення календаря">
                  <span className="leg-item leg-free">Вільно</span>
                  <span className="leg-item leg-issued">Видано</span>
                  <span className="leg-item leg-confirmed">Підтверджено</span>
                  <span className="leg-item leg-pending">Очікує</span>
                  <span className="leg-item leg-buffer">Буфер ТО</span>
                  <span className="leg-item leg-unavail">На ТО / Списано</span>
                </div>
              </div>

              <div className="table-responsive">
                <table className="availability-grid-table">
                  <thead>
                    <tr>
                      <th scope="col" className="unit-col-hdr">Фізичний екземпляр</th>
                      <th scope="col" className="state-col-hdr">Тех. стан і склад</th>
                      {CALENDAR_DAYS.map((dayStr) => (
                        <th key={dayStr} scope="col" className={dayStr === "2026-11-14" ? "today-col" : ""}>
                          {dayStr.slice(8, 10)}.{dayStr.slice(5, 7)}
                          {dayStr === "2026-11-14" && <div className="today-tag">Сьогодні</div>}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {selectedEquipment.units.map((unit) => {
                      const unitSlots = calendarSlots.filter((s) => s.unitId === unit.id);
                      const isSelectedRow = unit.id === selectedUnitId;

                      return (
                        <tr
                          key={unit.id}
                          className={isSelectedRow ? "selected-unit-row" : ""}
                          onClick={() => setSelectedUnitId(unit.id)}
                        >
                          <th scope="row" className="unit-cell-title">
                            <div className="unit-inv-code">
                              <input
                                type="radio"
                                name="selectedUnitRadio"
                                checked={isSelectedRow}
                                onChange={() => setSelectedUnitId(unit.id)}
                                aria-label={`Вибрати екземпляр ${unit.inventoryCode}`}
                              />
                              <strong>{unit.inventoryCode}</strong>
                            </div>
                            <div className="unit-sn">S/N: {unit.serialNumber}</div>
                          </th>
                          <td className="unit-cell-meta">
                            <span className={`unit-badge-sm ${unitConditionBadge(unit.conditionStatus).cls}`}>
                              {unitConditionBadge(unit.conditionStatus).icon} {unit.conditionStatus}
                            </span>
                            <div className="unit-note-sm">{unit.warehouseLocation} • {unit.notes}</div>
                          </td>
                          {CALENDAR_DAYS.map((dayStr) => {
                            if (unit.conditionStatus !== "AVAILABLE") {
                              return (
                                <td key={dayStr} className="cal-cell cal-unavail">
                                  <span className="cal-cell-lbl">
                                    {unit.conditionStatus === "IN_MAINTENANCE" ? "ТО" : "Спис."}
                                  </span>
                                </td>
                              );
                            }

                            const dayStart = new Date(`${dayStr}T00:00:00Z`).getTime();
                            const dayEnd = new Date(`${dayStr}T23:59:59Z`).getTime();

                            // Перевіряємо, чи припадає на цю добу активна оренда або її технічна перерва
                            const matchingSlot = unitSlots.find((s) => {
                              const sStart = new Date(s.startsAt).getTime();
                              const sBufEnd = new Date(s.bufferEndsAt).getTime();
                              return sStart <= dayEnd && sBufEnd > dayStart;
                            });

                            if (!matchingSlot) {
                              return (
                                <td key={dayStr} className="cal-cell cal-free" title={`${unit.inventoryCode}: Вільно ${dayStr}`}>
                                  <span className="cal-cell-lbl">Вільно</span>
                                </td>
                              );
                            }

                            const sEnd = new Date(matchingSlot.endsAt).getTime();
                            const isBufferOnly = dayStart >= sEnd;
                            if (isBufferOnly) {
                              return (
                                <td
                                  key={dayStr}
                                  className="cal-cell cal-buffer"
                                  title={`Технічна перерва після ${matchingSlot.bookingNumber} до ${formatDateTimeShort(matchingSlot.bufferEndsAt)}`}
                                >
                                  <span className="cal-cell-lbl">Буфер</span>
                                </td>
                              );
                            }

                            const cellCls =
                              matchingSlot.status === "ISSUED"
                                ? "cal-issued"
                                : matchingSlot.status === "CONFIRMED"
                                ? "cal-confirmed"
                                : "cal-pending";

                            const shortStatus =
                              matchingSlot.status === "ISSUED"
                                ? "Видано"
                                : matchingSlot.status === "CONFIRMED"
                                ? "Підтв."
                                : "Очікує";

                            return (
                              <td
                                key={dayStr}
                                className={`cal-cell ${cellCls}`}
                                title={`${matchingSlot.bookingNumber} (${matchingSlot.status}): ${formatDateTimeShort(matchingSlot.startsAt)} — ${formatDateTimeShort(matchingSlot.endsAt)} (+${matchingSlot.maintenanceBufferHours} год тех. перерва до ${formatDateTimeShort(matchingSlot.bufferEndsAt)})`}
                              >
                                <div className="cal-cell-lbl">{shortStatus}</div>
                                <div className="cal-cell-sub">{matchingSlot.bookingNumber.slice(-4)}</div>
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Детальний список активних слотів у календарі */}
              <div className="active-slots-list">
                <h4>Активні інтервали та технічні перерви екземплярів цієї позиції:</h4>
                {calendarSlots.length === 0 ? (
                  <p className="muted-text">Немає активних бронювань у вибраному діапазоні.</p>
                ) : (
                  <div className="slots-chips-wrap">
                    {calendarSlots.map((s) => (
                      <div key={s.bookingId} className="slot-detail-chip">
                        <strong>{s.inventoryCode}</strong> • <span>{s.bookingNumber}</span> •{" "}
                        <span className={`badge-inline ${statusBadgeInfo(s.status).cls}`}>
                          {statusBadgeInfo(s.status).symbol} {s.status}
                        </span>{" "}
                        • Оренда: <strong>{formatDateTimeShort(s.startsAt)} — {formatDateTimeShort(s.endsAt)}</strong>{" "}
                        • Тех. перерва до: <strong>{formatDateTimeShort(s.bufferEndsAt)}</strong>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Двоколонковий блок: Форма оформлення заявки + Попередній розрахунок вартості */}
            <div className="booking-workspace-grid">
              <form className="booking-form-card" onSubmit={handleCreateBooking} noValidate>
                <h3>Оформлення заявки на оренду фізичного екземпляра</h3>

                <div className="form-group">
                  <label htmlFor="bf-unit">1. Оберіть конкретний фізичний екземпляр (інвентарний код):</label>
                  <select
                    id="bf-unit"
                    value={selectedUnitId}
                    onChange={(e) => setSelectedUnitId(e.target.value)}
                  >
                    {selectedEquipment.units.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.inventoryCode} (S/N: {u.serialNumber}) — [{u.conditionStatus}] — {u.warehouseLocation}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-row-2col">
                  <div className="form-group">
                    <label htmlFor="bf-start">2. Дата і час початку оренди (включно):</label>
                    <input
                      id="bf-start"
                      type="datetime-local"
                      value={bookingStart}
                      onChange={(e) => setBookingStart(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="bf-end">3. Дата і час завершення оренди:</label>
                    <input
                      id="bf-end"
                      type="datetime-local"
                      value={bookingEnd}
                      onChange={(e) => setBookingEnd(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="bf-purpose">4. Цільове призначення / об’єкт використання (5–300 символів):</label>
                  <textarea
                    id="bf-purpose"
                    rows={3}
                    value={bookingPurpose}
                    onChange={(e) => setBookingPurpose(e.target.value)}
                    placeholder="Вкажіть мету використання обладнання та місце проведення робіт..."
                    required
                  />
                </div>

                <div className="quick-scenarios-bar">
                  <span>Швидкі пресети:</span>
                  <button
                    type="button"
                    className="btn-chip"
                    onClick={() => {
                      const availU = selectedEquipment.units.find((u) => u.conditionStatus === "AVAILABLE");
                      if (availU) setSelectedUnitId(availU.id);
                      setBookingStart("2026-11-20T09:00");
                      setBookingEnd("2026-11-22T09:00");
                      setBookingAlert(null);
                    }}
                  >
                    Вільний інтервал (20.11–22.11)
                  </button>
                  <button
                    type="button"
                    className="btn-chip"
                    onClick={() => {
                      setSelectedUnitId("unit-gen-01");
                      setBookingStart("2026-11-16T10:30");
                      setBookingEnd("2026-11-17T08:00");
                      setBookingAlert(null);
                    }}
                  >
                    Накладання на тех. перерву (16.11 10:30)
                  </button>
                  <button
                    type="button"
                    className="btn-chip"
                    onClick={() => {
                      setBookingStart("2026-11-19T16:00");
                      setBookingEnd("2026-11-18T10:00");
                      setBookingAlert(null);
                    }}
                  >
                    Кінець раніше початку
                  </button>
                </div>

                {bookingAlert && (
                  <div
                    className={`alert-box ${bookingAlert.type === "success" ? "alert-success" : "alert-error"}`}
                    role="alert"
                  >
                    <div className="alert-title">
                      [{bookingAlert.code}] {bookingAlert.title}
                    </div>
                    <div>{bookingAlert.detail}</div>
                  </div>
                )}

                <div className="form-submit-row">
                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={bookingSubmitting || !currentUser}
                  >
                    {bookingSubmitting
                      ? "Перевірка та збереження..."
                      : currentUser
                      ? "Підтвердити та надіслати заявку на бронювання"
                      : "Увійдіть у систему для створення заявки"}
                  </button>
                </div>
              </form>

              {/* Картка серверного розрахунку вартості та черги очікування */}
              <aside className="calculator-card" aria-label="Розрахунок вартості та перевірка доступності">
                <h3>Серверний розрахунок вартості та перевірка інтервалу</h3>
                {previewData ? (
                  <div className="calc-body">
                    <div className={`availability-status-banner ${previewData.isAvailable ? "avail-ok" : "avail-err"}`}>
                      {previewData.isAvailable ? (
                        <>
                          <strong>ЕКЗЕМПЛЯР {previewData.inventoryCode} ДОСТУПНИЙ</strong>
                          <div>Конфліктів у календарі та технічних перервах не виявлено.</div>
                        </>
                      ) : (
                        <>
                          <strong>НЕДОСТУПНО ({previewData.errorCode})</strong>
                          <div>{previewData.errorMessage}</div>
                        </>
                      )}
                    </div>

                    <dl className="calc-dl">
                      <div className="calc-row">
                        <dt>Фізичний екземпляр:</dt>
                        <dd><strong>{previewData.inventoryCode || selectedUnitId}</strong></dd>
                      </div>
                      <div className="calc-row">
                        <dt>Період оренди клієнта:</dt>
                        <dd>{formatDateTimeShort(previewData.startsAt)} — {formatDateTimeShort(previewData.endsAt)}</dd>
                      </div>
                      <div className="calc-row">
                        <dt>Завершення тех. перерви (+{previewData.maintenanceBufferHours} год):</dt>
                        <dd><strong>{formatDateTimeShort(previewData.bufferEndsAt)}</strong></dd>
                      </div>
                      <div className="calc-row">
                        <dt>Оплачуваних одиниць (округлення ⌈Δt/U⌉):</dt>
                        <dd>
                          <strong>{previewData.billedUnits}</strong>{" "}
                          {previewData.billingUnit === "HOUR" ? "год." : "діб"} × {previewData.unitRateFormatted}
                        </dd>
                      </div>
                      <div className="calc-row">
                        <dt>Базова вартість оренди:</dt>
                        <dd><strong>{previewData.basePriceFormatted}</strong></dd>
                      </div>
                      <div className="calc-row">
                        <dt>Навчальна поворотна застава:</dt>
                        <dd>{previewData.depositFormatted}</dd>
                      </div>
                      <div className="calc-row calc-total-row">
                        <dt>Підсумкова вартість оренди:</dt>
                        <dd>{previewData.totalPriceFormatted}</dd>
                      </div>
                    </dl>

                    {/* Черга очікування при конфлікті інтервалів */}
                    {!previewData.isAvailable && previewData.errorCode === "INTERVAL_CONFLICT" && (
                      <div className="waitlist-offer-box">
                        <h4>Запис у чергу очікування (Waitlist)</h4>
                        <p>
                          Обраний екземпляр зайнятий (заявка <strong>{previewData.conflictingBookingNumber}</strong>).
                          Ви можете стати в чергу очікування: у разі скасування або відхилення бронювання система автоматично переведе ваш запит у стан <code>NOTIFIED</code>.
                        </p>
                        <div className="form-group">
                          <label htmlFor="wl-note">Контактна примітка для менеджера:</label>
                          <input
                            id="wl-note"
                            type="text"
                            value={waitlistNote}
                            onChange={(e) => setWaitlistNote(e.target.value)}
                          />
                        </div>
                        <button
                          type="button"
                          className="btn-warning full-width"
                          onClick={handleJoinWaitlist}
                          disabled={!currentUser}
                        >
                          Стати в чергу очікування на цей інтервал
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="muted-text">Оберіть часовий інтервал для розрахунку вартості.</p>
                )}
              </aside>
            </div>
          </section>
        )}

        {/* ==================== ЕКРАН 4: ОСОБИСТИЙ КАБІНЕТ КЛІЄНТА ==================== */}
        {activeTab === "mybookings" && (
          <section aria-labelledby="mybookings-heading" className="view-section">
            <h2 id="mybookings-heading" className="section-title">
              Особистий кабінет користувача: Мої бронювання та черга очікування
            </h2>
            {!currentUser ? (
              <div className="empty-state-box" role="alert">
                <h3>Доступ лише для автентифікованих користувачів (401 Unauthorized)</h3>
                <p>Оберіть обліковий запис клієнта або менеджера у верхній панелі для перегляду заявок.</p>
              </div>
            ) : (
              <>
                <div className="table-responsive">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th scope="col">Номер заявки</th>
                        <th scope="col">Обладнання та екземпляр</th>
                        <th scope="col">Період оренди (+буфер ТО)</th>
                        <th scope="col">Вартість / Пеня</th>
                        <th scope="col">Статус</th>
                        <th scope="col">Дії</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bookingsList.map((b) => {
                        const st = statusBadgeInfo(b.status);
                        return (
                          <tr key={b.id}>
                            <td>
                              <strong>{b.bookingNumber}</strong>
                              <div className="sub-cell">v{b.version} • {b.clientName}</div>
                            </td>
                            <td>
                              <strong>{b.equipmentTitle}</strong>
                              <div className="sub-cell">Екземпляр: <code>{b.inventoryCode}</code></div>
                            </td>
                            <td>
                              <div>{formatDateTimeShort(b.startsAt)} — {formatDateTimeShort(b.endsAt)}</div>
                              <div className="sub-cell">Буфер до: {formatDateTimeShort(b.bufferEndsAt)}</div>
                            </td>
                            <td>
                              <div><strong>{b.totalPriceFormatted}</strong> ({b.billedUnits} од.)</div>
                              {b.lateHours > 0 && (
                                <div className="late-fee-tag">
                                  Прострочення {b.lateHours} год (+{b.lateFeeFormatted})
                                </div>
                              )}
                            </td>
                            <td>
                              <span className={`status-badge ${st.cls}`}>
                                {st.symbol} {st.label}
                              </span>
                              {b.rejectionReason && (
                                <div className="rej-reason-text">Причина: {b.rejectionReason}</div>
                              )}
                            </td>
                            <td className="actions-cell">
                              <button
                                type="button"
                                className="btn-sm btn-secondary"
                                onClick={() => handleInspectBooking(b.id)}
                              >
                                Історія / Деталі
                              </button>
                              {(b.status === "PENDING" || b.status === "CONFIRMED") && (
                                <button
                                  type="button"
                                  className="btn-sm btn-danger"
                                  onClick={() =>
                                    handleBookingTransition(b.id, "cancel", {
                                      notes: "Скасовано клієнтом з особистого кабінету"
                                    })
                                  }
                                >
                                  Скасувати
                                </button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Таблиця черги очікування (Waitlist) */}
                <div className="waitlist-section-block">
                  <h3>Черга очікування (Waitlist) на зайняті інтервали ({waitlistEntries.length})</h3>
                  {waitlistEntries.length === 0 ? (
                    <p className="muted-text">Записів у черзі очікування немає.</p>
                  ) : (
                    <div className="table-responsive">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th scope="col">ID запису</th>
                            <th scope="col">Тип обладнання / Бажаний екземпляр</th>
                            <th scope="col">Клієнт</th>
                            <th scope="col">Бажаний інтервал</th>
                            <th scope="col">Статус черги</th>
                            <th scope="col">Примітка</th>
                          </tr>
                        </thead>
                        <tbody>
                          {waitlistEntries.map((w) => (
                            <tr key={w.id}>
                              <td><code>{w.id}</code></td>
                              <td>
                                <strong>{w.equipmentTitle}</strong>
                                <div className="sub-cell">
                                  Екземпляр: {w.preferredInventoryCode || "Будь-який вільний"}
                                </div>
                              </td>
                              <td>{w.clientName}</td>
                              <td>
                                {formatDateTimeShort(w.desiredStartsAt)} — {formatDateTimeShort(w.desiredEndsAt)}
                              </td>
                              <td>
                                <span className={`status-badge ${w.status === "NOTIFIED" ? "badge-confirmed" : "badge-pending"}`}>
                                  {w.status === "NOTIFIED" ? "СПОВІЩЕНО (СЛОТ ВІЛЬНИЙ)" : w.status}
                                </span>
                              </td>
                              <td>{w.contactNote}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </>
            )}
          </section>
        )}

        {/* ==================== ЕКРАН 5: РОБОЧА ПАНЕЛЬ МЕНЕДЖЕРА ==================== */}
        {activeTab === "manager" && (
          <section aria-labelledby="manager-heading" className="view-section">
            <div className="section-header-row">
              <div>
                <h2 id="manager-heading" className="section-title">
                  Робоче місце менеджера: Погодження заявок, видача, повернення та облік прострочень
                </h2>
                <p className="section-desc">
                  Погодження або мотивоване відхилення заявок, фіксація фізичної видачі екземпляра (ISSUED) і приймання повернення (RETURNED) з автоматичним нарахуванням пені за запізнення.
                </p>
              </div>
              <div className="filter-field">
                <label htmlFor="mgr-status-filter">Фільтр за статусом заявок:</label>
                <select
                  id="mgr-status-filter"
                  value={statusFilterMgr}
                  onChange={(e) => setStatusFilterMgr(e.target.value)}
                >
                  <option value="ALL">Усі статуси ({bookingsList.length})</option>
                  <option value="PENDING">PENDING — Очікують погодження</option>
                  <option value="CONFIRMED">CONFIRMED — Підтверджені до видачі</option>
                  <option value="ISSUED">ISSUED — Фізично видані клієнтам</option>
                  <option value="RETURNED">RETURNED — Завершені / Повернуті</option>
                  <option value="REJECTED">REJECTED — Відхилені</option>
                  <option value="CANCELLED">CANCELLED — Скасовані</option>
                </select>
              </div>
            </div>

            {!currentUser || currentUser.role !== "MANAGER" ? (
              <div className="alert-box alert-error" role="alert">
                <div className="alert-title">[HTTP 403 / FORBIDDEN_ROLE] Доступ до адміністративних операцій обмежено</div>
                <p>
                  Поточна роль: <strong>{currentUser ? currentUser.role : "GUEST"}</strong>. Для виконання операцій погодження, видачі та повернення перемкніть обліковий запис у верхній панелі на <strong>Мельник Ірина Сергіївна (Менеджер)</strong>.
                </p>
              </div>
            ) : null}

            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th scope="col">Заявка / Клієнт</th>
                    <th scope="col">Фізичний екземпляр</th>
                    <th scope="col">Плановий інтервал (+буфер)</th>
                    <th scope="col">Фінансовий підсумок</th>
                    <th scope="col">Статус</th>
                    <th scope="col">Операції менеджера</th>
                  </tr>
                </thead>
                <tbody>
                  {bookingsList.map((b) => {
                    const st = statusBadgeInfo(b.status);
                    return (
                      <tr key={b.id}>
                        <td>
                          <strong>{b.bookingNumber}</strong>
                          <div className="sub-cell">{b.clientName}</div>
                          <div className="sub-cell">Мета: {b.purpose}</div>
                        </td>
                        <td>
                          <strong><code>{b.inventoryCode}</code></strong>
                          <div className="sub-cell">{b.equipmentTitle}</div>
                        </td>
                        <td>
                          <div>{formatDateTimeShort(b.startsAt)} — {formatDateTimeShort(b.endsAt)}</div>
                          <div className="sub-cell">Тех. перерва до: {formatDateTimeShort(b.bufferEndsAt)}</div>
                          {b.actualReturnedAt && (
                            <div className="sub-cell">Факт. повернення: {formatDateTimeShort(b.actualReturnedAt)}</div>
                          )}
                        </td>
                        <td>
                          <div>Разом: <strong>{b.totalPriceFormatted}</strong></div>
                          <div className="sub-cell">Застава: {b.depositFormatted}</div>
                          {b.lateHours > 0 && (
                            <div className="late-fee-tag">Пеня ({b.lateHours} год): +{b.lateFeeFormatted}</div>
                          )}
                        </td>
                        <td>
                          <span className={`status-badge ${st.cls}`}>
                            {st.symbol} {st.label}
                          </span>
                        </td>
                        <td className="actions-cell">
                          <button
                            type="button"
                            className="btn-sm btn-secondary"
                            onClick={() => handleInspectBooking(b.id)}
                          >
                            Керувати / Події
                          </button>
                          {b.status === "PENDING" && (
                            <button
                              type="button"
                              className="btn-sm btn-primary"
                              onClick={() =>
                                handleBookingTransition(b.id, "confirm", {
                                  notes: "Перевірено графік екземпляра, погоджено менеджером"
                                })
                              }
                            >
                              Погодити
                            </button>
                          )}
                          {b.status === "CONFIRMED" && (
                            <button
                              type="button"
                              className="btn-sm btn-primary"
                              onClick={() =>
                                handleBookingTransition(b.id, "issue", {
                                  notes: "Видано фізичний екземпляр клієнту за актом приймання-передачі",
                                  actualTimestamp: b.startsAt
                                })
                              }
                            >
                              Видати
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Модальне/бічне вікно детального керування бронюванням, продовження та історії подій */}
        {selectedBookingDetails && (
          <section className="booking-Inspector-drawer" aria-labelledby="inspector-title">
            <div className="inspector-header">
              <div>
                <h3 id="inspector-title">
                  Картка бронювання {selectedBookingDetails.bookingNumber} (екземпляр {selectedBookingDetails.inventoryCode})
                </h3>
                <p className="sub-cell">
                  Клієнт: {selectedBookingDetails.clientName} ({selectedBookingDetails.clientEmail}) •
                  Поточний стан: <strong>{selectedBookingDetails.status}</strong> • Версія запису: v{selectedBookingDetails.version}
                </p>
              </div>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setSelectedBookingDetails(null)}
              >
                Закрити картку ✕
              </button>
            </div>

            <div className="inspector-grid">
              <div className="inspector-actions-box">
                <h4>Керування життєвим циклом заявки та перевірка правил</h4>

                {/* Форма продовження оренди */}
                {(selectedBookingDetails.status === "PENDING" ||
                  selectedBookingDetails.status === "CONFIRMED" ||
                  selectedBookingDetails.status === "ISSUED") && (
                  <div className="action-subcard">
                    <h5>Продовження періоду оренди (Extension):</h5>
                    <div className="inline-control-row">
                      <input
                        type="datetime-local"
                        value={extendDateInput}
                        onChange={(e) => setExtendDateInput(e.target.value)}
                        aria-label="Нова дата завершення оренди"
                      />
                      <button
                        type="button"
                        className="btn-primary"
                        onClick={() =>
                          handleBookingTransition(selectedBookingDetails.id, "extend", {
                            newEndsAt: extendDateInput.endsWith("Z") ? extendDateInput : extendDateInput + ":00Z"
                          })
                        }
                      >
                        Продовжити оренду
                      </button>
                    </div>
                  </div>
                )}

                {/* Операції менеджера: Відхилення з обов'язковою причиною або Повернення із фіксацією часу */}
                <div className="action-subcard">
                  <h5>Коментар / Причина відхилення / Акт огляду при поверненні:</h5>
                  <input
                    type="text"
                    value={mgrNotesInput}
                    onChange={(e) => setMgrNotesInput(e.target.value)}
                    placeholder="Вкажіть причину відхилення або стан обладнання під час повернення..."
                  />

                  {selectedBookingDetails.status === "PENDING" && (
                    <div className="inline-control-row top-gap">
                      <button
                        type="button"
                        className="btn-primary"
                        onClick={() =>
                          handleBookingTransition(selectedBookingDetails.id, "confirm", {
                            notes: mgrNotesInput || "Погоджено менеджером"
                          })
                        }
                      >
                        Погодити заявку (CONFIRMED)
                      </button>
                      <button
                        type="button"
                        className="btn-danger"
                        onClick={() =>
                          handleBookingTransition(selectedBookingDetails.id, "reject", {
                            rejectionReason: mgrNotesInput
                          })
                        }
                      >
                        Відхилити заявку (REJECTED)
                      </button>
                    </div>
                  )}

                  {selectedBookingDetails.status === "ISSUED" && (
                    <div className="return-control-box top-gap">
                      <label htmlFor="actual-return-ts">
                        Фактичний час повернення (планове завершення: {formatDateTimeShort(selectedBookingDetails.endsAt)}):
                      </label>
                      <div className="inline-control-row">
                        <input
                          id="actual-return-ts"
                          type="datetime-local"
                          value={mgrReturnTimeInput}
                          onChange={(e) => setMgrReturnTimeInput(e.target.value)}
                        />
                        <button
                          type="button"
                          className="btn-primary"
                          onClick={() =>
                            handleBookingTransition(selectedBookingDetails.id, "return", {
                              notes: mgrNotesInput || "Обладнання перевірено та прийнято на склад",
                              actualTimestamp: mgrReturnTimeInput.endsWith("Z")
                                ? mgrReturnTimeInput
                                : mgrReturnTimeInput + ":00Z"
                            })
                          }
                        >
                          Зафіксувати повернення (RETURNED)
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Журнал подій (Audit Trail) */}
              <div className="inspector-events-box">
                <h4>Історія подій видачі, повернення та змін статусу (rental_events):</h4>
                <ul className="events-timeline">
                  {(selectedBookingDetails.events || []).map((ev) => (
                    <li key={ev.id} className="event-item">
                      <div className="event-top">
                        <strong>{ev.eventType}</strong> ({ev.oldStatus || "—"} → <strong>{ev.newStatus}</strong>)
                        <span className="event-time">{formatDateTimeShort(ev.occurredAt)}</span>
                      </div>
                      <div className="event-actor">Виконавець: {ev.actorName}</div>
                      <div className="event-note">{ev.notes}</div>
                      {ev.penaltyAddedMinor > 0 && (
                        <div className="late-fee-tag">Нараховано штраф: +{ev.penaltyAddedFormatted}</div>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
        )}
      </main>

      <footer className="app-footer" role="contentinfo">
        <div>
          Національний університет «Одеська політехніка» • Кафедра інформаційних систем • Одеса, 2026
        </div>
        <div>
          Варіант 12: Оренда обладнання з календарем доступності • Сливка Максим Олексійович, гр. АІ-243
        </div>
      </footer>
    </div>
  );
}
