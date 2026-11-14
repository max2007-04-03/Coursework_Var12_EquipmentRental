-- ============================================================================
-- Демонстраційний синтетичний набір даних (seed.sql)
-- Варіант 12: Оренда обладнання з календарем доступності
-- Паролі тестових облікових записів (PBKDF2-SHA256, для стенда):
--   manager@equiprent.op.edu.ua   -> ManagerRent#2026!Secure
--   kovalenko@student.op.edu.ua   -> ClientRent#2026!Kovalenko
--   bondarenko@student.op.edu.ua  -> ClientRent#2026!Bondarenko
--   shevchenko@student.op.edu.ua  -> ClientRent#2026!Shevchenko
-- ============================================================================

INSERT OR IGNORE INTO users (id, email, full_name, phone, role, password_hash, created_at) VALUES
('usr-mgr-01', 'manager@equiprent.op.edu.ua', 'Мельник Ірина Сергіївна (Менеджер)', '+380501112233', 'MANAGER', 'PBKDF2$100000$equiprent_salt_mgr$8f2d9c4b1e7a5f3c6d8e0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d', '2026-10-01T08:00:00Z'),
('usr-cli-01', 'kovalenko@student.op.edu.ua', 'Коваленко Олександр Ігорович', '+380672223344', 'CLIENT', 'PBKDF2$100000$equiprent_salt_c01$1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b', '2026-10-02T09:15:00Z'),
('usr-cli-02', 'bondarenko@student.op.edu.ua', 'Бондаренко Марія Василівна', '+380633334455', 'CLIENT', 'PBKDF2$100000$equiprent_salt_c02$2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c', '2026-10-03T11:30:00Z'),
('usr-cli-03', 'shevchenko@student.op.edu.ua', 'Шевченко Дмитро Олегович', '+380974445566', 'CLIENT', 'PBKDF2$100000$equiprent_salt_c03$3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d', '2026-10-05T14:20:00Z');

INSERT OR IGNORE INTO tariffs (id, code, name, billing_unit, rate_minor, deposit_minor, late_fee_per_hour_minor, min_units, max_units) VALUES
('trf-day-power', 'TRF-DAY-PWR', 'Добовий — Енергообладнання', 'DAY', 85000, 300000, 15000, 1, 30),
('trf-day-pro', 'TRF-DAY-PRO', 'Добовий — Професійна техніка', 'DAY', 120000, 500000, 25000, 1, 14),
('trf-hour-studio', 'TRF-HR-STD', 'Погодинний — Фото/Відео та студія', 'HOUR', 18000, 250000, 30000, 2, 72),
('trf-day-build', 'TRF-DAY-BLD', 'Добовий — Будівельний інструмент', 'DAY', 55000, 150000, 10000, 1, 21),
('trf-hour-meas', 'TRF-HR-MSR', 'Погодинний — Точні вимірювальні прилади', 'HOUR', 14000, 200000, 22000, 2, 48),
('trf-day-audio', 'TRF-DAY-AUD', 'Добовий — Концертний та презентаційний звук', 'DAY', 95000, 350000, 18000, 1, 10);

INSERT OR IGNORE INTO equipment_types (id, slug, title, category, brand_model, description, specs_json, tariff_id, maintenance_buffer_hours, active, image_tag) VALUES
('eqt-01', 'generator-honda-eu22i', 'Інверторний генератор Honda EU22i', 'Енергообладнання', 'Honda EU22i 2.2 кВт', 'Малошумний інверторний бензиновий генератор із чистою синусоїдою для резервного живлення серверного, лабораторного та знімального обладнання.', '{"power":"2.2 кВт","voltage":"230 В / 50 Гц","noise":"53 дБ","weight":"21.1 кг"}', 'trf-day-power', 4, 1, 'generator'),
('eqt-02', 'ecoflow-delta-pro', 'Зарядна станція EcoFlow DELTA Pro', 'Енергообладнання', 'EcoFlow DELTA Pro 3600 Вт·год', 'Портативна акумуляторна станція LiFePO4 великої ємності зі швидким заряджанням та виходами AC/DC/USB-C для виїзних заходів.', '{"capacity":"3600 Вт·год","output":"3600 Вт (X-Boost 4500 Вт)","battery":"LiFePO4","weight":"45 кг"}', 'trf-day-pro', 3, 1, 'powerstation'),
('eqt-03', 'sony-fx3-cinema', 'Кінокамера Sony FX3 Full-Frame', 'Фото та відео', 'Sony ILME-FX3 + 24-70mm f/2.8 GM', 'Повнокадрова професійна відеокамера лінійки Cinema Line із записом 4K 120p 10-bit 4:2:2, активним охолодженням та XLR-руків’ям.', '{"sensor":"Full-Frame CMOS","video":"4K 120fps 10-bit","mount":"Sony E + 24-70 GM","stabilization":"5-осьова IBIS"}', 'trf-hour-studio', 2, 1, 'camera'),
('eqt-04', 'aputure-600d-pro', 'Світлодіодний прожектор Aputure LS 600d Pro', 'Фото та відео', 'Aputure Light Storm 600d Pro', 'Потужне студійне та локаційне джерело постійного денного світла 5600K із захистом від пилу та вологи і керуванням Sidus Link.', '{"power":"600 Вт","colorTemp":"5600K CRI 96+","mount":"Bowens","control":"DMX / Bluetooth"}', 'trf-hour-studio', 2, 1, 'light'),
('eqt-05', 'bosch-gbh-8-45-dv', 'Перфоратор SDS-Max Bosch GBH 8-45 DV', 'Будівельний інструмент', 'Bosch Professional GBH 8-45 DV', 'Важкий мережевий перфоратор із системою гасіння вібрації Vibration Control та енергією удару 12.5 Дж для буріння бетону.', '{"impactEnergy":"12.5 Дж","power":"1500 Вт","chuck":"SDS-Max","weight":"8.9 кг"}', 'trf-day-build', 3, 1, 'drill'),
('eqt-06', 'makita-ls1018ln', 'Торцювальна пила Makita LS1018LN з протяжкою', 'Будівельний інструмент', 'Makita LS1018LN 260 мм', 'Настільна торцювальна пила з лазерним покажчиком лінії різу, плавним пуском і двонаправленим нахилом голови.', '{"blade":"260 мм","power":"1430 Вт","cutWidth":"310 мм","laser":"Вбудований"}', 'trf-day-build', 2, 1, 'saw'),
('eqt-07', 'flir-e8-xt-thermal', 'Тепловізор інфрачервоний FLIR E8-XT', 'Вимірювальні прилади', 'Teledyne FLIR E8-XT MSX', 'Професійний тепловізор для енергоаудиту будівель, перевірки електрощитів і діагностики нагріву механічних вузлів.', '{"irResolution":"320x240 (76800 пікс.)","tempRange":"-20°C ... +550°C","enhancement":"MSX","wifi":"Так"}', 'trf-hour-meas', 2, 1, 'thermal'),
('eqt-08', 'leica-disto-s910', 'Лазерний далекомір-тахеометр Leica DISTO S910', 'Вимірювальні прилади', 'Leica Geosystems DISTO S910 Set', 'Високоточний лазерний далекомір із технологією P2P (відстань між будь-якими двома точками у просторі) та експортом у DXF/CAD.', '{"range":"0.05 – 300 м","accuracy":"±1.0 мм","output":"DXF / WLAN","tripod":"FTA360-S у комплекті"}', 'trf-day-audio', 2, 1, 'laser');

INSERT OR IGNORE INTO equipment_units (id, equipment_type_id, inventory_code, serial_number, condition_status, warehouse_location, notes) VALUES
('unit-gen-01', 'eqt-01', 'INV-GEN-001', 'SN-HND-229011', 'AVAILABLE', 'Склад А, бокс 1', 'Після повного ТО, мастило замінено'),
('unit-gen-02', 'eqt-01', 'INV-GEN-002', 'SN-HND-229012', 'AVAILABLE', 'Склад А, бокс 2', 'Додатковий кабель 25 м у комплекті'),
('unit-gen-03', 'eqt-01', 'INV-GEN-003', 'SN-HND-229015', 'IN_MAINTENANCE', 'Сервісна зона', 'Планове чищення паливної системи'),
('unit-eco-01', 'eqt-02', 'INV-ECO-001', 'SN-ECF-881201', 'AVAILABLE', 'Склад А, стелаж 4', '100% ємності батареї, 42 цикли'),
('unit-eco-02', 'eqt-02', 'INV-ECO-002', 'SN-ECF-881209', 'AVAILABLE', 'Склад А, стелаж 4', 'З кабелем MC4 для сонячних панелей'),
('unit-cam-01', 'eqt-03', 'INV-CAM-001', 'SN-SNY-550311', 'AVAILABLE', 'Сейф-бокс Б1', 'Картка CFexpress Type A 160GB у комплекті'),
('unit-cam-02', 'eqt-03', 'INV-CAM-002', 'SN-SNY-550312', 'AVAILABLE', 'Сейф-бокс Б1', 'Два акумулятори NP-FZ100'),
('unit-cam-03', 'eqt-03', 'INV-CAM-003', 'SN-SNY-550319', 'RETIRED', 'Архів списання', 'Виведено з експлуатації (заміна байонета)'),
('unit-lgt-01', 'eqt-04', 'INV-LGT-001', 'SN-APT-600401', 'AVAILABLE', 'Склад Б, секція 2', 'Софтбокс Light Dome II у кофрі'),
('unit-lgt-02', 'eqt-04', 'INV-LGT-002', 'SN-APT-600402', 'AVAILABLE', 'Склад Б, секція 2', 'Стандартний рефлектор 55°'),
('unit-drl-01', 'eqt-05', 'INV-DRL-001', 'SN-BSH-774101', 'AVAILABLE', 'Склад В, стелаж 1', 'Набір бурів 16/22/32 мм'),
('unit-drl-02', 'eqt-05', 'INV-DRL-002', 'SN-BSH-774102', 'AVAILABLE', 'Склад В, стелаж 1', 'Кейс + піка SDS-Max'),
('unit-saw-01', 'eqt-06', 'INV-SAW-001', 'SN-MKT-331901', 'AVAILABLE', 'Склад В, стелаж 3', 'Диск по дереву та алюмінію 80T'),
('unit-saw-02', 'eqt-06', 'INV-SAW-002', 'SN-MKT-331904', 'AVAILABLE', 'Склад В, стелаж 3', 'Новий диск Makita Efficut'),
('unit-flr-01', 'eqt-07', 'INV-FLR-001', 'SN-FLR-910201', 'AVAILABLE', 'Сейф-бокс Б2', 'Сертифікат калібрування до 2027 р.'),
('unit-flr-02', 'eqt-07', 'INV-FLR-002', 'SN-FLR-910205', 'AVAILABLE', 'Сейф-бокс Б2', 'Запасний акумулятор у кейсі'),
('unit-lca-01', 'eqt-08', 'INV-LCA-001', 'SN-LCA-440110', 'AVAILABLE', 'Сейф-бокс Б3', 'Повний геодезичний комплект зі штативом'),
('unit-lca-02', 'eqt-08', 'INV-LCA-002', 'SN-LCA-440112', 'AVAILABLE', 'Сейф-бокс Б3', 'Перевірено юстування візира');

-- Демонстраційні бронювання на листопад 2026 р. (поточна дата стенда: 2026-11-14)
INSERT OR IGNORE INTO bookings (
    id, booking_number, unit_id, client_user_id, tariff_id,
    starts_at, ends_at, buffer_ends_at, status, purpose, rejection_reason,
    billed_units, unit_rate_minor, base_price_minor, deposit_minor,
    late_hours, late_fee_minor, total_price_minor,
    actual_issued_at, actual_returned_at, created_at, updated_at, version
) VALUES
-- 1. Активна видана оренда генератора INV-GEN-001 (13.11 – 16.11, +4 год тех. перерви)
('bkg-1001', 'RN-2026-1001', 'unit-gen-01', 'usr-cli-01', 'trf-day-power',
 '2026-11-13T09:00:00Z', '2026-11-16T09:00:00Z', '2026-11-16T13:00:00Z', 'ISSUED',
 'Резервне живлення виїзної студентської лабораторії робототехніки', NULL,
 3, 85000, 255000, 300000, 0, 0, 255000,
 '2026-11-13T09:05:00Z', NULL, '2026-11-10T10:15:00Z', '2026-11-13T09:05:00Z', 3),

-- 2. Підтверджене майбутнє бронювання того ж генератора INV-GEN-001 (17.11 – 19.11)
('bkg-1002', 'RN-2026-1002', 'unit-gen-01', 'usr-cli-02', 'trf-day-power',
 '2026-11-17T10:00:00Z', '2026-11-19T10:00:00Z', '2026-11-19T14:00:00Z', 'CONFIRMED',
 'Живлення звукового стенда на відкритому ярмарку інженерних проєктів', NULL,
 2, 85000, 170000, 300000, 0, 0, 170000,
 NULL, NULL, '2026-11-11T14:20:00Z', '2026-11-11T16:00:00Z', 2),

-- 3. Очікує погодження менеджером (другий екземпляр генератора INV-GEN-002 на 15.11 – 17.11)
('bkg-1003', 'RN-2026-1003', 'unit-gen-02', 'usr-cli-03', 'trf-day-power',
 '2026-11-15T08:00:00Z', '2026-11-17T08:00:00Z', '2026-11-17T12:00:00Z', 'PENDING',
 'Автономне живлення польових випробувань БПЛА', NULL,
 2, 85000, 170000, 300000, 0, 0, 170000,
 NULL, NULL, '2026-11-14T07:30:00Z', '2026-11-14T07:30:00Z', 1),

-- 4. Підтверджене бронювання EcoFlow INV-ECO-001 (14.11 – 16.11, +3 год тех. перерви)
('bkg-1004', 'RN-2026-1004', 'unit-eco-01', 'usr-cli-01', 'trf-day-pro',
 '2026-11-14T12:00:00Z', '2026-11-16T12:00:00Z', '2026-11-16T15:00:00Z', 'CONFIRMED',
 'Безперебійне живлення телекомунікаційного вузла хакатону', NULL,
 2, 120000, 240000, 500000, 0, 0, 240000,
 NULL, NULL, '2026-11-12T11:00:00Z', '2026-11-12T13:10:00Z', 2),

-- 5. Очікує погодження — камера Sony FX3 INV-CAM-001 (15.11 з 10:00 до 18:00, 8 год + 2 год тех. перерви)
('bkg-1005', 'RN-2026-1005', 'unit-cam-01', 'usr-cli-02', 'trf-hour-studio',
 '2026-11-15T10:00:00Z', '2026-11-15T18:00:00Z', '2026-11-15T20:00:00Z', 'PENDING',
 'Зйомка презентаційного відеоролика кафедри інформаційних систем', NULL,
 8, 18000, 144000, 250000, 0, 0, 144000,
 NULL, NULL, '2026-11-14T08:10:00Z', '2026-11-14T08:10:00Z', 1),

-- 6. Завершене вчасно бронювання (RETURNED без запізнення) — тепловізор INV-FLR-001
('bkg-1006', 'RN-2026-1006', 'unit-flr-01', 'usr-cli-01', 'trf-hour-meas',
 '2026-11-08T10:00:00Z', '2026-11-08T16:00:00Z', '2026-11-08T18:00:00Z', 'RETURNED',
 'Тепловізійне обстеження серверної кімнати корпусу ІКС', NULL,
 6, 14000, 84000, 200000, 0, 0, 84000,
 '2026-11-08T09:55:00Z', '2026-11-08T15:50:00Z', '2026-11-06T12:00:00Z', '2026-11-08T15:50:00Z', 4),

-- 7. Завершене із запізненням на 3 години (RETURNED + пеня 3 * 100.00 грн = 300.00 грн) — перфоратор INV-DRL-001
('bkg-1007', 'RN-2026-1007', 'unit-drl-01', 'usr-cli-03', 'trf-day-build',
 '2026-11-05T09:00:00Z', '2026-11-07T09:00:00Z', '2026-11-07T12:00:00Z', 'RETURNED',
 'Монтаж кабельних трас у лабораторному корпусі', NULL,
 2, 55000, 110000, 150000, 3, 30000, 140000,
 '2026-11-05T09:02:00Z', '2026-11-07T11:45:00Z', '2026-11-03T15:00:00Z', '2026-11-07T11:45:00Z', 4),

-- 8. Відхилена менеджером заявка (REJECTED із фіксацією причини)
('bkg-1008', 'RN-2026-1008', 'unit-lca-01', 'usr-cli-02', 'trf-day-audio',
 '2026-11-11T09:00:00Z', '2026-11-12T09:00:00Z', '2026-11-12T11:00:00Z', 'REJECTED',
 'Геодезичні обміри відкритого майданчика під час зливи',
 'Відхилено за регламентом експлуатації: використання далекоміра Leica S910 на відкритому майданчику під час опадів заборонено.',
 1, 95000, 95000, 350000, 0, 0, 95000,
 NULL, NULL, '2026-11-09T16:40:00Z', '2026-11-10T09:10:00Z', 2),

-- 9. Скасована клієнтом заявка (CANCELLED — не блокує календар)
('bkg-1009', 'RN-2026-1009', 'unit-lgt-01', 'usr-cli-01', 'trf-hour-studio',
 '2026-11-16T10:00:00Z', '2026-11-16T16:00:00Z', '2026-11-16T18:00:00Z', 'CANCELLED',
 'Студійна предметна фотозйомка прототипів', NULL,
 6, 18000, 108000, 250000, 0, 0, 108000,
 NULL, NULL, '2026-11-12T18:00:00Z', '2026-11-13T10:30:00Z', 2),

-- 10. Активна видана оренда прожектора INV-LGT-002 (14.11 з 08:00 до 14.11 16:00)
('bkg-1010', 'RN-2026-1010', 'unit-lgt-02', 'usr-cli-03', 'trf-hour-studio',
 '2026-11-14T08:00:00Z', '2026-11-14T16:00:00Z', '2026-11-14T18:00:00Z', 'ISSUED',
 'Освітлення сцени студентської конференції', NULL,
 8, 18000, 144000, 250000, 0, 0, 144000,
 '2026-11-14T08:02:00Z', NULL, '2026-11-12T09:00:00Z', '2026-11-14T08:02:00Z', 3);

-- Історія подій видачі, повернення та зміни станів
INSERT OR IGNORE INTO rental_events (id, booking_id, actor_user_id, event_type, old_status, new_status, occurred_at, notes, penalty_added_minor) VALUES
('evt-01', 'bkg-1001', 'usr-cli-01', 'CREATED', NULL, 'PENDING', '2026-11-10T10:15:00Z', 'Заявку створено клієнтом через вебкаталог', 0),
('evt-02', 'bkg-1001', 'usr-mgr-01', 'CONFIRMED', 'PENDING', 'CONFIRMED', '2026-11-10T11:30:00Z', 'Перевірено графік ТО екземпляра INV-GEN-001, заявку погоджено', 0),
('evt-03', 'bkg-1001', 'usr-mgr-01', 'ISSUED', 'CONFIRMED', 'ISSUED', '2026-11-13T09:05:00Z', 'Видано фізичний екземпляр INV-GEN-001, бак заправлений, пломби цілі', 0),
('evt-04', 'bkg-1002', 'usr-cli-02', 'CREATED', NULL, 'PENDING', '2026-11-11T14:20:00Z', 'Заявку створено клієнтом', 0),
('evt-05', 'bkg-1002', 'usr-mgr-01', 'CONFIRMED', 'PENDING', 'CONFIRMED', '2026-11-11T16:00:00Z', 'Погоджено після завершення попередньої оренди та 4 год тех. перерви', 0),
('evt-06', 'bkg-1003', 'usr-cli-03', 'CREATED', NULL, 'PENDING', '2026-11-14T07:30:00Z', 'Очікує перевірки менеджером', 0),
('evt-07', 'bkg-1004', 'usr-cli-01', 'CREATED', NULL, 'PENDING', '2026-11-12T11:00:00Z', 'Заявка на зарядну станцію EcoFlow', 0),
('evt-08', 'bkg-1004', 'usr-mgr-01', 'CONFIRMED', 'PENDING', 'CONFIRMED', '2026-11-12T13:10:00Z', 'Погоджено менеджером', 0),
('evt-09', 'bkg-1005', 'usr-cli-02', 'CREATED', NULL, 'PENDING', '2026-11-14T08:10:00Z', 'Заявка на камеру Sony FX3 (8 годин)', 0),
('evt-10', 'bkg-1006', 'usr-cli-01', 'CREATED', NULL, 'PENDING', '2026-11-06T12:00:00Z', 'Заявка на тепловізор FLIR E8-XT', 0),
('evt-11', 'bkg-1006', 'usr-mgr-01', 'CONFIRMED', 'PENDING', 'CONFIRMED', '2026-11-06T14:00:00Z', 'Погоджено', 0),
('evt-12', 'bkg-1006', 'usr-mgr-01', 'ISSUED', 'CONFIRMED', 'ISSUED', '2026-11-08T09:55:00Z', 'Видано у справному стані з кейсом', 0),
('evt-13', 'bkg-1006', 'usr-mgr-01', 'RETURNED_ON_TIME', 'ISSUED', 'RETURNED', '2026-11-08T15:50:00Z', 'Повернуто вчасно, зауважень до стану лінзи немає', 0),
('evt-14', 'bkg-1007', 'usr-cli-03', 'CREATED', NULL, 'PENDING', '2026-11-03T15:00:00Z', 'Заявка на перфоратор Bosch', 0),
('evt-15', 'bkg-1007', 'usr-mgr-01', 'CONFIRMED', 'PENDING', 'CONFIRMED', '2026-11-03T16:10:00Z', 'Погоджено', 0),
('evt-16', 'bkg-1007', 'usr-mgr-01', 'ISSUED', 'CONFIRMED', 'ISSUED', '2026-11-05T09:02:00Z', 'Видано клієнту під підпис', 0),
('evt-17', 'bkg-1007', 'usr-mgr-01', 'RETURNED_LATE', 'ISSUED', 'RETURNED', '2026-11-07T11:45:00Z', 'Повернуто із запізненням 2 год 45 хв (округлено до 3 год). Нараховано пеню 300,00 грн.', 30000),
('evt-18', 'bkg-1008', 'usr-cli-02', 'CREATED', NULL, 'PENDING', '2026-11-09T16:40:00Z', 'Заявка на далекомір Leica', 0),
('evt-19', 'bkg-1008', 'usr-mgr-01', 'REJECTED', 'PENDING', 'REJECTED', '2026-11-10T09:10:00Z', 'Відхилено через погодні умови та регламент безпеки', 0),
('evt-20', 'bkg-1009', 'usr-cli-01', 'CREATED', NULL, 'PENDING', '2026-11-12T18:00:00Z', 'Заявка на прожектор Aputure', 0),
('evt-21', 'bkg-1009', 'usr-cli-01', 'CANCELLED', 'PENDING', 'CANCELLED', '2026-11-13T10:30:00Z', 'Скасовано клієнтом через перенесення зйомки', 0),
('evt-22', 'bkg-1010', 'usr-cli-03', 'CREATED', NULL, 'PENDING', '2026-11-12T09:00:00Z', 'Заявка на прожектор INV-LGT-002', 0),
('evt-23', 'bkg-1010', 'usr-mgr-01', 'CONFIRMED', 'PENDING', 'CONFIRMED', '2026-11-12T10:15:00Z', 'Погоджено', 0),
('evt-24', 'bkg-1010', 'usr-mgr-01', 'ISSUED', 'CONFIRMED', 'ISSUED', '2026-11-14T08:02:00Z', 'Видано клієнту', 0);

-- Записи черги очікування (Waitlist)
INSERT OR IGNORE INTO waitlist_entries (
    id, equipment_type_id, preferred_unit_id, client_user_id,
    desired_starts_at, desired_ends_at, status, contact_note, notified_at, created_at
) VALUES
('wlt-01', 'eqt-01', 'unit-gen-01', 'usr-cli-02',
 '2026-11-15T10:00:00Z', '2026-11-16T10:00:00Z', 'WAITING',
 'Потрібен саме генератор Honda EU22i на випадок дострокового повернення або скасування', NULL, '2026-11-13T12:00:00Z'),
('wlt-02', 'eqt-02', 'unit-eco-01', 'usr-cli-03',
 '2026-11-14T14:00:00Z', '2026-11-16T10:00:00Z', 'WAITING',
 'Готовий забрати станцію EcoFlow одразу після звільнення слота', NULL, '2026-11-13T15:40:00Z');
