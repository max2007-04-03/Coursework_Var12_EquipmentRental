namespace EquipmentRental.Domain;

/// <summary>
/// Результат розрахунку вартості та часових меж оренди.
/// </summary>
public sealed record PriceCalculationResult(
    int BilledUnits,
    BillingUnit BillingUnit,
    long UnitRateMinor,
    long BasePriceMinor,
    long DepositMinor,
    long TotalPriceMinor,
    DateTimeOffset StartsAt,
    DateTimeOffset EndsAt,
    DateTimeOffset BufferEndsAt,
    int MaintenanceBufferHours
);

/// <summary>
/// Результат перевірки перетину інтервалів.
/// </summary>
public sealed record AvailabilityCheckResult(
    bool IsAvailable,
    string? ErrorCode,
    string? ErrorMessage,
    Booking? ConflictingBooking
);

/// <summary>
/// Доменні алгоритми перевірки доступності фізичного екземпляра,
/// розрахунку вартості оренди, технічних перерв, продовження та пені за прострочення.
/// </summary>
public static class PricingAndAvailabilityRules
{
    /// <summary>
    /// Перевіряє, чи перетинаються два напіввідкриті інтервали [startA, endA) та [startB, endB).
    /// Межа початку включена, межа завершення (разом із технічною перервою) не включена:
    /// якщо перша оренда разом із тех. перервою завершується о 13:00, наступна може початися рівно о 13:00.
    /// </summary>
    public static bool IntervalsOverlap(
        DateTimeOffset startA,
        DateTimeOffset endAWithBuffer,
        DateTimeOffset startB,
        DateTimeOffset endBWithBuffer)
    {
        return startA < endBWithBuffer && startB < endAWithBuffer;
    }

    /// <summary>
    /// Обчислює кількість одиниць тарифікації, базову вартість, заставу та межу технічної перерви.
    /// Неповна година або доба округлюється вгору на користь повної одиниці тарифікації.
    /// </summary>
    public static PriceCalculationResult CalculatePrice(
        DateTimeOffset startsAt,
        DateTimeOffset endsAt,
        Tariff tariff,
        int maintenanceBufferHours)
    {
        if (endsAt <= startsAt)
            throw new DomainRuleException("INVALID_INTERVAL", "Дата та час завершення оренди мають бути пізнішими за дату початку.");

        TimeSpan duration = endsAt - startsAt;
        double totalMinutes = duration.TotalMinutes;

        int billedUnits;
        if (tariff.BillingUnit == BillingUnit.HOUR)
        {
            billedUnits = (int)Math.Ceiling(totalMinutes / 60.0);
        }
        else
        {
            billedUnits = (int)Math.Ceiling(totalMinutes / (60.0 * 24.0));
        }

        if (billedUnits < 1) billedUnits = 1;

        long basePriceMinor = checked(billedUnits * tariff.RateMinor);
        DateTimeOffset bufferEndsAt = endsAt.AddHours(maintenanceBufferHours);

        return new PriceCalculationResult(
            BilledUnits: billedUnits,
            BillingUnit: tariff.BillingUnit,
            UnitRateMinor: tariff.RateMinor,
            BasePriceMinor: basePriceMinor,
            DepositMinor: tariff.DepositMinor,
            TotalPriceMinor: basePriceMinor,
            StartsAt: startsAt,
            EndsAt: endsAt,
            BufferEndsAt: bufferEndsAt,
            MaintenanceBufferHours: maintenanceBufferHours
        );
    }

    /// <summary>
    /// Перевіряє допустимість періоду за правилами тарифу та станом екземпляра,
    /// а також відсутність перетину з активними бронюваннями цього ж екземпляра.
    /// </summary>
    public static AvailabilityCheckResult ValidateAndCheckAvailability(
        EquipmentType equipmentType,
        EquipmentUnit unit,
        Tariff tariff,
        DateTimeOffset startsAt,
        DateTimeOffset endsAt,
        DateTimeOffset referenceNow,
        IEnumerable<Booking> existingActiveBookingsForUnit,
        string? ignoreBookingId = null)
    {
        if (!equipmentType.Active)
        {
            return new AvailabilityCheckResult(false, "EQUIPMENT_INACTIVE",
                "Обраний тип обладнання тимчасово недоступний для нових замовлень.", null);
        }

        if (unit.ConditionStatus != UnitConditionStatus.AVAILABLE)
        {
            return new AvailabilityCheckResult(false, "UNIT_NOT_AVAILABLE",
                $"Фізичний екземпляр {unit.InventoryCode} має технічний стан «{unit.ConditionStatus}» і недоступний для видачі.", null);
        }

        if (endsAt <= startsAt)
        {
            return new AvailabilityCheckResult(false, "END_BEFORE_START",
                "Дата завершення оренди повинна бути строго пізнішою за дату початку.", null);
        }

        if (startsAt < referenceNow.AddMinutes(-5) && ignoreBookingId is null)
        {
            return new AvailabilityCheckResult(false, "START_IN_PAST",
                "Неможливо створити нове бронювання на дату або час у минулому.", null);
        }

        var calc = CalculatePrice(startsAt, endsAt, tariff, equipmentType.MaintenanceBufferHours);
        string unitLabel = tariff.BillingUnit == BillingUnit.HOUR ? "год." : "діб";

        if (calc.BilledUnits < tariff.MinUnits)
        {
            return new AvailabilityCheckResult(false, "DURATION_TOO_SHORT",
                $"Мінімальна тривалість за тарифом «{tariff.Name}» становить {tariff.MinUnits} {unitLabel} (обрано: {calc.BilledUnits}).", null);
        }

        if (calc.BilledUnits > tariff.MaxUnits)
        {
            return new AvailabilityCheckResult(false, "DURATION_TOO_LONG",
                $"Максимальна тривалість за тарифом «{tariff.Name}» становить {tariff.MaxUnits} {unitLabel} (обрано: {calc.BilledUnits}).", null);
        }

        foreach (var existing in existingActiveBookingsForUnit)
        {
            if (ignoreBookingId is not null && string.Equals(existing.Id, ignoreBookingId, StringComparison.OrdinalIgnoreCase))
                continue;

            if (!existing.IsActiveInCalendar())
                continue;

            if (IntervalsOverlap(startsAt, calc.BufferEndsAt, existing.StartsAt, existing.BufferEndsAt))
            {
                return new AvailabilityCheckResult(
                    false,
                    "INTERVAL_CONFLICT",
                    $"Екземпляр {unit.InventoryCode} уже зайнятий у період з {existing.StartsAt:dd.MM.yyyy HH:mm} до {existing.EndsAt:dd.MM.yyyy HH:mm} (разом із тех. перервою до {existing.BufferEndsAt:dd.MM.yyyy HH:mm}, заявка {existing.BookingNumber}).",
                    existing);
            }
        }

        return new AvailabilityCheckResult(true, null, null, null);
    }

    /// <summary>
    /// Обчислює кількість годин прострочення та суму пені при поверненні із запізненням.
    /// Допускається нештрафований технічний допуск 10 хвилин.
    /// </summary>
    public static (int LateHours, long LateFeeMinor) CalculateLateReturnPenalty(
        DateTimeOffset plannedEndsAt,
        DateTimeOffset actualReturnedAt,
        long lateFeePerHourMinor)
    {
        TimeSpan diff = actualReturnedAt - plannedEndsAt;
        if (diff.TotalMinutes <= 10.0)
            return (0, 0L);

        int lateHours = (int)Math.Ceiling(diff.TotalMinutes / 60.0);
        long lateFeeMinor = checked(lateHours * lateFeePerHourMinor);
        return (lateHours, lateFeeMinor);
    }

    /// <summary>
    /// Перевіряє допустимість переходу статусу бронювання та повноваження ролі.
    /// </summary>
    public static void ValidateStatusTransition(BookingStatus current, BookingStatus target, UserRole actorRole, bool isOwner)
    {
        if (current == target)
            throw new DomainRuleException("SAME_STATUS", $"Бронювання вже перебуває у стані {current}.");

        bool allowed = (current, target, actorRole) switch
        {
            // Клієнт-власник або менеджер може скасувати PENDING або CONFIRMED заявку до її фізичної видачі
            (BookingStatus.PENDING, BookingStatus.CANCELLED, UserRole.CLIENT) => isOwner,
            (BookingStatus.CONFIRMED, BookingStatus.CANCELLED, UserRole.CLIENT) => isOwner,
            (BookingStatus.PENDING, BookingStatus.CANCELLED, UserRole.MANAGER) => true,
            (BookingStatus.CONFIRMED, BookingStatus.CANCELLED, UserRole.MANAGER) => true,

            // Лише менеджер погоджує або відхиляє нову заявку
            (BookingStatus.PENDING, BookingStatus.CONFIRMED, UserRole.MANAGER) => true,
            (BookingStatus.PENDING, BookingStatus.REJECTED, UserRole.MANAGER) => true,

            // Лише менеджер фіксує фізичну видачу підтвердженого бронювання
            (BookingStatus.CONFIRMED, BookingStatus.ISSUED, UserRole.MANAGER) => true,

            // Лише менеджер фіксує повернення виданого екземпляра
            (BookingStatus.ISSUED, BookingStatus.RETURNED, UserRole.MANAGER) => true,

            _ => false
        };

        if (!allowed)
        {
            throw new DomainRuleException(
                "INVALID_STATUS_TRANSITION",
                $"Перехід зі стану «{current}» у стан «{target}» недозволений для ролі «{actorRole}».");
        }
    }
}

public sealed class DomainRuleException : Exception
{
    public string Code { get; }
    public int SuggestedHttpStatus { get; }

    public DomainRuleException(string code, string message, int suggestedHttpStatus = 400)
        : base(message)
    {
        Code = code;
        SuggestedHttpStatus = suggestedHttpStatus;
    }
}
