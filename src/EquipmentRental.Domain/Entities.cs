using System.Globalization;

namespace EquipmentRental.Domain;

/// <summary>
/// Ролі користувачів вебсистеми оренди обладнання.
/// </summary>
public enum UserRole
{
    CLIENT,
    MANAGER
}

/// <summary>
/// Технічний стан фізичного екземпляра обладнання.
/// </summary>
public enum UnitConditionStatus
{
    AVAILABLE,
    IN_MAINTENANCE,
    RETIRED
}

/// <summary>
/// Одиниця тарифікації оренди.
/// </summary>
public enum BillingUnit
{
    HOUR,
    DAY
}

/// <summary>
/// Статуси життєвого циклу заявки на бронювання (оренду).
/// Активними (такими, що блокують календар екземпляра) є PENDING, CONFIRMED, ISSUED.
/// </summary>
public enum BookingStatus
{
    PENDING,
    CONFIRMED,
    ISSUED,
    RETURNED,
    CANCELLED,
    REJECTED
}

/// <summary>
/// Статуси запису в черзі очікування (Waitlist).
/// </summary>
public enum WaitlistStatus
{
    WAITING,
    NOTIFIED,
    CONVERTED,
    CANCELLED
}

/// <summary>
/// Допоміжний клас точних грошових розрахунків у копійках (long) без використання float/double.
/// </summary>
public static class Money
{
    public static string FormatUah(long minorUnits)
    {
        decimal uah = minorUnits / 100m;
        return uah.ToString("N2", new CultureInfo("uk-UA")) + " грн";
    }

    public static decimal ToDecimal(long minorUnits) => minorUnits / 100m;

    public static bool TryParseUahToMinor(string? input, out long minorUnits)
    {
        minorUnits = 0;
        if (string.IsNullOrWhiteSpace(input)) return false;
        string normalized = input.Trim().Replace(" ", "").Replace(',', '.');
        if (!decimal.TryParse(normalized, NumberStyles.Number, CultureInfo.InvariantCulture, out decimal value))
            return false;
        if (value < 0 || decimal.Round(value, 2) != value)
            return false;
        minorUnits = (long)(value * 100m);
        return true;
    }
}

public sealed class User
{
    public string Id { get; init; } = "";
    public string Email { get; init; } = "";
    public string FullName { get; init; } = "";
    public string Phone { get; init; } = "";
    public UserRole Role { get; init; }
    public string PasswordHash { get; init; } = "";
    public DateTimeOffset CreatedAt { get; init; }
}

public sealed class Tariff
{
    public string Id { get; init; } = "";
    public string Code { get; init; } = "";
    public string Name { get; init; } = "";
    public BillingUnit BillingUnit { get; init; }
    public long RateMinor { get; init; }
    public long DepositMinor { get; init; }
    public long LateFeePerHourMinor { get; init; }
    public int MinUnits { get; init; }
    public int MaxUnits { get; init; }
}

public sealed class EquipmentType
{
    public string Id { get; init; } = "";
    public string Slug { get; init; } = "";
    public string Title { get; init; } = "";
    public string Category { get; init; } = "";
    public string BrandModel { get; init; } = "";
    public string Description { get; init; } = "";
    public string SpecsJson { get; init; } = "{}";
    public string TariffId { get; init; } = "";
    public int MaintenanceBufferHours { get; init; }
    public bool Active { get; init; } = true;
    public string ImageTag { get; init; } = "";
    public Tariff? Tariff { get; set; }
    public List<EquipmentUnit> Units { get; set; } = new();
}

public sealed class EquipmentUnit
{
    public string Id { get; init; } = "";
    public string EquipmentTypeId { get; init; } = "";
    public string InventoryCode { get; init; } = "";
    public string SerialNumber { get; init; } = "";
    public UnitConditionStatus ConditionStatus { get; set; }
    public string WarehouseLocation { get; set; } = "";
    public string Notes { get; set; } = "";
}

public sealed class Booking
{
    public string Id { get; init; } = "";
    public string BookingNumber { get; init; } = "";
    public string UnitId { get; init; } = "";
    public string ClientUserId { get; init; } = "";
    public string TariffId { get; init; } = "";
    public DateTimeOffset StartsAt { get; set; }
    public DateTimeOffset EndsAt { get; set; }
    public DateTimeOffset BufferEndsAt { get; set; }
    public BookingStatus Status { get; set; }
    public string Purpose { get; set; } = "";
    public string? RejectionReason { get; set; }
    public int BilledUnits { get; set; }
    public long UnitRateMinor { get; set; }
    public long BasePriceMinor { get; set; }
    public long DepositMinor { get; set; }
    public int LateHours { get; set; }
    public long LateFeeMinor { get; set; }
    public long TotalPriceMinor { get; set; }
    public DateTimeOffset? ActualIssuedAt { get; set; }
    public DateTimeOffset? ActualReturnedAt { get; set; }
    public DateTimeOffset CreatedAt { get; init; }
    public DateTimeOffset UpdatedAt { get; set; }
    public int Version { get; set; } = 1;

    // Додаткові навігаційні відомості для відображення
    public string? InventoryCode { get; set; }
    public string? EquipmentTitle { get; set; }
    public string? EquipmentTypeId { get; set; }
    public string? ClientName { get; set; }
    public string? ClientEmail { get; set; }
    public string? BillingUnitName { get; set; }

    public bool IsActiveInCalendar() =>
        Status is BookingStatus.PENDING or BookingStatus.CONFIRMED or BookingStatus.ISSUED;
}

public sealed class RentalEvent
{
    public string Id { get; init; } = "";
    public string BookingId { get; init; } = "";
    public string ActorUserId { get; init; } = "";
    public string ActorName { get; init; } = "";
    public string EventType { get; init; } = "";
    public string? OldStatus { get; init; }
    public string NewStatus { get; init; } = "";
    public DateTimeOffset OccurredAt { get; init; }
    public string Notes { get; init; } = "";
    public long PenaltyAddedMinor { get; init; }
}

public sealed class WaitlistEntry
{
    public string Id { get; init; } = "";
    public string EquipmentTypeId { get; init; } = "";
    public string? EquipmentTitle { get; set; }
    public string? PreferredUnitId { get; init; }
    public string? PreferredInventoryCode { get; set; }
    public string ClientUserId { get; init; } = "";
    public string? ClientName { get; set; }
    public DateTimeOffset DesiredStartsAt { get; init; }
    public DateTimeOffset DesiredEndsAt { get; init; }
    public WaitlistStatus Status { get; set; }
    public string ContactNote { get; init; } = "";
    public DateTimeOffset? NotifiedAt { get; set; }
    public DateTimeOffset CreatedAt { get; init; }
}
