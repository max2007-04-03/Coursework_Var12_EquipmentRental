namespace EquipmentRental.Domain;

/// <summary>
/// Контракт доступу до сховища даних системи оренди обладнання.
/// </summary>
public interface IRentalRepository
{
    void EnsureDatabaseInitialized(string initSqlPath, string seedSqlPath);

    // Користувачі
    User? GetUserByEmail(string email);
    User? GetUserById(string id);
    IReadOnlyList<User> GetAllUsers();

    // Каталог, тарифи та фізичні екземпляри
    IReadOnlyList<Tariff> GetAllTariffs();
    Tariff? GetTariffById(string id);
    IReadOnlyList<EquipmentType> GetEquipmentCatalog(
        string? search = null,
        string? category = null,
        string? billingUnit = null,
        DateTimeOffset? availableFrom = null,
        DateTimeOffset? availableTo = null);
    EquipmentType? GetEquipmentTypeById(string id);
    EquipmentUnit? GetEquipmentUnitById(string unitId);
    IReadOnlyList<EquipmentUnit> GetUnitsByTypeId(string equipmentTypeId);
    void UpdateUnitCondition(string unitId, UnitConditionStatus newStatus, string notes);

    // Календар та бронювання
    IReadOnlyList<Booking> GetActiveBookingsForUnit(string unitId);
    IReadOnlyList<Booking> GetBookingsForTypeInPeriod(string equipmentTypeId, DateTimeOffset from, DateTimeOffset to);
    IReadOnlyList<Booking> GetBookings(string? clientUserId = null, string? statusFilter = null, string? unitId = null);
    Booking? GetBookingById(string bookingId);
    IReadOnlyList<RentalEvent> GetEventsForBooking(string bookingId);

    // Атомарні транзакційні операції зі зміною стану
    Booking CreateBookingAtomic(
        string clientUserId,
        string unitId,
        DateTimeOffset startsAt,
        DateTimeOffset endsAt,
        string purpose,
        DateTimeOffset referenceNow);

    Booking ConfirmBookingAtomic(string bookingId, string managerUserId, string notes, DateTimeOffset now);
    Booking RejectBookingAtomic(string bookingId, string managerUserId, string rejectionReason, DateTimeOffset now);
    Booking CancelBookingAtomic(string bookingId, User actor, string reason, DateTimeOffset now);
    Booking IssueEquipmentAtomic(string bookingId, string managerUserId, string inspectionNotes, DateTimeOffset issuedAt);
    Booking ReturnEquipmentAtomic(string bookingId, string managerUserId, string inspectionNotes, DateTimeOffset actualReturnedAt);
    Booking ExtendBookingAtomic(string bookingId, User actor, DateTimeOffset newEndsAt, DateTimeOffset now);

    // Черга очікування (Waitlist)
    WaitlistEntry AddWaitlistEntry(
        string clientUserId,
        string equipmentTypeId,
        string? preferredUnitId,
        DateTimeOffset desiredStartsAt,
        DateTimeOffset desiredEndsAt,
        string contactNote,
        DateTimeOffset now);
    IReadOnlyList<WaitlistEntry> GetWaitlistEntries(string? clientUserId = null);
    WaitlistEntry CancelWaitlistEntry(string waitlistId, User actor);
}
