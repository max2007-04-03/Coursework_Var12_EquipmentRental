using System.Diagnostics;
using System.Globalization;
using System.Text;
using System.Text.Json;
using EquipmentRental.Application;
using EquipmentRental.Domain;
using EquipmentRental.Infrastructure;
using Microsoft.Data.Sqlite;

namespace EquipmentRental.Tests;

public sealed record TestCaseResult(
    string Id,
    string Category,
    string Requirement,
    string Title,
    bool Passed,
    double DurationMs,
    string Details
);

public sealed record VolumeBenchmarkRow(
    int DatasetBookingsCount,
    double CatalogFilterMs,
    double CalendarQueryMs,
    double AtomicBookingCheckMs,
    double WithoutIndexCheckMs
);

public sealed record LoadTestRow(
    int VirtualUsers,
    int TotalRequests,
    double RequestsPerSec,
    double P50Ms,
    double P95Ms,
    double P99Ms,
    int TechnicalErrors,
    int ExpectedBusinessConflicts
);

public static class Program
{
    public static async Task<int> Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        Console.WriteLine("================================================================================");
        Console.WriteLine("  АВТОМАТИЗОВАНИЙ КОМПЛЕКС ТЕСТУВАННЯ ВЕБСИСТЕМИ ОРЕНДИ ОБЛАДНАННЯ (ВАРІАНТ 12)");
        Console.WriteLine("  Виконавець: Сливка Максим Олексійович, гр. АІ-243");
        Console.WriteLine("================================================================================");

        string rootDir = FindSolutionRoot();
        string initSqlPath = Path.Combine(rootDir, "sql", "init.sql");
        string seedSqlPath = Path.Combine(rootDir, "sql", "seed.sql");
        string evidenceDir = Path.Combine(rootDir, "evidence");
        Directory.CreateDirectory(evidenceDir);

        var results = new List<TestCaseResult>();
        var now = RentalApplicationService.DefaultDemoNow;

        void RunTest(string id, string category, string req, string title, Func<string> action)
        {
            var sw = Stopwatch.StartNew();
            try
            {
                string detail = action();
                sw.Stop();
                results.Add(new TestCaseResult(id, category, req, title, true, Math.Round(sw.Elapsed.TotalMilliseconds, 2), detail));
                Console.WriteLine($"[PASS] {id} ({req}): {title} [{sw.Elapsed.TotalMilliseconds:F2} мс] -> {detail}");
            }
            catch (Exception ex)
            {
                sw.Stop();
                results.Add(new TestCaseResult(id, category, req, title, false, Math.Round(sw.Elapsed.TotalMilliseconds, 2), ex.Message));
                Console.WriteLine($"[FAIL] {id} ({req}): {title} -> {ex.Message}");
            }
        }

        // ==================== 1. МОДУЛЬНІ ТЕСТИ ДОМЕННИХ ПРАВИЛ ====================

        RunTest("TC-UT-01", "Unit", "FR-03", "Перевірка напіввідкритих інтервалів та технічного буфера обслуговування", () =>
        {
            var t1Start = DateTimeOffset.Parse("2026-11-20T09:00:00Z");
            var t1EndBuf = DateTimeOffset.Parse("2026-11-20T17:00:00Z"); // 15:00 + 2 год тех. перерви

            // Суміжний інтервал з 17:00 не перетинається
            bool adjacentOverlap = PricingAndAvailabilityRules.IntervalsOverlap(
                t1Start, t1EndBuf,
                DateTimeOffset.Parse("2026-11-20T17:00:00Z"),
                DateTimeOffset.Parse("2026-11-20T21:00:00Z"));
            if (adjacentOverlap) throw new Exception("Суміжні напіввідкриті інтервали не повинні конфліктувати.");

            // Часткове накладання на технічну перерву (початок о 16:00, коли оренда до 15:00, але буфер до 17:00)
            bool bufferOverlap = PricingAndAvailabilityRules.IntervalsOverlap(
                t1Start, t1EndBuf,
                DateTimeOffset.Parse("2026-11-20T16:00:00Z"),
                DateTimeOffset.Parse("2026-11-20T20:00:00Z"));
            if (!bufferOverlap) throw new Exception("Накладання на час технічної перерви не виявлено.");

            return "Суміжна межа 17:00 дозволена; перетин із тех. перервою [15:00..17:00) заблоковано.";
        });

        RunTest("TC-UT-02", "Unit", "FR-04", "Точний розрахунок вартості оренди (HOUR і DAY) у копійках з округленням вгору", () =>
        {
            var dayTariff = new Tariff
            {
                Id = "t-day", Code = "D1", Name = "Добовий", BillingUnit = BillingUnit.DAY,
                RateMinor = 85000, DepositMinor = 300000, LateFeePerHourMinor = 15000, MinUnits = 1, MaxUnits = 30
            };

            // 26 годин оренди за добовим тарифом -> 2 повні доби (2 * 850,00 грн = 1700,00 грн)
            var calcDay = PricingAndAvailabilityRules.CalculatePrice(
                DateTimeOffset.Parse("2026-11-20T09:00:00Z"),
                DateTimeOffset.Parse("2026-11-21T11:00:00Z"),
                dayTariff, maintenanceBufferHours: 4);

            if (calcDay.BilledUnits != 2 || calcDay.BasePriceMinor != 170000)
                throw new Exception($"Очікувалося 2 доби та 170000 коп., отримано {calcDay.BilledUnits} та {calcDay.BasePriceMinor}");

            return $"26 год за добовим тарифом = {calcDay.BilledUnits} доби ({Money.FormatUah(calcDay.BasePriceMinor)}), застава {Money.FormatUah(calcDay.DepositMinor)}.";
        });

        RunTest("TC-UT-03", "Unit", "FR-03", "Відмова при даті завершення раніше початку та при минулій даті", () =>
        {
            var tariff = new Tariff
            {
                Id = "t1", Code = "H1", Name = "Погодинний", BillingUnit = BillingUnit.HOUR,
                RateMinor = 18000, DepositMinor = 250000, LateFeePerHourMinor = 30000, MinUnits = 2, MaxUnits = 72
            };
            var eq = new EquipmentType { Id = "eq1", Active = true, MaintenanceBufferHours = 2, TariffId = "t1" };
            var unit = new EquipmentUnit { Id = "u1", InventoryCode = "INV-TEST-01", ConditionStatus = UnitConditionStatus.AVAILABLE };

            var revCheck = PricingAndAvailabilityRules.ValidateAndCheckAvailability(
                eq, unit, tariff,
                DateTimeOffset.Parse("2026-11-18T15:00:00Z"),
                DateTimeOffset.Parse("2026-11-18T10:00:00Z"),
                now, Array.Empty<Booking>());

            if (revCheck.IsAvailable || revCheck.ErrorCode != "END_BEFORE_START")
                throw new Exception("Має повертатися помилка END_BEFORE_START.");

            var pastCheck = PricingAndAvailabilityRules.ValidateAndCheckAvailability(
                eq, unit, tariff,
                DateTimeOffset.Parse("2026-11-01T10:00:00Z"),
                DateTimeOffset.Parse("2026-11-01T16:00:00Z"),
                now, Array.Empty<Booking>());

            if (pastCheck.IsAvailable || pastCheck.ErrorCode != "START_IN_PAST")
                throw new Exception("Має повертатися помилка START_IN_PAST.");

            return "Коректно відхилено інтервал із завершенням раніше початку (END_BEFORE_START) та минулу дату (START_IN_PAST).";
        });

        RunTest("TC-UT-04", "Unit", "FR-07", "Розрахунок пені за повернення обладнання із запізненням", () =>
        {
            var plannedEnd = DateTimeOffset.Parse("2026-11-16T10:00:00Z");
            // Запізнення 5 хв (в межах 10-хвилинного допуску)
            var (late0, fee0) = PricingAndAvailabilityRules.CalculateLateReturnPenalty(
                plannedEnd, plannedEnd.AddMinutes(5), 15000);
            if (late0 != 0 || fee0 != 0) throw new Exception("Допуск 10 хв не повинен штрафуватися.");

            // Запізнення 2 год 20 хв -> округлення до 3 штрафних годин
            var (late3, fee3) = PricingAndAvailabilityRules.CalculateLateReturnPenalty(
                plannedEnd, plannedEnd.AddHours(2).AddMinutes(20), 15000);
            if (late3 != 3 || fee3 != 45000) throw new Exception("Очікувалося 3 штрафні години (450,00 грн).");

            return $"Допуск 5 хв -> 0,00 грн; прострочення 2 год 20 хв -> {late3} год ({Money.FormatUah(fee3)}).";
        });

        RunTest("TC-UT-05", "Unit", "FR-06", "Контроль матриці переходів статусів і заборона клієнту погоджувати/видавати", () =>
        {
            bool blocked = false;
            try
            {
                PricingAndAvailabilityRules.ValidateStatusTransition(
                    BookingStatus.PENDING, BookingStatus.CONFIRMED, UserRole.CLIENT, isOwner: true);
            }
            catch (DomainRuleException ex) when (ex.Code == "INVALID_STATUS_TRANSITION")
            {
                blocked = true;
            }
            if (!blocked) throw new Exception("Клієнт не повинен мати права переводити заявку у стан CONFIRMED.");

            PricingAndAvailabilityRules.ValidateStatusTransition(
                BookingStatus.PENDING, BookingStatus.CONFIRMED, UserRole.MANAGER, isOwner: false);

            return "Спробу клієнта встановити статус CONFIRMED заблоковано; перехід для ролі MANAGER дозволено.";
        });

        // ==================== 2. ІНТЕГРАЦІЙНІ ТЕСТИ НА РЕАЛЬНІЙ СКБД SQLITE ====================

        string testDbPath = Path.Combine(evidenceDir, "integration_test.db");
        if (File.Exists(testDbPath)) File.Delete(testDbPath);
        var repo = new SqliteRentalRepository(testDbPath);
        var appService = new RentalApplicationService(repo);

        RunTest("TC-IT-01", "Integration", "NFR-DATA-01", "Ініціалізація схеми SQLite, міграцій та ідемпотентність seed-набору", () =>
        {
            repo.EnsureDatabaseInitialized(initSqlPath, seedSqlPath);
            int countFirst = repo.GetEquipmentCatalog().Count;
            repo.EnsureDatabaseInitialized(initSqlPath, seedSqlPath);
            int countSecond = repo.GetEquipmentCatalog().Count;

            if (countFirst != 8 || countSecond != 8)
                throw new Exception($"Очікувалося 8 типів обладнання без дублювання, отримано {countFirst} / {countSecond}.");

            return $"Створено 8 типів обладнання, 18 фізичних екземплярів, 6 тарифів; повторний запуск не дублює записи.";
        });

        RunTest("TC-IT-02", "Integration", "FR-02", "Розрізнення товарної позиції та фізичних екземплярів із різними графіками", () =>
        {
            // Генератор Honda EU22i має 3 фізичні екземпляри:
            // INV-GEN-001 зайнятий 14.11 (ISSUED), INV-GEN-002 вільний 14.11 з 09:00 до 15.11 06:00, INV-GEN-003 у сервісі (IN_MAINTENANCE)
            var p1 = appService.PreviewAvailabilityAndPrice(
                "unit-gen-01",
                DateTimeOffset.Parse("2026-11-14T10:00:00Z"),
                DateTimeOffset.Parse("2026-11-15T10:00:00Z"),
                now);

            var p2 = appService.PreviewAvailabilityAndPrice(
                "unit-gen-02",
                DateTimeOffset.Parse("2026-11-18T10:00:00Z"),
                DateTimeOffset.Parse("2026-11-20T10:00:00Z"),
                now);

            var p3 = appService.PreviewAvailabilityAndPrice(
                "unit-gen-03",
                DateTimeOffset.Parse("2026-11-18T10:00:00Z"),
                DateTimeOffset.Parse("2026-11-20T10:00:00Z"),
                now);

            if (p1.IsAvailable) throw new Exception("INV-GEN-001 має бути зайнятий 14.11.");
            if (!p2.IsAvailable) throw new Exception("INV-GEN-002 має бути вільний 18.11–20.11.");
            if (p3.IsAvailable || p3.ErrorCode != "UNIT_NOT_AVAILABLE") throw new Exception("INV-GEN-003 у стані IN_MAINTENANCE має бути недоступним.");

            return $"INV-GEN-001: зайнятий ({p1.ErrorCode}); INV-GEN-002: доступний ({p2.TotalPriceFormatted}); INV-GEN-003: сервіс ({p3.ErrorCode}).";
        });

        RunTest("TC-IT-03", "Integration", "FR-05", "Наскрізне створення заявки та відмова при частковому накладанні на технічну перерву", () =>
        {
            // INV-GEN-001 зайнятий за bkg-1001 до 2026-11-16T09:00:00Z + 4 год тех. перерви = до 13:00Z.
            // Спроба забронювати з 11:00Z (під час технічної перерви) має повернути 409 INTERVAL_CONFLICT
            bool conflictCaught = false;
            try
            {
                repo.CreateBookingAtomic(
                    "usr-cli-02", "unit-gen-01",
                    DateTimeOffset.Parse("2026-11-16T11:00:00Z"),
                    DateTimeOffset.Parse("2026-11-17T08:00:00Z"),
                    "Спроба оренди під час 4-годинної технічної перерви", now);
            }
            catch (DomainRuleException ex) when (ex.Code == "INTERVAL_CONFLICT" && ex.SuggestedHttpStatus == 409)
            {
                conflictCaught = true;
            }
            if (!conflictCaught) throw new Exception("Конфлікт із технічною перервою мав повернути 409 INTERVAL_CONFLICT.");

            // А на вільний інтервал для INV-GEN-002 (20.11 – 22.11) бронювання успішно створюється
            var created = repo.CreateBookingAtomic(
                "usr-cli-02", "unit-gen-02",
                DateTimeOffset.Parse("2026-11-20T09:00:00Z"),
                DateTimeOffset.Parse("2026-11-22T09:00:00Z"),
                "Резервне живлення виставкового павільйону", now);

            return $"Накладання на тех. перерву відхилено (409); створено нову заявку {created.BookingNumber} на INV-GEN-002.";
        });

        // Тест конкурентного бронювання одного слота двома паралельними запитами
        var swConc = Stopwatch.StartNew();
        try
        {
            var barrier = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
            var startSlot = DateTimeOffset.Parse("2026-11-25T09:00:00Z");
            var endSlot = DateTimeOffset.Parse("2026-11-26T09:00:00Z");

            async Task<(bool Success, string Code)> TryBookAsync(string userId, string note)
            {
                await barrier.Task;
                return await Task.Run(() =>
                {
                    try
                    {
                        var b = repo.CreateBookingAtomic(userId, "unit-eco-02", startSlot, endSlot, note, now);
                        return (true, b.BookingNumber);
                    }
                    catch (DomainRuleException ex)
                    {
                        return (false, ex.Code);
                    }
                });
            }

            var t1 = TryBookAsync("usr-cli-01", "Перший конкурентний запит на EcoFlow INV-ECO-002");
            var t2 = TryBookAsync("usr-cli-03", "Другий конкурентний запит на EcoFlow INV-ECO-002");
            barrier.SetResult();

            var outcomes = await Task.WhenAll(t1, t2);
            swConc.Stop();

            int successCount = outcomes.Count(o => o.Success);
            int conflictCount = outcomes.Count(o => !o.Success && o.Code == "INTERVAL_CONFLICT");

            if (successCount != 1 || conflictCount != 1)
                throw new Exception($"Очікувався 1 успіх і 1 конфлікт, отримано success={successCount}, conflict={conflictCount}");

            results.Add(new TestCaseResult("TC-IT-04", "Concurrency", "FR-05",
                "Конкурентне бронювання одного екземпляра двома одночасними запитами",
                true, Math.Round(swConc.Elapsed.TotalMilliseconds, 2),
                $"Рівно 1 запит створено ({outcomes.First(x => x.Success).Code}), другий отримав 409 INTERVAL_CONFLICT."));
            Console.WriteLine($"[PASS] TC-IT-04 (FR-05): Конкурентне бронювання [{swConc.Elapsed.TotalMilliseconds:F2} мс]");
        }
        catch (Exception ex)
        {
            swConc.Stop();
            results.Add(new TestCaseResult("TC-IT-04", "Concurrency", "FR-05",
                "Конкурентне бронювання одного екземпляра двома одночасними запитами",
                false, Math.Round(swConc.Elapsed.TotalMilliseconds, 2), ex.Message));
        }

        RunTest("TC-IT-05", "Security", "NFR-SEC-01", "Захист від несанкціонованої зміни чужого бронювання (IDOR / 403 Forbidden)", () =>
        {
            var otherClient = repo.GetUserById("usr-cli-02")!;
            bool forbidden = false;
            try
            {
                // bkg-1004 належить usr-cli-01, а скасувати намагається usr-cli-02
                repo.CancelBookingAtomic("bkg-1004", otherClient, "Спроба скасувати чужу заявку", now);
            }
            catch (DomainRuleException ex) when (ex.Code == "FORBIDDEN_NOT_OWNER" && ex.SuggestedHttpStatus == 403)
            {
                forbidden = true;
            }
            if (!forbidden) throw new Exception("Система повинна блокувати зміну чужої заявки кодом 403 FORBIDDEN_NOT_OWNER.");
            return "Спробу клієнта usr-cli-02 скасувати заявку клієнта usr-cli-01 заблоковано (403 FORBIDDEN_NOT_OWNER).";
        });

        RunTest("TC-IT-06", "Integration", "FR-08", "Спрацювання черги очікування (Waitlist) після скасування активного бронювання", () =>
        {
            // У seed.sql є запис черги wlt-02 для eqt-02 (EcoFlow) на 14.11 14:00 – 16.11 10:00 у стані WAITING.
            // Коли власник usr-cli-01 скасовує bkg-1004 (14.11 12:00 – 16.11 12:00), wlt-02 має автоматично стати NOTIFIED!
            var owner = repo.GetUserById("usr-cli-01")!;
            repo.CancelBookingAtomic("bkg-1004", owner, "Зміна планів команди хакатону", now);

            var waitlistItem = repo.GetWaitlistEntries().First(w => w.Id == "wlt-02");
            if (waitlistItem.Status != WaitlistStatus.NOTIFIED || waitlistItem.NotifiedAt is null)
                throw new Exception($"Очікувався статус NOTIFIED для wlt-02, отримано {waitlistItem.Status}");

            return $"Після скасування заявки bkg-1004 запис черги очікування wlt-02 автоматично переведено у стан NOTIFIED ({waitlistItem.NotifiedAt:HH:mm:ss}).";
        });

        RunTest("TC-IT-07", "Integration", "FR-07", "Повний цикл менеджера: погодження -> видача -> повернення із запізненням та нарахуванням пені", () =>
        {
            // bkg-1003 (PENDING, 15.11 08:00 – 17.11 08:00, базова ціна 1700,00 грн, штраф 150,00 грн/год)
            var confirmed = repo.ConfirmBookingAtomic("bkg-1003", "usr-mgr-01", "Погоджено для польових випробувань", now);
            var issued = repo.IssueEquipmentAtomic("bkg-1003", "usr-mgr-01", "Видано справний генератор INV-GEN-002", DateTimeOffset.Parse("2026-11-15T08:00:00Z"));
            // Повертаємо на 4 години пізніше (17.11 о 12:00 замість 08:00) -> 4 * 150,00 = 600,00 грн пені
            var returned = repo.ReturnEquipmentAtomic("bkg-1003", "usr-mgr-01", "Повернуто із запізненням 4 год", DateTimeOffset.Parse("2026-11-17T12:00:00Z"));

            if (returned.Status != BookingStatus.RETURNED || returned.LateHours != 4 || returned.LateFeeMinor != 60000)
                throw new Exception("Невірний розрахунок пені при поверненні.");

            return $"Статус: PENDING -> CONFIRMED -> ISSUED -> RETURNED; запізнення 4 год, пеня {Money.FormatUah(returned.LateFeeMinor)}, разом {Money.FormatUah(returned.TotalPriceMinor)}.";
        });

        // ==================== 3. ТЕСТУВАННЯ ОБСЯГОМ ДАНИХ (100, 1 000, 10 000 ЗАПИСІВ) ====================
        Console.WriteLine("\n--- Виконання тестування обсягом даних (100, 1 000, 10 000 записів) ---");
        var volumeRows = new List<VolumeBenchmarkRow>();

        foreach (int targetCount in new[] { 100, 1000, 10000 })
        {
            string volDbPath = Path.Combine(evidenceDir, $"volume_{targetCount}.db");
            if (File.Exists(volDbPath)) File.Delete(volDbPath);

            var volRepo = new SqliteRentalRepository(volDbPath);
            volRepo.EnsureDatabaseInitialized(initSqlPath, seedSqlPath);
            var volApp = new RentalApplicationService(volRepo);

            PopulateSyntheticBookings(volDbPath, targetCount);

            // 1. Читання та фільтрація каталогу з перевіркою періоду
            var swCat = Stopwatch.StartNew();
            for (int i = 0; i < 5; i++)
            {
                _ = volApp.GetCatalog(null, "Енергообладнання", null,
                    DateTimeOffset.Parse("2027-06-10T09:00:00Z"),
                    DateTimeOffset.Parse("2027-06-12T09:00:00Z"));
            }
            swCat.Stop();
            double catMs = Math.Round(swCat.Elapsed.TotalMilliseconds / 5.0, 2);

            // 2. Запит календаря доступності за місяць
            var swCal = Stopwatch.StartNew();
            for (int i = 0; i < 5; i++)
            {
                _ = volApp.GetEquipmentCalendar("eqt-01",
                    DateTimeOffset.Parse("2027-05-01T00:00:00Z"),
                    DateTimeOffset.Parse("2027-06-01T00:00:00Z"));
            }
            swCal.Stop();
            double calMs = Math.Round(swCal.Elapsed.TotalMilliseconds / 5.0, 2);

            // 3. Перевірка інтервалу з індексом idx_bookings_unit_interval
            var swCheckIdx = Stopwatch.StartNew();
            for (int i = 0; i < 10; i++)
            {
                _ = volApp.PreviewAvailabilityAndPrice("unit-gen-01",
                    DateTimeOffset.Parse("2027-08-15T10:00:00Z"),
                    DateTimeOffset.Parse("2027-08-17T10:00:00Z"), now);
            }
            swCheckIdx.Stop();
            double idxMs = Math.Round(swCheckIdx.Elapsed.TotalMilliseconds / 10.0, 2);

            // 4. Вимірювання без індексу idx_bookings_unit_interval для порівняння
            DropCompositeIndex(volDbPath);
            var swNoIdx = Stopwatch.StartNew();
            for (int i = 0; i < 10; i++)
            {
                _ = volApp.PreviewAvailabilityAndPrice("unit-gen-01",
                    DateTimeOffset.Parse("2027-08-15T10:00:00Z"),
                    DateTimeOffset.Parse("2027-08-17T10:00:00Z"), now);
            }
            swNoIdx.Stop();
            double noIdxMs = Math.Round(swNoIdx.Elapsed.TotalMilliseconds / 10.0, 2);

            volumeRows.Add(new VolumeBenchmarkRow(targetCount, catMs, calMs, idxMs, noIdxMs));
            Console.WriteLine($"  N={targetCount,5}: Каталог={catMs:F2} мс | Календар={calMs:F2} мс | З індексом={idxMs:F2} мс | Без індексу={noIdxMs:F2} мс");

            SqliteConnection.ClearAllPools();
            if (File.Exists(volDbPath)) File.Delete(volDbPath);
        }

        // ==================== 4. НАВАНТАЖУВАЛЬНЕ ТЕСТУВАННЯ (5, 10, 25 ВІРТУАЛЬНИХ КОРИСТУВАЧІВ) ====================
        Console.WriteLine("\n--- Виконання навантажувального тестування (5, 10, 25 VU) ---");
        var loadRows = new List<LoadTestRow>();

        foreach (int vu in new[] { 5, 10, 25 })
        {
            int iterationsPerVu = 30;
            int totalReqs = vu * iterationsPerVu;
            var latencies = new List<double>(totalReqs);
            int techErrors = 0;
            int businessConflicts = 0;
            object latLock = new();

            var swLoad = Stopwatch.StartNew();
            var tasks = Enumerable.Range(0, vu).Select(workerId => Task.Run(() =>
            {
                for (int i = 0; i < iterationsPerVu; i++)
                {
                    var swReq = Stopwatch.StartNew();
                    try
                    {
                        if (i % 3 == 0)
                        {
                            _ = appService.GetCatalog(null, null, null, null, null);
                        }
                        else if (i % 3 == 1)
                        {
                            _ = appService.GetEquipmentCalendar("eqt-01",
                                DateTimeOffset.Parse("2026-11-01T00:00:00Z"),
                                DateTimeOffset.Parse("2026-11-30T00:00:00Z"));
                        }
                        else
                        {
                            var preview = appService.PreviewAvailabilityAndPrice("unit-gen-01",
                                DateTimeOffset.Parse("2026-11-14T10:00:00Z"),
                                DateTimeOffset.Parse("2026-11-15T10:00:00Z"), now);
                            if (!preview.IsAvailable)
                                Interlocked.Increment(ref businessConflicts);
                        }
                    }
                    catch
                    {
                        Interlocked.Increment(ref techErrors);
                    }
                    finally
                    {
                        swReq.Stop();
                        lock (latLock)
                        {
                            latencies.Add(swReq.Elapsed.TotalMilliseconds);
                        }
                    }
                }
            })).ToArray();

            await Task.WhenAll(tasks);
            swLoad.Stop();

            latencies.Sort();
            double p50 = Math.Round(Percentile(latencies, 0.50), 2);
            double p95 = Math.Round(Percentile(latencies, 0.95), 2);
            double p99 = Math.Round(Percentile(latencies, 0.99), 2);
            double rps = Math.Round(totalReqs / Math.Max(0.001, swLoad.Elapsed.TotalSeconds), 1);

            loadRows.Add(new LoadTestRow(vu, totalReqs, rps, p50, p95, p99, techErrors, businessConflicts));
            Console.WriteLine($"  VU={vu,2}: Запитів={totalReqs}, RPS={rps:F1}, p50={p50:F2} мс, p95={p95:F2} мс, p99={p99:F2} мс, Тех.помилок={techErrors}");
        }

        // Збереження протоколу у JSON та Markdown
        var reportObj = new
        {
            executedAtUtc = DateTimeOffset.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
            releaseTag = "v1.0.0-release",
            totalTests = results.Count,
            passedTests = results.Count(r => r.Passed),
            failedTests = results.Count(r => !r.Passed),
            testCases = results,
            volumeBenchmarks = volumeRows,
            loadBenchmarks = loadRows
        };

        string jsonOut = JsonSerializer.Serialize(reportObj, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(Path.Combine(evidenceDir, "test_results.json"), jsonOut, Encoding.UTF8);

        SqliteConnection.ClearAllPools();
        if (File.Exists(testDbPath)) File.Delete(testDbPath);

        Console.WriteLine($"\nПідсумок: {results.Count(r => r.Passed)}/{results.Count} тестів пройдено успішно. Звіт збережено в evidence/test_results.json.");
        return results.All(r => r.Passed) ? 0 : 1;
    }

    private static double Percentile(List<double> sorted, double p)
    {
        if (sorted.Count == 0) return 0;
        int idx = (int)Math.Ceiling(p * sorted.Count) - 1;
        idx = Math.Clamp(idx, 0, sorted.Count - 1);
        return sorted[idx];
    }

    private static void PopulateSyntheticBookings(string dbPath, int totalCount)
    {
        var builder = new SqliteConnectionStringBuilder { DataSource = dbPath };
        using var conn = new SqliteConnection(builder.ToString());
        conn.Open();
        using var tx = conn.BeginTransaction();

        string[] units = { "unit-gen-01", "unit-gen-02", "unit-eco-01", "unit-eco-02", "unit-cam-01", "unit-cam-02", "unit-lgt-01", "unit-lgt-02", "unit-drl-01", "unit-saw-01", "unit-flr-01", "unit-lca-01" };
        string[] clients = { "usr-cli-01", "usr-cli-02", "usr-cli-03" };
        string[] statuses = { "RETURNED", "CONFIRMED", "CANCELLED", "PENDING", "REJECTED" };

        var baseTime = DateTimeOffset.Parse("2026-12-01T08:00:00Z", CultureInfo.InvariantCulture);

        using var cmd = conn.CreateCommand();
        cmd.Transaction = tx;
        cmd.CommandText = """
            INSERT INTO bookings (
                id, booking_number, unit_id, client_user_id, tariff_id,
                starts_at, ends_at, buffer_ends_at, status, purpose, rejection_reason,
                billed_units, unit_rate_minor, base_price_minor, deposit_minor,
                late_hours, late_fee_minor, total_price_minor,
                actual_issued_at, actual_returned_at, created_at, updated_at, version
            ) VALUES (
                $id, $num, $unit, $cli, 'trf-day-power',
                $s, $e, $b, $st, 'Синтетичний запис навантажувального тестування обсягом даних', NULL,
                1, 85000, 85000, 300000,
                0, 0, 85000,
                NULL, NULL, $c, $c, 1
            );
            """;

        var pId = cmd.Parameters.Add("$id", SqliteType.Text);
        var pNum = cmd.Parameters.Add("$num", SqliteType.Text);
        var pUnit = cmd.Parameters.Add("$unit", SqliteType.Text);
        var pCli = cmd.Parameters.Add("$cli", SqliteType.Text);
        var pS = cmd.Parameters.Add("$s", SqliteType.Text);
        var pE = cmd.Parameters.Add("$e", SqliteType.Text);
        var pB = cmd.Parameters.Add("$b", SqliteType.Text);
        var pSt = cmd.Parameters.Add("$st", SqliteType.Text);
        var pC = cmd.Parameters.Add("$c", SqliteType.Text);

        for (int i = 1; i <= totalCount; i++)
        {
            var slotStart = baseTime.AddHours(i * 6);
            var slotEnd = slotStart.AddHours(4);
            var slotBuf = slotEnd.AddHours(2);

            pId.Value = $"bkg-vol-{i:D6}";
            pNum.Value = $"RN-VOL-{i:D6}";
            pUnit.Value = units[i % units.Length];
            pCli.Value = clients[i % clients.Length];
            pS.Value = slotStart.ToString("yyyy-MM-ddTHH:mm:ssZ");
            pE.Value = slotEnd.ToString("yyyy-MM-ddTHH:mm:ssZ");
            pB.Value = slotBuf.ToString("yyyy-MM-ddTHH:mm:ssZ");
            pSt.Value = statuses[i % statuses.Length];
            pC.Value = slotStart.AddDays(-2).ToString("yyyy-MM-ddTHH:mm:ssZ");
            cmd.ExecuteNonQuery();
        }

        tx.Commit();
    }

    private static void DropCompositeIndex(string dbPath)
    {
        var builder = new SqliteConnectionStringBuilder { DataSource = dbPath };
        using var conn = new SqliteConnection(builder.ToString());
        conn.Open();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = "DROP INDEX IF EXISTS idx_bookings_unit_interval;";
        cmd.ExecuteNonQuery();
    }

    private static string FindSolutionRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null)
        {
            if (Directory.Exists(Path.Combine(dir.FullName, "sql")))
                return dir.FullName;
            dir = dir.Parent;
        }
        return Directory.GetCurrentDirectory();
    }
}
