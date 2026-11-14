using System.ComponentModel.DataAnnotations;
using EquipmentRental.Domain;

namespace EquipmentRental.Application;

public sealed record UserDto(
    string Id,
    string Email,
    string FullName,
    string Phone,
    string Role
);

public sealed record LoginRequestDto(
    [Required(ErrorMessage = "Вкажіть email облікового запису")]
    string Email,
    string? Password
);

public sealed record TariffDto(
    string Id,
    string Code,
    string Name,
    string BillingUnit,
    long RateMinor,
    string RateFormatted,
    long DepositMinor,
    string DepositFormatted,
    long LateFeePerHourMinor,
    string LateFeeFormatted,
    int MinUnits,
    int MaxUnits
);

public sealed record EquipmentUnitDto(
    string Id,
    string EquipmentTypeId,
    string InventoryCode,
    string SerialNumber,
    string ConditionStatus,
    string WarehouseLocation,
    string Notes,
    bool IsAvailableInSelectedPeriod
);

public sealed record EquipmentTypeDto(
    string Id,
    string Slug,
    string Title,
    string Category,
    string BrandModel,
    string Description,
    string SpecsJson,
    int MaintenanceBufferHours,
    bool Active,
    string ImageTag,
    TariffDto Tariff,
    IReadOnlyList<EquipmentUnitDto> Units,
    int TotalUnitsCount,
    int AvailableUnitsCount
);

public sealed record CalendarSlotItemDto(
    string BookingId,
    string BookingNumber,
    string UnitId,
    string InventoryCode,
    string Status,
    string StartsAt,
    string EndsAt,
    string BufferEndsAt,
    int MaintenanceBufferHours,
    string PurposeSummary
);

public sealed record AvailabilityPreviewRequestDto(
    string UnitId,
    string StartsAt,
    string EndsAt
);

public sealed record AvailabilityPreviewResponseDto(
    bool IsAvailable,
    string? ErrorCode,
    string? ErrorMessage,
    string UnitId,
    string InventoryCode,
    int BilledUnits,
    string BillingUnit,
    long UnitRateMinor,
    string UnitRateFormatted,
    long BasePriceMinor,
    string BasePriceFormatted,
    long DepositMinor,
    string DepositFormatted,
    long TotalPriceMinor,
    string TotalPriceFormatted,
    string StartsAt,
    string EndsAt,
    string BufferEndsAt,
    int MaintenanceBufferHours,
    string? ConflictingBookingNumber
);

public sealed record CreateBookingRequestDto(
    [Required(ErrorMessage = "Оберіть фізичний екземпляр обладнання")]
    string UnitId,
    [Required(ErrorMessage = "Вкажіть дату та час початку оренди")]
    string StartsAt,
    [Required(ErrorMessage = "Вкажіть дату та час завершення оренди")]
    string EndsAt,
    [Required(ErrorMessage = "Зазначте мету використання обладнання")]
    [StringLength(300, MinimumLength = 5, ErrorMessage = "Мета використання повинна містити від 5 до 300 символів")]
    string Purpose
);

public sealed record ExtendBookingRequestDto(
    [Required(ErrorMessage = "Вкажіть нову дату та час завершення оренди")]
    string NewEndsAt
);

public sealed record ManagerDecisionRequestDto(
    string? Notes,
    string? RejectionReason,
    string? ActualTimestamp
);

public sealed record RentalEventDto(
    string Id,
    string BookingId,
    string ActorUserId,
    string ActorName,
    string EventType,
    string? OldStatus,
    string NewStatus,
    string OccurredAt,
    string Notes,
    long PenaltyAddedMinor,
    string PenaltyAddedFormatted
);

public sealed record BookingResponseDto(
    string Id,
    string BookingNumber,
    string UnitId,
    string InventoryCode,
    string EquipmentTypeId,
    string EquipmentTitle,
    string ClientUserId,
    string ClientName,
    string ClientEmail,
    string TariffId,
    string BillingUnit,
    string StartsAt,
    string EndsAt,
    string BufferEndsAt,
    string Status,
    string Purpose,
    string? RejectionReason,
    int BilledUnits,
    long UnitRateMinor,
    string UnitRateFormatted,
    long BasePriceMinor,
    string BasePriceFormatted,
    long DepositMinor,
    string DepositFormatted,
    int LateHours,
    long LateFeeMinor,
    string LateFeeFormatted,
    long TotalPriceMinor,
    string TotalPriceFormatted,
    string? ActualIssuedAt,
    string? ActualReturnedAt,
    string CreatedAt,
    int Version,
    IReadOnlyList<RentalEventDto>? Events = null
);

public sealed record CreateWaitlistRequestDto(
    [Required(ErrorMessage = "Вкажіть тип обладнання")]
    string EquipmentTypeId,
    string? PreferredUnitId,
    [Required(ErrorMessage = "Вкажіть бажаний початок періоду")]
    string DesiredStartsAt,
    [Required(ErrorMessage = "Вкажіть бажане завершення періоду")]
    string DesiredEndsAt,
    [Required(ErrorMessage = "Вкажіть контактну примітку для сповіщення")]
    [StringLength(250, MinimumLength = 3, ErrorMessage = "Примітка має містити від 3 до 250 символів")]
    string ContactNote
);

public sealed record WaitlistEntryDto(
    string Id,
    string EquipmentTypeId,
    string EquipmentTitle,
    string? PreferredUnitId,
    string? PreferredInventoryCode,
    string ClientUserId,
    string ClientName,
    string DesiredStartsAt,
    string DesiredEndsAt,
    string Status,
    string ContactNote,
    string? NotifiedAt,
    string CreatedAt
);

public sealed record FieldErrorDto(string Field, string Message);

/// <summary>
/// Єдиний формат помилки за контрактом API (сумісний із RFC 9457 Problem Details).
/// </summary>
public sealed record ApiErrorResponse(
    string Type,
    string Title,
    int Status,
    string Detail,
    string Code,
    string TraceId,
    IReadOnlyList<FieldErrorDto>? FieldErrors = null
);
