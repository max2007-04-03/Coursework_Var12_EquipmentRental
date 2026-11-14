using System.Globalization;
using EquipmentRental.Domain;

namespace EquipmentRental.Application;

/// <summary>
/// Прикладний сервіс координації сценаріїв каталогу, календаря доступності,
/// бронювання екземплярів, видачі/повернення та черги очікування.
/// </summary>
public sealed class RentalApplicationService
{
    private readonly IRentalRepository _repo;

    // Фіксований опорний час демонстраційного стенда (2026-11-14 09:00 UTC) для відтворюваних тестів
    public static readonly DateTimeOffset DefaultDemoNow =
        DateTimeOffset.Parse("2026-11-14T09:00:00Z", CultureInfo.InvariantCulture);

    public RentalApplicationService(IRentalRepository repo)
    {
        _repo = repo;
    }

    public static UserDto MapUser(User u) => new(
        u.Id,
        u.Email,
        u.FullName,
        u.Phone,
        u.Role.ToString()
    );

    public static TariffDto MapTariff(Tariff t) => new(
        t.Id,
        t.Code,
        t.Name,
        t.BillingUnit.ToString(),
        t.RateMinor,
        Money.FormatUah(t.RateMinor),
        t.DepositMinor,
        Money.FormatUah(t.DepositMinor),
        t.LateFeePerHourMinor,
        Money.FormatUah(t.LateFeePerHourMinor),
        t.MinUnits,
        t.MaxUnits
    );

    public static BookingResponseDto MapBooking(Booking b, IReadOnlyList<RentalEvent>? events = null) => new(
        b.Id,
        b.BookingNumber,
        b.UnitId,
        b.InventoryCode ?? b.UnitId,
        b.EquipmentTypeId ?? "",
        b.EquipmentTitle ?? "",
        b.ClientUserId,
        b.ClientName ?? "",
        b.ClientEmail ?? "",
        b.TariffId,
        b.BillingUnitName ?? "DAY",
        b.StartsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
        b.EndsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
        b.BufferEndsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
        b.Status.ToString(),
        b.Purpose,
        b.RejectionReason,
        b.BilledUnits,
        b.UnitRateMinor,
        Money.FormatUah(b.UnitRateMinor),
        b.BasePriceMinor,
        Money.FormatUah(b.BasePriceMinor),
        b.DepositMinor,
        Money.FormatUah(b.DepositMinor),
        b.LateHours,
        b.LateFeeMinor,
        Money.FormatUah(b.LateFeeMinor),
        b.TotalPriceMinor,
        Money.FormatUah(b.TotalPriceMinor),
        b.ActualIssuedAt?.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
        b.ActualReturnedAt?.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
        b.CreatedAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
        b.Version,
        events?.Select(e => new RentalEventDto(
            e.Id,
            e.BookingId,
            e.ActorUserId,
            e.ActorName,
            e.EventType,
            e.OldStatus,
            e.NewStatus,
            e.OccurredAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
            e.Notes,
            e.PenaltyAddedMinor,
            Money.FormatUah(e.PenaltyAddedMinor)
        )).ToList()
    );

    public IReadOnlyList<EquipmentTypeDto> GetCatalog(
        string? search,
        string? category,
        string? billingUnit,
        DateTimeOffset? availableFrom,
        DateTimeOffset? availableTo)
    {
        if (availableFrom.HasValue && availableTo.HasValue && availableTo.Value <= availableFrom.Value)
        {
            throw new DomainRuleException("END_BEFORE_START",
                "У фільтрі періоду дата завершення має бути пізнішою за дату початку.", 400);
        }

        var types = _repo.GetEquipmentCatalog(search, category, billingUnit, availableFrom, availableTo);
        var result = new List<EquipmentTypeDto>(types.Count);

        foreach (var eq in types)
        {
            var tariff = eq.Tariff ?? _repo.GetTariffById(eq.TariffId)!;
            var unitDtos = new List<EquipmentUnitDto>(eq.Units.Count);
            int availableCount = 0;

            foreach (var u in eq.Units)
            {
                bool isAvail = u.ConditionStatus == UnitConditionStatus.AVAILABLE;
                if (isAvail && availableFrom.HasValue && availableTo.HasValue)
                {
                    var activeBookings = _repo.GetActiveBookingsForUnit(u.Id);
                    var check = PricingAndAvailabilityRules.ValidateAndCheckAvailability(
                        eq, u, tariff, availableFrom.Value, availableTo.Value,
                        availableFrom.Value.AddMinutes(-10), activeBookings);
                    isAvail = check.IsAvailable;
                }

                if (isAvail) availableCount++;

                unitDtos.Add(new EquipmentUnitDto(
                    u.Id,
                    u.EquipmentTypeId,
                    u.InventoryCode,
                    u.SerialNumber,
                    u.ConditionStatus.ToString(),
                    u.WarehouseLocation,
                    u.Notes,
                    isAvail
                ));
            }

            result.Add(new EquipmentTypeDto(
                eq.Id,
                eq.Slug,
                eq.Title,
                eq.Category,
                eq.BrandModel,
                eq.Description,
                eq.SpecsJson,
                eq.MaintenanceBufferHours,
                eq.Active,
                eq.ImageTag,
                MapTariff(tariff),
                unitDtos,
                eq.Units.Count,
                availableCount
            ));
        }

        return result;
    }

    public AvailabilityPreviewResponseDto PreviewAvailabilityAndPrice(
        string unitId,
        DateTimeOffset startsAt,
        DateTimeOffset endsAt,
        DateTimeOffset referenceNow)
    {
        var unit = _repo.GetEquipmentUnitById(unitId)
            ?? throw new DomainRuleException("UNIT_NOT_FOUND", $"Фізичний екземпляр «{unitId}» не знайдено.", 404);

        var eqType = _repo.GetEquipmentTypeById(unit.EquipmentTypeId)
            ?? throw new DomainRuleException("EQUIPMENT_NOT_FOUND", "Тип обладнання не знайдено.", 404);

        var tariff = eqType.Tariff ?? _repo.GetTariffById(eqType.TariffId)!;

        if (endsAt <= startsAt)
        {
            return new AvailabilityPreviewResponseDto(
                false,
                "END_BEFORE_START",
                "Дата завершення оренди повинна бути пізнішою за дату початку.",
                unit.Id,
                unit.InventoryCode,
                0,
                tariff.BillingUnit.ToString(),
                tariff.RateMinor,
                Money.FormatUah(tariff.RateMinor),
                0, Money.FormatUah(0),
                tariff.DepositMinor, Money.FormatUah(tariff.DepositMinor),
                0, Money.FormatUah(0),
                startsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
                endsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
                endsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
                eqType.MaintenanceBufferHours,
                null
            );
        }

        var calc = PricingAndAvailabilityRules.CalculatePrice(startsAt, endsAt, tariff, eqType.MaintenanceBufferHours);
        var activeBookings = _repo.GetActiveBookingsForUnit(unit.Id);
        var check = PricingAndAvailabilityRules.ValidateAndCheckAvailability(
            eqType, unit, tariff, startsAt, endsAt, referenceNow, activeBookings);

        return new AvailabilityPreviewResponseDto(
            check.IsAvailable,
            check.ErrorCode,
            check.ErrorMessage,
            unit.Id,
            unit.InventoryCode,
            calc.BilledUnits,
            calc.BillingUnit.ToString(),
            calc.UnitRateMinor,
            Money.FormatUah(calc.UnitRateMinor),
            calc.BasePriceMinor,
            Money.FormatUah(calc.BasePriceMinor),
            calc.DepositMinor,
            Money.FormatUah(calc.DepositMinor),
            calc.TotalPriceMinor,
            Money.FormatUah(calc.TotalPriceMinor),
            calc.StartsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
            calc.EndsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
            calc.BufferEndsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
            calc.MaintenanceBufferHours,
            check.ConflictingBooking?.BookingNumber
        );
    }

    public IReadOnlyList<CalendarSlotItemDto> GetEquipmentCalendar(
        string equipmentTypeId,
        DateTimeOffset from,
        DateTimeOffset to)
    {
        if (to <= from)
            throw new DomainRuleException("END_BEFORE_START", "Кінець періоду календаря має бути пізнішим за початок.", 400);

        var eq = _repo.GetEquipmentTypeById(equipmentTypeId)
            ?? throw new DomainRuleException("EQUIPMENT_NOT_FOUND", "Тип обладнання не знайдено.", 404);

        var bookings = _repo.GetBookingsForTypeInPeriod(equipmentTypeId, from, to);
        return bookings.Select(b => new CalendarSlotItemDto(
            b.Id,
            b.BookingNumber,
            b.UnitId,
            b.InventoryCode ?? b.UnitId,
            b.Status.ToString(),
            b.StartsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
            b.EndsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
            b.BufferEndsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
            eq.MaintenanceBufferHours,
            b.Status == BookingStatus.ISSUED ? "Видано в оренду" :
            b.Status == BookingStatus.CONFIRMED ? "Підтверджене бронювання" : "Очікує погодження"
        )).ToList();
    }
}
