using System.Globalization;
using EquipmentRental.Domain;
using Microsoft.Data.Sqlite;

namespace EquipmentRental.Infrastructure;

/// <summary>
/// Реляційний репозиторій SQLite із параметризованими SQL-запитами,
/// атомарними транзакціями бронювання та контролем цілісності.
/// </summary>
public sealed class SqliteRentalRepository : IRentalRepository
{
    private readonly string _connectionString;
    private static readonly object WriteLock = new();

    public SqliteRentalRepository(string dbFilePath)
    {
        var dir = Path.GetDirectoryName(dbFilePath);
        if (!string.IsNullOrEmpty(dir))
            Directory.CreateDirectory(dir);

        var builder = new SqliteConnectionStringBuilder
        {
            DataSource = dbFilePath,
            Mode = SqliteOpenMode.ReadWriteCreate,
            ForeignKeys = true,
            Pooling = true,
            DefaultTimeout = 10
        };
        _connectionString = builder.ToString();
    }

    private SqliteConnection OpenConnection()
    {
        var conn = new SqliteConnection(_connectionString);
        conn.Open();
        using var pragma = conn.CreateCommand();
        pragma.CommandText = "PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL; PRAGMA busy_timeout = 5000;";
        pragma.ExecuteNonQuery();
        return conn;
    }

    public void EnsureDatabaseInitialized(string initSqlPath, string seedSqlPath)
    {
        lock (WriteLock)
        {
            using var conn = OpenConnection();
            string initSql = File.ReadAllText(initSqlPath);
            using (var cmd = conn.CreateCommand())
            {
                cmd.CommandText = initSql;
                cmd.ExecuteNonQuery();
            }

            using var checkCmd = conn.CreateCommand();
            checkCmd.CommandText = "SELECT COUNT(*) FROM equipment_types;";
            long count = (long)(checkCmd.ExecuteScalar() ?? 0L);

            if (count == 0 && File.Exists(seedSqlPath))
            {
                string seedSql = File.ReadAllText(seedSqlPath);
                using var seedCmd = conn.CreateCommand();
                seedCmd.CommandText = seedSql;
                seedCmd.ExecuteNonQuery();
            }
        }
    }

    private static DateTimeOffset ParseIso(string value) =>
        DateTimeOffset.Parse(value, CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal);

    private static string FormatIso(DateTimeOffset value) =>
        value.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture);

    public User? GetUserByEmail(string email)
    {
        using var conn = OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = """
            SELECT id, email, full_name, phone, role, password_hash, created_at
            FROM users
            WHERE email = $email COLLATE NOCASE
            LIMIT 1;
            """;
        cmd.Parameters.AddWithValue("$email", email.Trim());
        using var r = cmd.ExecuteReader();
        return r.Read() ? ReadUser(r) : null;
    }

    public User? GetUserById(string id)
    {
        using var conn = OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = """
            SELECT id, email, full_name, phone, role, password_hash, created_at
            FROM users
            WHERE id = $id
            LIMIT 1;
            """;
        cmd.Parameters.AddWithValue("$id", id);
        using var r = cmd.ExecuteReader();
        return r.Read() ? ReadUser(r) : null;
    }

    public IReadOnlyList<User> GetAllUsers()
    {
        using var conn = OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = """
            SELECT id, email, full_name, phone, role, password_hash, created_at
            FROM users
            ORDER BY role DESC, full_name ASC;
            """;
        using var r = cmd.ExecuteReader();
        var list = new List<User>();
        while (r.Read()) list.Add(ReadUser(r));
        return list;
    }

    private static User ReadUser(SqliteDataReader r) => new()
    {
        Id = r.GetString(0),
        Email = r.GetString(1),
        FullName = r.GetString(2),
        Phone = r.GetString(3),
        Role = Enum.Parse<UserRole>(r.GetString(4), true),
        PasswordHash = r.GetString(5),
        CreatedAt = ParseIso(r.GetString(6))
    };

    public IReadOnlyList<Tariff> GetAllTariffs()
    {
        using var conn = OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = """
            SELECT id, code, name, billing_unit, rate_minor, deposit_minor, late_fee_per_hour_minor, min_units, max_units
            FROM tariffs
            ORDER BY rate_minor ASC;
            """;
        using var r = cmd.ExecuteReader();
        var list = new List<Tariff>();
        while (r.Read()) list.Add(ReadTariff(r));
        return list;
    }

    public Tariff? GetTariffById(string id)
    {
        using var conn = OpenConnection();
        return GetTariffByIdInternal(conn, null, id);
    }

    private static Tariff? GetTariffByIdInternal(SqliteConnection conn, SqliteTransaction? tx, string id)
    {
        using var cmd = conn.CreateCommand();
        cmd.Transaction = tx;
        cmd.CommandText = """
            SELECT id, code, name, billing_unit, rate_minor, deposit_minor, late_fee_per_hour_minor, min_units, max_units
            FROM tariffs
            WHERE id = $id
            LIMIT 1;
            """;
        cmd.Parameters.AddWithValue("$id", id);
        using var r = cmd.ExecuteReader();
        return r.Read() ? ReadTariff(r) : null;
    }

    private static Tariff ReadTariff(SqliteDataReader r) => new()
    {
        Id = r.GetString(0),
        Code = r.GetString(1),
        Name = r.GetString(2),
        BillingUnit = Enum.Parse<BillingUnit>(r.GetString(3), true),
        RateMinor = r.GetInt64(4),
        DepositMinor = r.GetInt64(5),
        LateFeePerHourMinor = r.GetInt64(6),
        MinUnits = r.GetInt32(7),
        MaxUnits = r.GetInt32(8)
    };

    public IReadOnlyList<EquipmentType> GetEquipmentCatalog(
        string? search = null,
        string? category = null,
        string? billingUnit = null,
        DateTimeOffset? availableFrom = null,
        DateTimeOffset? availableTo = null)
    {
        using var conn = OpenConnection();
        var tariffs = GetAllTariffs().ToDictionary(t => t.Id);

        using var cmd = conn.CreateCommand();
        var sql = """
            SELECT id, slug, title, category, brand_model, description, specs_json, tariff_id, maintenance_buffer_hours, active, image_tag
            FROM equipment_types
            WHERE 1=1
            """;

        if (!string.IsNullOrWhiteSpace(category) && !string.Equals(category, "ALL", StringComparison.OrdinalIgnoreCase))
        {
            sql += " AND category = $category";
            cmd.Parameters.AddWithValue("$category", category.Trim());
        }

        if (!string.IsNullOrWhiteSpace(search))
        {
            sql += """
                 AND (
                    title LIKE $q COLLATE NOCASE
                    OR brand_model LIKE $q COLLATE NOCASE
                    OR description LIKE $q COLLATE NOCASE
                    OR EXISTS (
                        SELECT 1 FROM equipment_units u
                        WHERE u.equipment_type_id = equipment_types.id
                          AND (u.inventory_code LIKE $q COLLATE NOCASE OR u.serial_number LIKE $q COLLATE NOCASE)
                    )
                 )
                """;
            cmd.Parameters.AddWithValue("$q", $"%{search.Trim()}%");
        }

        sql += " ORDER BY category ASC, title ASC;";
        cmd.CommandText = sql;

        var types = new List<EquipmentType>();
        using (var r = cmd.ExecuteReader())
        {
            while (r.Read())
            {
                var eq = ReadEquipmentType(r);
                if (tariffs.TryGetValue(eq.TariffId, out var t))
                    eq.Tariff = t;
                types.Add(eq);
            }
        }

        if (!string.IsNullOrWhiteSpace(billingUnit) && !string.Equals(billingUnit, "ALL", StringComparison.OrdinalIgnoreCase))
        {
            types = types.Where(t => t.Tariff is not null &&
                string.Equals(t.Tariff.BillingUnit.ToString(), billingUnit.Trim(), StringComparison.OrdinalIgnoreCase)).ToList();
        }

        foreach (var eq in types)
        {
            eq.Units = GetUnitsByTypeIdInternal(conn, null, eq.Id).ToList();
        }

        return types;
    }

    public EquipmentType? GetEquipmentTypeById(string id)
    {
        using var conn = OpenConnection();
        return GetEquipmentTypeByIdInternal(conn, null, id);
    }

    private static EquipmentType? GetEquipmentTypeByIdInternal(SqliteConnection conn, SqliteTransaction? tx, string id)
    {
        using var cmd = conn.CreateCommand();
        cmd.Transaction = tx;
        cmd.CommandText = """
            SELECT id, slug, title, category, brand_model, description, specs_json, tariff_id, maintenance_buffer_hours, active, image_tag
            FROM equipment_types
            WHERE id = $id
            LIMIT 1;
            """;
        cmd.Parameters.AddWithValue("$id", id);
        EquipmentType? eq = null;
        using (var r = cmd.ExecuteReader())
        {
            if (r.Read()) eq = ReadEquipmentType(r);
        }
        if (eq is null) return null;

        eq.Tariff = GetTariffByIdInternal(conn, tx, eq.TariffId);
        eq.Units = GetUnitsByTypeIdInternal(conn, tx, eq.Id).ToList();
        return eq;
    }

    private static EquipmentType ReadEquipmentType(SqliteDataReader r) => new()
    {
        Id = r.GetString(0),
        Slug = r.GetString(1),
        Title = r.GetString(2),
        Category = r.GetString(3),
        BrandModel = r.GetString(4),
        Description = r.GetString(5),
        SpecsJson = r.GetString(6),
        TariffId = r.GetString(7),
        MaintenanceBufferHours = r.GetInt32(8),
        Active = r.GetInt32(9) == 1,
        ImageTag = r.GetString(10)
    };

    public EquipmentUnit? GetEquipmentUnitById(string unitId)
    {
        using var conn = OpenConnection();
        return GetEquipmentUnitByIdInternal(conn, null, unitId);
    }

    private static EquipmentUnit? GetEquipmentUnitByIdInternal(SqliteConnection conn, SqliteTransaction? tx, string unitId)
    {
        using var cmd = conn.CreateCommand();
        cmd.Transaction = tx;
        cmd.CommandText = """
            SELECT id, equipment_type_id, inventory_code, serial_number, condition_status, warehouse_location, notes
            FROM equipment_units
            WHERE id = $id
            LIMIT 1;
            """;
        cmd.Parameters.AddWithValue("$id", unitId);
        using var r = cmd.ExecuteReader();
        return r.Read() ? ReadEquipmentUnit(r) : null;
    }

    public IReadOnlyList<EquipmentUnit> GetUnitsByTypeId(string equipmentTypeId)
    {
        using var conn = OpenConnection();
        return GetUnitsByTypeIdInternal(conn, null, equipmentTypeId);
    }

    private static IReadOnlyList<EquipmentUnit> GetUnitsByTypeIdInternal(SqliteConnection conn, SqliteTransaction? tx, string equipmentTypeId)
    {
        using var cmd = conn.CreateCommand();
        cmd.Transaction = tx;
        cmd.CommandText = """
            SELECT id, equipment_type_id, inventory_code, serial_number, condition_status, warehouse_location, notes
            FROM equipment_units
            WHERE equipment_type_id = $typeId
            ORDER BY inventory_code ASC;
            """;
        cmd.Parameters.AddWithValue("$typeId", equipmentTypeId);
        using var r = cmd.ExecuteReader();
        var list = new List<EquipmentUnit>();
        while (r.Read()) list.Add(ReadEquipmentUnit(r));
        return list;
    }

    private static EquipmentUnit ReadEquipmentUnit(SqliteDataReader r) => new()
    {
        Id = r.GetString(0),
        EquipmentTypeId = r.GetString(1),
        InventoryCode = r.GetString(2),
        SerialNumber = r.GetString(3),
        ConditionStatus = Enum.Parse<UnitConditionStatus>(r.GetString(4), true),
        WarehouseLocation = r.GetString(5),
        Notes = r.GetString(6)
    };

    public void UpdateUnitCondition(string unitId, UnitConditionStatus newStatus, string notes)
    {
        lock (WriteLock)
        {
            using var conn = OpenConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = """
                UPDATE equipment_units
                SET condition_status = $status, notes = $notes
                WHERE id = $id;
                """;
            cmd.Parameters.AddWithValue("$status", newStatus.ToString());
            cmd.Parameters.AddWithValue("$notes", notes ?? "");
            cmd.Parameters.AddWithValue("$id", unitId);
            int affected = cmd.ExecuteNonQuery();
            if (affected == 0)
                throw new DomainRuleException("UNIT_NOT_FOUND", $"Екземпляр {unitId} не знайдено.", 404);
        }
    }

    public IReadOnlyList<Booking> GetActiveBookingsForUnit(string unitId)
    {
        using var conn = OpenConnection();
        return GetActiveBookingsForUnitInternal(conn, null, unitId);
    }

    private static IReadOnlyList<Booking> GetActiveBookingsForUnitInternal(SqliteConnection conn, SqliteTransaction? tx, string unitId)
    {
        using var cmd = conn.CreateCommand();
        cmd.Transaction = tx;
        cmd.CommandText = """
            SELECT b.id, b.booking_number, b.unit_id, b.client_user_id, b.tariff_id,
                   b.starts_at, b.ends_at, b.buffer_ends_at, b.status, b.purpose, b.rejection_reason,
                   b.billed_units, b.unit_rate_minor, b.base_price_minor, b.deposit_minor,
                   b.late_hours, b.late_fee_minor, b.total_price_minor,
                   b.actual_issued_at, b.actual_returned_at, b.created_at, b.updated_at, b.version,
                   u.inventory_code, et.title, et.id, usr.full_name, usr.email, t.billing_unit
            FROM bookings b
            JOIN equipment_units u ON u.id = b.unit_id
            JOIN equipment_types et ON et.id = u.equipment_type_id
            JOIN users usr ON usr.id = b.client_user_id
            JOIN tariffs t ON t.id = b.tariff_id
            WHERE b.unit_id = $unitId
              AND b.status IN ('PENDING', 'CONFIRMED', 'ISSUED')
            ORDER BY b.starts_at ASC;
            """;
        cmd.Parameters.AddWithValue("$unitId", unitId);
        using var r = cmd.ExecuteReader();
        var list = new List<Booking>();
        while (r.Read()) list.Add(ReadBookingJoined(r));
        return list;
    }

    public IReadOnlyList<Booking> GetBookingsForTypeInPeriod(string equipmentTypeId, DateTimeOffset from, DateTimeOffset to)
    {
        using var conn = OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = """
            SELECT b.id, b.booking_number, b.unit_id, b.client_user_id, b.tariff_id,
                   b.starts_at, b.ends_at, b.buffer_ends_at, b.status, b.purpose, b.rejection_reason,
                   b.billed_units, b.unit_rate_minor, b.base_price_minor, b.deposit_minor,
                   b.late_hours, b.late_fee_minor, b.total_price_minor,
                   b.actual_issued_at, b.actual_returned_at, b.created_at, b.updated_at, b.version,
                   u.inventory_code, et.title, et.id, usr.full_name, usr.email, t.billing_unit
            FROM bookings b
            JOIN equipment_units u ON u.id = b.unit_id
            JOIN equipment_types et ON et.id = u.equipment_type_id
            JOIN users usr ON usr.id = b.client_user_id
            JOIN tariffs t ON t.id = b.tariff_id
            WHERE u.equipment_type_id = $typeId
              AND b.status IN ('PENDING', 'CONFIRMED', 'ISSUED')
              AND b.starts_at < $to
              AND b.buffer_ends_at > $from
            ORDER BY u.inventory_code ASC, b.starts_at ASC;
            """;
        cmd.Parameters.AddWithValue("$typeId", equipmentTypeId);
        cmd.Parameters.AddWithValue("$from", FormatIso(from));
        cmd.Parameters.AddWithValue("$to", FormatIso(to));
        using var r = cmd.ExecuteReader();
        var list = new List<Booking>();
        while (r.Read()) list.Add(ReadBookingJoined(r));
        return list;
    }

    public IReadOnlyList<Booking> GetBookings(string? clientUserId = null, string? statusFilter = null, string? unitId = null)
    {
        using var conn = OpenConnection();
        using var cmd = conn.CreateCommand();
        var sql = """
            SELECT b.id, b.booking_number, b.unit_id, b.client_user_id, b.tariff_id,
                   b.starts_at, b.ends_at, b.buffer_ends_at, b.status, b.purpose, b.rejection_reason,
                   b.billed_units, b.unit_rate_minor, b.base_price_minor, b.deposit_minor,
                   b.late_hours, b.late_fee_minor, b.total_price_minor,
                   b.actual_issued_at, b.actual_returned_at, b.created_at, b.updated_at, b.version,
                   u.inventory_code, et.title, et.id, usr.full_name, usr.email, t.billing_unit
            FROM bookings b
            JOIN equipment_units u ON u.id = b.unit_id
            JOIN equipment_types et ON et.id = u.equipment_type_id
            JOIN users usr ON usr.id = b.client_user_id
            JOIN tariffs t ON t.id = b.tariff_id
            WHERE 1=1
            """;

        if (!string.IsNullOrWhiteSpace(clientUserId))
        {
            sql += " AND b.client_user_id = $clientId";
            cmd.Parameters.AddWithValue("$clientId", clientUserId);
        }
        if (!string.IsNullOrWhiteSpace(statusFilter) && !string.Equals(statusFilter, "ALL", StringComparison.OrdinalIgnoreCase))
        {
            sql += " AND b.status = $status";
            cmd.Parameters.AddWithValue("$status", statusFilter.Trim().ToUpperInvariant());
        }
        if (!string.IsNullOrWhiteSpace(unitId))
        {
            sql += " AND b.unit_id = $unitId";
            cmd.Parameters.AddWithValue("$unitId", unitId);
        }

        sql += " ORDER BY b.created_at DESC, b.booking_number DESC;";
        cmd.CommandText = sql;

        using var r = cmd.ExecuteReader();
        var list = new List<Booking>();
        while (r.Read()) list.Add(ReadBookingJoined(r));
        return list;
    }

    public Booking? GetBookingById(string bookingId)
    {
        using var conn = OpenConnection();
        return GetBookingByIdInternal(conn, null, bookingId);
    }

    private static Booking? GetBookingByIdInternal(SqliteConnection conn, SqliteTransaction? tx, string bookingId)
    {
        using var cmd = conn.CreateCommand();
        cmd.Transaction = tx;
        cmd.CommandText = """
            SELECT b.id, b.booking_number, b.unit_id, b.client_user_id, b.tariff_id,
                   b.starts_at, b.ends_at, b.buffer_ends_at, b.status, b.purpose, b.rejection_reason,
                   b.billed_units, b.unit_rate_minor, b.base_price_minor, b.deposit_minor,
                   b.late_hours, b.late_fee_minor, b.total_price_minor,
                   b.actual_issued_at, b.actual_returned_at, b.created_at, b.updated_at, b.version,
                   u.inventory_code, et.title, et.id, usr.full_name, usr.email, t.billing_unit
            FROM bookings b
            JOIN equipment_units u ON u.id = b.unit_id
            JOIN equipment_types et ON et.id = u.equipment_type_id
            JOIN users usr ON usr.id = b.client_user_id
            JOIN tariffs t ON t.id = b.tariff_id
            WHERE b.id = $id
            LIMIT 1;
            """;
        cmd.Parameters.AddWithValue("$id", bookingId);
        using var r = cmd.ExecuteReader();
        return r.Read() ? ReadBookingJoined(r) : null;
    }

    private static Booking ReadBookingJoined(SqliteDataReader r) => new()
    {
        Id = r.GetString(0),
        BookingNumber = r.GetString(1),
        UnitId = r.GetString(2),
        ClientUserId = r.GetString(3),
        TariffId = r.GetString(4),
        StartsAt = ParseIso(r.GetString(5)),
        EndsAt = ParseIso(r.GetString(6)),
        BufferEndsAt = ParseIso(r.GetString(7)),
        Status = Enum.Parse<BookingStatus>(r.GetString(8), true),
        Purpose = r.GetString(9),
        RejectionReason = r.IsDBNull(10) ? null : r.GetString(10),
        BilledUnits = r.GetInt32(11),
        UnitRateMinor = r.GetInt64(12),
        BasePriceMinor = r.GetInt64(13),
        DepositMinor = r.GetInt64(14),
        LateHours = r.GetInt32(15),
        LateFeeMinor = r.GetInt64(16),
        TotalPriceMinor = r.GetInt64(17),
        ActualIssuedAt = r.IsDBNull(18) ? null : ParseIso(r.GetString(18)),
        ActualReturnedAt = r.IsDBNull(19) ? null : ParseIso(r.GetString(19)),
        CreatedAt = ParseIso(r.GetString(20)),
        UpdatedAt = ParseIso(r.GetString(21)),
        Version = r.GetInt32(22),
        InventoryCode = r.GetString(23),
        EquipmentTitle = r.GetString(24),
        EquipmentTypeId = r.GetString(25),
        ClientName = r.GetString(26),
        ClientEmail = r.GetString(27),
        BillingUnitName = r.GetString(28)
    };

    public IReadOnlyList<RentalEvent> GetEventsForBooking(string bookingId)
    {
        using var conn = OpenConnection();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = """
            SELECT e.id, e.booking_id, e.actor_user_id, u.full_name, e.event_type,
                   e.old_status, e.new_status, e.occurred_at, e.notes, e.penalty_added_minor
            FROM rental_events e
            JOIN users u ON u.id = e.actor_user_id
            WHERE e.booking_id = $bookingId
            ORDER BY e.occurred_at ASC, e.id ASC;
            """;
        cmd.Parameters.AddWithValue("$bookingId", bookingId);
        using var r = cmd.ExecuteReader();
        var list = new List<RentalEvent>();
        while (r.Read())
        {
            list.Add(new RentalEvent
            {
                Id = r.GetString(0),
                BookingId = r.GetString(1),
                ActorUserId = r.GetString(2),
                ActorName = r.GetString(3),
                EventType = r.GetString(4),
                OldStatus = r.IsDBNull(5) ? null : r.GetString(5),
                NewStatus = r.GetString(6),
                OccurredAt = ParseIso(r.GetString(7)),
                Notes = r.GetString(8),
                PenaltyAddedMinor = r.GetInt64(9)
            });
        }
        return list;
    }

    /// <summary>
    /// Атомарне створення заявки на бронювання фізичного екземпляра всередині транзакції.
    /// Повторно перевіряє доступність екземпляра, тариф і відсутність перетину інтервалів.
    /// </summary>
    public Booking CreateBookingAtomic(
        string clientUserId,
        string unitId,
        DateTimeOffset startsAt,
        DateTimeOffset endsAt,
        string purpose,
        DateTimeOffset referenceNow)
    {
        string trimmedPurpose = (purpose ?? "").Trim();
        if (trimmedPurpose.Length < 5 || trimmedPurpose.Length > 300)
            throw new DomainRuleException("INVALID_PURPOSE", "Мета використання обладнання має містити від 5 до 300 символів.", 400);

        lock (WriteLock)
        {
            using var conn = OpenConnection();
            using var tx = conn.BeginTransaction();
            try
            {
                var unit = GetEquipmentUnitByIdInternal(conn, tx, unitId)
                    ?? throw new DomainRuleException("UNIT_NOT_FOUND", $"Фізичний екземпляр «{unitId}» не знайдено.", 404);

                var eqType = GetEquipmentTypeByIdInternal(conn, tx, unit.EquipmentTypeId)
                    ?? throw new DomainRuleException("EQUIPMENT_NOT_FOUND", "Тип обладнання не знайдено.", 404);

                var tariff = eqType.Tariff
                    ?? throw new DomainRuleException("TARIFF_NOT_FOUND", "Тарифний план не знайдено.", 404);

                var activeBookings = GetActiveBookingsForUnitInternal(conn, tx, unit.Id);
                var check = PricingAndAvailabilityRules.ValidateAndCheckAvailability(
                    eqType, unit, tariff, startsAt, endsAt, referenceNow, activeBookings);

                if (!check.IsAvailable)
                {
                    int status = check.ErrorCode == "INTERVAL_CONFLICT" ? 409 : 400;
                    throw new DomainRuleException(check.ErrorCode ?? "BOOKING_REJECTED", check.ErrorMessage ?? "Неможливо створити бронювання.", status);
                }

                var price = PricingAndAvailabilityRules.CalculatePrice(startsAt, endsAt, tariff, eqType.MaintenanceBufferHours);
                string bookingId = "bkg-" + Guid.NewGuid().ToString("N")[..10];

                using var seqCmd = conn.CreateCommand();
                seqCmd.Transaction = tx;
                seqCmd.CommandText = "SELECT COUNT(*) + 1001 FROM bookings;";
                long seqNum = (long)(seqCmd.ExecuteScalar() ?? 1001L);
                string bookingNumber = $"RN-2026-{seqNum}-{Guid.NewGuid().ToString("N")[..4].ToUpperInvariant()}";

                string nowIso = FormatIso(referenceNow);

                using (var insCmd = conn.CreateCommand())
                {
                    insCmd.Transaction = tx;
                    insCmd.CommandText = """
                        INSERT INTO bookings (
                            id, booking_number, unit_id, client_user_id, tariff_id,
                            starts_at, ends_at, buffer_ends_at, status, purpose, rejection_reason,
                            billed_units, unit_rate_minor, base_price_minor, deposit_minor,
                            late_hours, late_fee_minor, total_price_minor,
                            actual_issued_at, actual_returned_at, created_at, updated_at, version
                        ) VALUES (
                            $id, $number, $unitId, $clientId, $tariffId,
                            $startsAt, $endsAt, $bufferEndsAt, 'PENDING', $purpose, NULL,
                            $billedUnits, $unitRate, $basePrice, $deposit,
                            0, 0, $totalPrice,
                            NULL, NULL, $now, $now, 1
                        );
                        """;
                    insCmd.Parameters.AddWithValue("$id", bookingId);
                    insCmd.Parameters.AddWithValue("$number", bookingNumber);
                    insCmd.Parameters.AddWithValue("$unitId", unit.Id);
                    insCmd.Parameters.AddWithValue("$clientId", clientUserId);
                    insCmd.Parameters.AddWithValue("$tariffId", tariff.Id);
                    insCmd.Parameters.AddWithValue("$startsAt", FormatIso(price.StartsAt));
                    insCmd.Parameters.AddWithValue("$endsAt", FormatIso(price.EndsAt));
                    insCmd.Parameters.AddWithValue("$bufferEndsAt", FormatIso(price.BufferEndsAt));
                    insCmd.Parameters.AddWithValue("$purpose", trimmedPurpose);
                    insCmd.Parameters.AddWithValue("$billedUnits", price.BilledUnits);
                    insCmd.Parameters.AddWithValue("$unitRate", price.UnitRateMinor);
                    insCmd.Parameters.AddWithValue("$basePrice", price.BasePriceMinor);
                    insCmd.Parameters.AddWithValue("$deposit", price.DepositMinor);
                    insCmd.Parameters.AddWithValue("$totalPrice", price.TotalPriceMinor);
                    insCmd.Parameters.AddWithValue("$now", nowIso);
                    insCmd.ExecuteNonQuery();
                }

                InsertEventInternal(conn, tx, bookingId, clientUserId, "CREATED", null, "PENDING",
                    nowIso, $"Створено заявку на екземпляр {unit.InventoryCode} ({price.BilledUnits} од. тарифікації).", 0);

                tx.Commit();
                return GetBookingByIdInternal(conn, null, bookingId)!;
            }
            catch
            {
                tx.Rollback();
                throw;
            }
        }
    }

    public Booking ConfirmBookingAtomic(string bookingId, string managerUserId, string notes, DateTimeOffset now)
    {
        lock (WriteLock)
        {
            using var conn = OpenConnection();
            using var tx = conn.BeginTransaction();
            try
            {
                var booking = GetBookingByIdInternal(conn, tx, bookingId)
                    ?? throw new DomainRuleException("BOOKING_NOT_FOUND", "Бронювання не знайдено.", 404);

                PricingAndAvailabilityRules.ValidateStatusTransition(booking.Status, BookingStatus.CONFIRMED, UserRole.MANAGER, false);

                string nowIso = FormatIso(now);
                using (var cmd = conn.CreateCommand())
                {
                    cmd.Transaction = tx;
                    cmd.CommandText = """
                        UPDATE bookings
                        SET status = 'CONFIRMED', updated_at = $now, version = version + 1
                        WHERE id = $id AND version = $version;
                        """;
                    cmd.Parameters.AddWithValue("$now", nowIso);
                    cmd.Parameters.AddWithValue("$id", booking.Id);
                    cmd.Parameters.AddWithValue("$version", booking.Version);
                    if (cmd.ExecuteNonQuery() == 0)
                        throw new DomainRuleException("CONCURRENT_MODIFICATION", "Запис було змінено іншим користувачем. Оновіть дані.", 409);
                }

                InsertEventInternal(conn, tx, booking.Id, managerUserId, "CONFIRMED",
                    booking.Status.ToString(), "CONFIRMED", nowIso,
                    string.IsNullOrWhiteSpace(notes) ? "Заявку погоджено менеджером" : notes.Trim(), 0);

                tx.Commit();
                return GetBookingByIdInternal(conn, null, bookingId)!;
            }
            catch
            {
                tx.Rollback();
                throw;
            }
        }
    }

    public Booking RejectBookingAtomic(string bookingId, string managerUserId, string rejectionReason, DateTimeOffset now)
    {
        string trimmedReason = (rejectionReason ?? "").Trim();
        if (trimmedReason.Length < 5)
            throw new DomainRuleException("REJECTION_REASON_REQUIRED", "При відхиленні заявки обов’язково вкажіть причину (щонайменше 5 символів).", 400);

        lock (WriteLock)
        {
            using var conn = OpenConnection();
            using var tx = conn.BeginTransaction();
            try
            {
                var booking = GetBookingByIdInternal(conn, tx, bookingId)
                    ?? throw new DomainRuleException("BOOKING_NOT_FOUND", "Бронювання не знайдено.", 404);

                PricingAndAvailabilityRules.ValidateStatusTransition(booking.Status, BookingStatus.REJECTED, UserRole.MANAGER, false);

                string nowIso = FormatIso(now);
                using (var cmd = conn.CreateCommand())
                {
                    cmd.Transaction = tx;
                    cmd.CommandText = """
                        UPDATE bookings
                        SET status = 'REJECTED', rejection_reason = $reason, updated_at = $now, version = version + 1
                        WHERE id = $id AND version = $version;
                        """;
                    cmd.Parameters.AddWithValue("$reason", trimmedReason);
                    cmd.Parameters.AddWithValue("$now", nowIso);
                    cmd.Parameters.AddWithValue("$id", booking.Id);
                    cmd.Parameters.AddWithValue("$version", booking.Version);
                    if (cmd.ExecuteNonQuery() == 0)
                        throw new DomainRuleException("CONCURRENT_MODIFICATION", "Конфлікт версій при оновленні заявки.", 409);
                }

                InsertEventInternal(conn, tx, booking.Id, managerUserId, "REJECTED",
                    booking.Status.ToString(), "REJECTED", nowIso, $"Відхилено: {trimmedReason}", 0);

                NotifyWaitlistCandidatesInternal(conn, tx, booking.EquipmentTypeId!, booking.StartsAt, booking.BufferEndsAt, nowIso);

                tx.Commit();
                return GetBookingByIdInternal(conn, null, bookingId)!;
            }
            catch
            {
                tx.Rollback();
                throw;
            }
        }
    }

    public Booking CancelBookingAtomic(string bookingId, User actor, string reason, DateTimeOffset now)
    {
        lock (WriteLock)
        {
            using var conn = OpenConnection();
            using var tx = conn.BeginTransaction();
            try
            {
                var booking = GetBookingByIdInternal(conn, tx, bookingId)
                    ?? throw new DomainRuleException("BOOKING_NOT_FOUND", "Бронювання не знайдено.", 404);

                bool isOwner = string.Equals(booking.ClientUserId, actor.Id, StringComparison.OrdinalIgnoreCase);
                if (actor.Role == UserRole.CLIENT && !isOwner)
                    throw new DomainRuleException("FORBIDDEN_NOT_OWNER", "Ви не маєте права скасовувати чуже бронювання.", 403);

                PricingAndAvailabilityRules.ValidateStatusTransition(booking.Status, BookingStatus.CANCELLED, actor.Role, isOwner);

                string nowIso = FormatIso(now);
                using (var cmd = conn.CreateCommand())
                {
                    cmd.Transaction = tx;
                    cmd.CommandText = """
                        UPDATE bookings
                        SET status = 'CANCELLED', updated_at = $now, version = version + 1
                        WHERE id = $id AND version = $version;
                        """;
                    cmd.Parameters.AddWithValue("$now", nowIso);
                    cmd.Parameters.AddWithValue("$id", booking.Id);
                    cmd.Parameters.AddWithValue("$version", booking.Version);
                    if (cmd.ExecuteNonQuery() == 0)
                        throw new DomainRuleException("CONCURRENT_MODIFICATION", "Конфлікт версій при скасуванні заявки.", 409);
                }

                InsertEventInternal(conn, tx, booking.Id, actor.Id, "CANCELLED",
                    booking.Status.ToString(), "CANCELLED", nowIso,
                    string.IsNullOrWhiteSpace(reason) ? "Бронювання скасовано" : reason.Trim(), 0);

                NotifyWaitlistCandidatesInternal(conn, tx, booking.EquipmentTypeId!, booking.StartsAt, booking.BufferEndsAt, nowIso);

                tx.Commit();
                return GetBookingByIdInternal(conn, null, bookingId)!;
            }
            catch
            {
                tx.Rollback();
                throw;
            }
        }
    }

    public Booking IssueEquipmentAtomic(string bookingId, string managerUserId, string inspectionNotes, DateTimeOffset issuedAt)
    {
        lock (WriteLock)
        {
            using var conn = OpenConnection();
            using var tx = conn.BeginTransaction();
            try
            {
                var booking = GetBookingByIdInternal(conn, tx, bookingId)
                    ?? throw new DomainRuleException("BOOKING_NOT_FOUND", "Бронювання не знайдено.", 404);

                PricingAndAvailabilityRules.ValidateStatusTransition(booking.Status, BookingStatus.ISSUED, UserRole.MANAGER, false);

                string issuedIso = FormatIso(issuedAt);
                using (var cmd = conn.CreateCommand())
                {
                    cmd.Transaction = tx;
                    cmd.CommandText = """
                        UPDATE bookings
                        SET status = 'ISSUED', actual_issued_at = $issuedAt, updated_at = $issuedAt, version = version + 1
                        WHERE id = $id AND version = $version;
                        """;
                    cmd.Parameters.AddWithValue("$issuedAt", issuedIso);
                    cmd.Parameters.AddWithValue("$id", booking.Id);
                    cmd.Parameters.AddWithValue("$version", booking.Version);
                    if (cmd.ExecuteNonQuery() == 0)
                        throw new DomainRuleException("CONCURRENT_MODIFICATION", "Конфлікт версій при оформленні видачі.", 409);
                }

                InsertEventInternal(conn, tx, booking.Id, managerUserId, "ISSUED",
                    booking.Status.ToString(), "ISSUED", issuedIso,
                    string.IsNullOrWhiteSpace(inspectionNotes) ? "Фізичний екземпляр видано клієнтові" : inspectionNotes.Trim(), 0);

                tx.Commit();
                return GetBookingByIdInternal(conn, null, bookingId)!;
            }
            catch
            {
                tx.Rollback();
                throw;
            }
        }
    }

    public Booking ReturnEquipmentAtomic(string bookingId, string managerUserId, string inspectionNotes, DateTimeOffset actualReturnedAt)
    {
        lock (WriteLock)
        {
            using var conn = OpenConnection();
            using var tx = conn.BeginTransaction();
            try
            {
                var booking = GetBookingByIdInternal(conn, tx, bookingId)
                    ?? throw new DomainRuleException("BOOKING_NOT_FOUND", "Бронювання не знайдено.", 404);

                PricingAndAvailabilityRules.ValidateStatusTransition(booking.Status, BookingStatus.RETURNED, UserRole.MANAGER, false);

                var tariff = GetTariffByIdInternal(conn, tx, booking.TariffId)!;
                var (lateHours, lateFeeMinor) = PricingAndAvailabilityRules.CalculateLateReturnPenalty(
                    booking.EndsAt, actualReturnedAt, tariff.LateFeePerHourMinor);

                long newTotalMinor = checked(booking.BasePriceMinor + lateFeeMinor);
                string returnedIso = FormatIso(actualReturnedAt);

                using (var cmd = conn.CreateCommand())
                {
                    cmd.Transaction = tx;
                    cmd.CommandText = """
                        UPDATE bookings
                        SET status = 'RETURNED',
                            actual_returned_at = $returnedAt,
                            late_hours = $lateHours,
                            late_fee_minor = $lateFee,
                            total_price_minor = $totalPrice,
                            updated_at = $returnedAt,
                            version = version + 1
                        WHERE id = $id AND version = $version;
                        """;
                    cmd.Parameters.AddWithValue("$returnedAt", returnedIso);
                    cmd.Parameters.AddWithValue("$lateHours", lateHours);
                    cmd.Parameters.AddWithValue("$lateFee", lateFeeMinor);
                    cmd.Parameters.AddWithValue("$totalPrice", newTotalMinor);
                    cmd.Parameters.AddWithValue("$id", booking.Id);
                    cmd.Parameters.AddWithValue("$version", booking.Version);
                    if (cmd.ExecuteNonQuery() == 0)
                        throw new DomainRuleException("CONCURRENT_MODIFICATION", "Конфлікт версій при оформленні повернення.", 409);
                }

                string evtType = lateHours > 0 ? "RETURNED_LATE" : "RETURNED_ON_TIME";
                string notePrefix = lateHours > 0
                    ? $"Повернуто із запізненням ({lateHours} год.), нараховано пеню {Money.FormatUah(lateFeeMinor)}. "
                    : "Повернуто вчасно без прострочення. ";

                InsertEventInternal(conn, tx, booking.Id, managerUserId, evtType,
                    booking.Status.ToString(), "RETURNED", returnedIso,
                    notePrefix + (inspectionNotes ?? "").Trim(), lateFeeMinor);

                tx.Commit();
                return GetBookingByIdInternal(conn, null, bookingId)!;
            }
            catch
            {
                tx.Rollback();
                throw;
            }
        }
    }

    public Booking ExtendBookingAtomic(string bookingId, User actor, DateTimeOffset newEndsAt, DateTimeOffset now)
    {
        lock (WriteLock)
        {
            using var conn = OpenConnection();
            using var tx = conn.BeginTransaction();
            try
            {
                var booking = GetBookingByIdInternal(conn, tx, bookingId)
                    ?? throw new DomainRuleException("BOOKING_NOT_FOUND", "Бронювання не знайдено.", 404);

                bool isOwner = string.Equals(booking.ClientUserId, actor.Id, StringComparison.OrdinalIgnoreCase);
                if (actor.Role == UserRole.CLIENT && !isOwner)
                    throw new DomainRuleException("FORBIDDEN_NOT_OWNER", "Ви не маєте права продовжувати чуже бронювання.", 403);

                if (!booking.IsActiveInCalendar())
                    throw new DomainRuleException("INVALID_STATE_FOR_EXTENSION",
                        $"Продовження можливе лише для активних бронювань (поточний стан: {booking.Status}).", 409);

                if (newEndsAt <= booking.EndsAt)
                    throw new DomainRuleException("EXTENSION_MUST_BE_LATER",
                        "Нова дата завершення повинна бути пізнішою за поточну дату завершення бронювання.", 400);

                var unit = GetEquipmentUnitByIdInternal(conn, tx, booking.UnitId)!;
                var eqType = GetEquipmentTypeByIdInternal(conn, tx, unit.EquipmentTypeId)!;
                var tariff = eqType.Tariff!;

                var activeBookings = GetActiveBookingsForUnitInternal(conn, tx, unit.Id);
                var check = PricingAndAvailabilityRules.ValidateAndCheckAvailability(
                    eqType, unit, tariff, booking.StartsAt, newEndsAt, now, activeBookings, ignoreBookingId: booking.Id);

                if (!check.IsAvailable)
                {
                    int status = check.ErrorCode == "INTERVAL_CONFLICT" ? 409 : 400;
                    throw new DomainRuleException(check.ErrorCode ?? "EXTENSION_CONFLICT",
                        check.ErrorMessage ?? "Неможливо продовжити оренду через накладання в календарі.", status);
                }

                var newCalc = PricingAndAvailabilityRules.CalculatePrice(
                    booking.StartsAt, newEndsAt, tariff, eqType.MaintenanceBufferHours);

                string nowIso = FormatIso(now);
                using (var cmd = conn.CreateCommand())
                {
                    cmd.Transaction = tx;
                    cmd.CommandText = """
                        UPDATE bookings
                        SET ends_at = $endsAt,
                            buffer_ends_at = $bufferEndsAt,
                            billed_units = $billedUnits,
                            base_price_minor = $basePrice,
                            total_price_minor = $totalPrice,
                            updated_at = $now,
                            version = version + 1
                        WHERE id = $id AND version = $version;
                        """;
                    cmd.Parameters.AddWithValue("$endsAt", FormatIso(newCalc.EndsAt));
                    cmd.Parameters.AddWithValue("$bufferEndsAt", FormatIso(newCalc.BufferEndsAt));
                    cmd.Parameters.AddWithValue("$billedUnits", newCalc.BilledUnits);
                    cmd.Parameters.AddWithValue("$basePrice", newCalc.BasePriceMinor);
                    cmd.Parameters.AddWithValue("$totalPrice", newCalc.TotalPriceMinor + booking.LateFeeMinor);
                    cmd.Parameters.AddWithValue("$now", nowIso);
                    cmd.Parameters.AddWithValue("$id", booking.Id);
                    cmd.Parameters.AddWithValue("$version", booking.Version);
                    if (cmd.ExecuteNonQuery() == 0)
                        throw new DomainRuleException("CONCURRENT_MODIFICATION", "Конфлікт версій при продовженні оренди.", 409);
                }

                InsertEventInternal(conn, tx, booking.Id, actor.Id, "EXTENDED",
                    booking.Status.ToString(), booking.Status.ToString(), nowIso,
                    $"Продовжено до {newCalc.EndsAt:dd.MM.yyyy HH:mm} (нова кількість одиниць: {newCalc.BilledUnits}, сума: {Money.FormatUah(newCalc.BasePriceMinor)}).", 0);

                tx.Commit();
                return GetBookingByIdInternal(conn, null, bookingId)!;
            }
            catch
            {
                tx.Rollback();
                throw;
            }
        }
    }

    private static void InsertEventInternal(
        SqliteConnection conn,
        SqliteTransaction tx,
        string bookingId,
        string actorUserId,
        string eventType,
        string? oldStatus,
        string newStatus,
        string occurredAtIso,
        string notes,
        long penaltyMinor)
    {
        using var cmd = conn.CreateCommand();
        cmd.Transaction = tx;
        cmd.CommandText = """
            INSERT INTO rental_events (
                id, booking_id, actor_user_id, event_type, old_status, new_status, occurred_at, notes, penalty_added_minor
            ) VALUES (
                $id, $bookingId, $actorId, $eventType, $oldStatus, $newStatus, $occurredAt, $notes, $penalty
            );
            """;
        cmd.Parameters.AddWithValue("$id", "evt-" + Guid.NewGuid().ToString("N")[..10]);
        cmd.Parameters.AddWithValue("$bookingId", bookingId);
        cmd.Parameters.AddWithValue("$actorId", actorUserId);
        cmd.Parameters.AddWithValue("$eventType", eventType);
        cmd.Parameters.AddWithValue("$oldStatus", (object?)oldStatus ?? DBNull.Value);
        cmd.Parameters.AddWithValue("$newStatus", newStatus);
        cmd.Parameters.AddWithValue("$occurredAt", occurredAtIso);
        cmd.Parameters.AddWithValue("$notes", notes);
        cmd.Parameters.AddWithValue("$penalty", penaltyMinor);
        cmd.ExecuteNonQuery();
    }

    private static void NotifyWaitlistCandidatesInternal(
        SqliteConnection conn,
        SqliteTransaction tx,
        string equipmentTypeId,
        DateTimeOffset freedStart,
        DateTimeOffset freedEndWithBuffer,
        string nowIso)
    {
        using var cmd = conn.CreateCommand();
        cmd.Transaction = tx;
        cmd.CommandText = """
            UPDATE waitlist_entries
            SET status = 'NOTIFIED', notified_at = $now
            WHERE id = (
                SELECT id FROM waitlist_entries
                WHERE equipment_type_id = $typeId
                  AND status = 'WAITING'
                  AND desired_starts_at < $freedEnd
                  AND desired_ends_at > $freedStart
                ORDER BY created_at ASC
                LIMIT 1
            );
            """;
        cmd.Parameters.AddWithValue("$now", nowIso);
        cmd.Parameters.AddWithValue("$typeId", equipmentTypeId);
        cmd.Parameters.AddWithValue("$freedStart", FormatIso(freedStart));
        cmd.Parameters.AddWithValue("$freedEnd", FormatIso(freedEndWithBuffer));
        cmd.ExecuteNonQuery();
    }

    public WaitlistEntry AddWaitlistEntry(
        string clientUserId,
        string equipmentTypeId,
        string? preferredUnitId,
        DateTimeOffset desiredStartsAt,
        DateTimeOffset desiredEndsAt,
        string contactNote,
        DateTimeOffset now)
    {
        if (desiredEndsAt <= desiredStartsAt)
            throw new DomainRuleException("END_BEFORE_START", "Бажана дата завершення в черзі очікування має бути пізнішою за дату початку.", 400);

        string trimmedNote = (contactNote ?? "").Trim();
        if (trimmedNote.Length < 3 || trimmedNote.Length > 250)
            throw new DomainRuleException("INVALID_NOTE", "Примітка для черги очікування має містити від 3 до 250 символів.", 400);

        lock (WriteLock)
        {
            using var conn = OpenConnection();
            var eqType = GetEquipmentTypeByIdInternal(conn, null, equipmentTypeId)
                ?? throw new DomainRuleException("EQUIPMENT_NOT_FOUND", "Тип обладнання не знайдено.", 404);

            string id = "wlt-" + Guid.NewGuid().ToString("N")[..10];
            string nowIso = FormatIso(now);

            using var cmd = conn.CreateCommand();
            cmd.CommandText = """
                INSERT INTO waitlist_entries (
                    id, equipment_type_id, preferred_unit_id, client_user_id,
                    desired_starts_at, desired_ends_at, status, contact_note, notified_at, created_at
                ) VALUES (
                    $id, $typeId, $unitId, $clientId,
                    $startsAt, $endsAt, 'WAITING', $note, NULL, $now
                );
                """;
            cmd.Parameters.AddWithValue("$id", id);
            cmd.Parameters.AddWithValue("$typeId", eqType.Id);
            cmd.Parameters.AddWithValue("$unitId", (object?)preferredUnitId ?? DBNull.Value);
            cmd.Parameters.AddWithValue("$clientId", clientUserId);
            cmd.Parameters.AddWithValue("$startsAt", FormatIso(desiredStartsAt));
            cmd.Parameters.AddWithValue("$endsAt", FormatIso(desiredEndsAt));
            cmd.Parameters.AddWithValue("$note", trimmedNote);
            cmd.Parameters.AddWithValue("$now", nowIso);
            cmd.ExecuteNonQuery();

            return GetWaitlistEntries().First(w => w.Id == id);
        }
    }

    public IReadOnlyList<WaitlistEntry> GetWaitlistEntries(string? clientUserId = null)
    {
        using var conn = OpenConnection();
        using var cmd = conn.CreateCommand();
        var sql = """
            SELECT w.id, w.equipment_type_id, et.title, w.preferred_unit_id, u.inventory_code,
                   w.client_user_id, usr.full_name, w.desired_starts_at, w.desired_ends_at,
                   w.status, w.contact_note, w.notified_at, w.created_at
            FROM waitlist_entries w
            JOIN equipment_types et ON et.id = w.equipment_type_id
            LEFT JOIN equipment_units u ON u.id = w.preferred_unit_id
            JOIN users usr ON usr.id = w.client_user_id
            WHERE 1=1
            """;
        if (!string.IsNullOrWhiteSpace(clientUserId))
        {
            sql += " AND w.client_user_id = $clientId";
            cmd.Parameters.AddWithValue("$clientId", clientUserId);
        }
        sql += " ORDER BY w.created_at DESC;";
        cmd.CommandText = sql;

        using var r = cmd.ExecuteReader();
        var list = new List<WaitlistEntry>();
        while (r.Read())
        {
            list.Add(new WaitlistEntry
            {
                Id = r.GetString(0),
                EquipmentTypeId = r.GetString(1),
                EquipmentTitle = r.GetString(2),
                PreferredUnitId = r.IsDBNull(3) ? null : r.GetString(3),
                PreferredInventoryCode = r.IsDBNull(4) ? null : r.GetString(4),
                ClientUserId = r.GetString(5),
                ClientName = r.GetString(6),
                DesiredStartsAt = ParseIso(r.GetString(7)),
                DesiredEndsAt = ParseIso(r.GetString(8)),
                Status = Enum.Parse<WaitlistStatus>(r.GetString(9), true),
                ContactNote = r.GetString(10),
                NotifiedAt = r.IsDBNull(11) ? null : ParseIso(r.GetString(11)),
                CreatedAt = ParseIso(r.GetString(12))
            });
        }
        return list;
    }

    public WaitlistEntry CancelWaitlistEntry(string waitlistId, User actor)
    {
        lock (WriteLock)
        {
            using var conn = OpenConnection();
            var existing = GetWaitlistEntries().FirstOrDefault(w => w.Id == waitlistId)
                ?? throw new DomainRuleException("WAITLIST_NOT_FOUND", "Запис черги очікування не знайдено.", 404);

            if (actor.Role == UserRole.CLIENT && !string.Equals(existing.ClientUserId, actor.Id, StringComparison.OrdinalIgnoreCase))
                throw new DomainRuleException("FORBIDDEN_NOT_OWNER", "Ви не маєте права змінювати чужий запис у черзі очікування.", 403);

            using var cmd = conn.CreateCommand();
            cmd.CommandText = "UPDATE waitlist_entries SET status = 'CANCELLED' WHERE id = $id;";
            cmd.Parameters.AddWithValue("$id", waitlistId);
            cmd.ExecuteNonQuery();

            return GetWaitlistEntries().First(w => w.Id == waitlistId);
        }
    }
}
