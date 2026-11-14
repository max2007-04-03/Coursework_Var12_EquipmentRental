using System.Globalization;
using EquipmentRental.Application;
using EquipmentRental.Domain;
using EquipmentRental.Infrastructure;
using Microsoft.AspNetCore.Mvc;

namespace EquipmentRental.WebApi.Controllers;

[ApiController]
[Route("api")]
public sealed class RentalApiController : ControllerBase
{
    private readonly IRentalRepository _repo;
    private readonly RentalApplicationService _app;
    private readonly SessionAuthManager _auth;
    private readonly ILogger<RentalApiController> _logger;

    public RentalApiController(
        IRentalRepository repo,
        RentalApplicationService app,
        SessionAuthManager auth,
        ILogger<RentalApiController> logger)
    {
        _repo = repo;
        _app = app;
        _auth = auth;
        _logger = logger;
    }

    private ActionResult<T> ProblemResponse<T>(int status, string code, string title, string detail, IReadOnlyList<FieldErrorDto>? fieldErrors = null)
    {
        var err = new ApiErrorResponse(
            Type: $"https://equiprent.op.edu.ua/problems/{code.ToLowerInvariant()}",
            Title: title,
            Status: status,
            Detail: detail,
            Code: code,
            TraceId: HttpContext.TraceIdentifier,
            FieldErrors: fieldErrors
        );
        return StatusCode(status, err);
    }

    private static bool TryParseTimestamp(string? raw, out DateTimeOffset dto)
    {
        dto = default;
        if (string.IsNullOrWhiteSpace(raw)) return false;
        return DateTimeOffset.TryParse(
            raw.Trim(),
            CultureInfo.InvariantCulture,
            DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal,
            out dto);
    }

    [HttpGet("health")]
    public IActionResult GetHealth()
    {
        try
        {
            var tariffs = _repo.GetAllTariffs();
            return Ok(new
            {
                status = "UP",
                database = "CONNECTED",
                tariffsLoaded = tariffs.Count,
                serverTimeUtc = DateTimeOffset.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
                demoReferenceTimeUtc = RentalApplicationService.DefaultDemoNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Health check failed");
            return StatusCode(503, new { status = "DOWN", database = "ERROR" });
        }
    }

    // ==================== АВТЕНТИФІКАЦІЯ ТА СЕСІЇ ====================

    [HttpGet("auth/users")]
    public ActionResult<IReadOnlyList<UserDto>> GetDemoUsers()
    {
        var users = _repo.GetAllUsers().Select(RentalApplicationService.MapUser).ToList();
        return Ok(users);
    }

    [HttpGet("auth/me")]
    public ActionResult<object> GetCurrentUser()
    {
        var user = _auth.ResolveCurrentUser(HttpContext, _repo);
        if (user is null)
            return Ok(new { authenticated = false, user = (UserDto?)null });

        return Ok(new { authenticated = true, user = RentalApplicationService.MapUser(user) });
    }

    [HttpPost("auth/login")]
    public ActionResult<object> Login([FromBody] LoginRequestDto request)
    {
        if (string.IsNullOrWhiteSpace(request.Email))
            return ProblemResponse<object>(400, "INVALID_CREDENTIALS", "Помилка введення", "Вкажіть email облікового запису.");

        var user = _repo.GetUserByEmail(request.Email);
        if (user is null)
            return ProblemResponse<object>(401, "AUTH_FAILED", "Відмова автентифікації", "Обліковий запис із вказаним email не знайдено.");

        if (!string.IsNullOrWhiteSpace(request.Password) &&
            !PasswordHasher.VerifyPassword(request.Password, user.PasswordHash, user.Email))
        {
            _logger.LogWarning("Failed login attempt for {Email} [TraceId={TraceId}]", request.Email, HttpContext.TraceIdentifier);
            return ProblemResponse<object>(401, "AUTH_FAILED", "Відмова автентифікації", "Невірний пароль облікового запису.");
        }

        string token = _auth.CreateSession(user.Id);
        Response.Cookies.Append(SessionAuthManager.CookieName, token, new CookieOptions
        {
            HttpOnly = true,
            SameSite = SameSiteMode.Lax,
            Secure = Request.IsHttps,
            Expires = DateTimeOffset.UtcNow.AddHours(12),
            Path = "/"
        });

        _logger.LogInformation("User {UserId} ({Role}) logged in [TraceId={TraceId}]", user.Id, user.Role, HttpContext.TraceIdentifier);
        return Ok(new
        {
            authenticated = true,
            sessionToken = token,
            user = RentalApplicationService.MapUser(user)
        });
    }

    [HttpPost("auth/logout")]
    public IActionResult Logout()
    {
        if (Request.Cookies.TryGetValue(SessionAuthManager.CookieName, out var token) && !string.IsNullOrEmpty(token))
        {
            _auth.RemoveSession(token);
        }
        Response.Cookies.Delete(SessionAuthManager.CookieName, new CookieOptions { Path = "/" });
        return Ok(new { authenticated = false });
    }

    // ==================== КАТАЛОГ ТА КАЛЕНДАР ДОСТУПНОСТІ ====================

    [HttpGet("tariffs")]
    public ActionResult<IReadOnlyList<TariffDto>> GetTariffs()
    {
        return Ok(_repo.GetAllTariffs().Select(RentalApplicationService.MapTariff).ToList());
    }

    [HttpGet("catalog")]
    public ActionResult<IReadOnlyList<EquipmentTypeDto>> GetCatalog(
        [FromQuery] string? search = null,
        [FromQuery] string? category = null,
        [FromQuery] string? billingUnit = null,
        [FromQuery] string? availableFrom = null,
        [FromQuery] string? availableTo = null)
    {
        DateTimeOffset? fromDto = null;
        DateTimeOffset? toDto = null;

        if (!string.IsNullOrWhiteSpace(availableFrom))
        {
            if (!TryParseTimestamp(availableFrom, out var parsedFrom))
                return ProblemResponse<IReadOnlyList<EquipmentTypeDto>>(400, "INVALID_DATE", "Некоректний формат дати", "Параметр availableFrom має некоректний формат ISO-8601.");
            fromDto = parsedFrom;
        }

        if (!string.IsNullOrWhiteSpace(availableTo))
        {
            if (!TryParseTimestamp(availableTo, out var parsedTo))
                return ProblemResponse<IReadOnlyList<EquipmentTypeDto>>(400, "INVALID_DATE", "Некоректний формат дати", "Параметр availableTo має некоректний формат ISO-8601.");
            toDto = parsedTo;
        }

        try
        {
            var catalog = _app.GetCatalog(search, category, billingUnit, fromDto, toDto);
            return Ok(catalog);
        }
        catch (DomainRuleException ex)
        {
            return ProblemResponse<IReadOnlyList<EquipmentTypeDto>>(ex.SuggestedHttpStatus, ex.Code, "Помилка параметрів фільтрації", ex.Message);
        }
    }

    [HttpGet("catalog/{id}")]
    public ActionResult<EquipmentTypeDto> GetCatalogItem(string id)
    {
        var item = _app.GetCatalog(null, null, null, null, null)
            .FirstOrDefault(x => string.Equals(x.Id, id, StringComparison.OrdinalIgnoreCase) ||
                                 string.Equals(x.Slug, id, StringComparison.OrdinalIgnoreCase));
        if (item is null)
            return ProblemResponse<EquipmentTypeDto>(404, "EQUIPMENT_NOT_FOUND", "Позицію не знайдено", $"Тип обладнання «{id}» не існує в каталозі.");
        return Ok(item);
    }

    [HttpGet("catalog/{id}/calendar")]
    public ActionResult<IReadOnlyList<CalendarSlotItemDto>> GetEquipmentCalendar(
        string id,
        [FromQuery] string? from = null,
        [FromQuery] string? to = null)
    {
        var fromDate = TryParseTimestamp(from, out var f) ? f : RentalApplicationService.DefaultDemoNow.AddDays(-10);
        var toDate = TryParseTimestamp(to, out var t) ? t : RentalApplicationService.DefaultDemoNow.AddDays(20);

        try
        {
            var items = _app.GetEquipmentCalendar(id, fromDate, toDate);
            return Ok(items);
        }
        catch (DomainRuleException ex)
        {
            return ProblemResponse<IReadOnlyList<CalendarSlotItemDto>>(ex.SuggestedHttpStatus, ex.Code, "Помилка запиту календаря", ex.Message);
        }
    }

    [HttpPost("bookings/preview")]
    public ActionResult<AvailabilityPreviewResponseDto> PreviewBooking([FromBody] AvailabilityPreviewRequestDto request)
    {
        if (!TryParseTimestamp(request.StartsAt, out var startsAt) || !TryParseTimestamp(request.EndsAt, out var endsAt))
        {
            return ProblemResponse<AvailabilityPreviewResponseDto>(400, "INVALID_DATE", "Некоректні часові межі", "Вкажіть коректну дату та час початку і завершення оренди.");
        }

        try
        {
            var preview = _app.PreviewAvailabilityAndPrice(
                request.UnitId, startsAt, endsAt, RentalApplicationService.DefaultDemoNow);
            return Ok(preview);
        }
        catch (DomainRuleException ex)
        {
            return ProblemResponse<AvailabilityPreviewResponseDto>(ex.SuggestedHttpStatus, ex.Code, "Помилка розрахунку", ex.Message);
        }
    }

    // ==================== БРОНЮВАННЯ ТА ЖИТТЄВИЙ ЦИКЛ ОРЕНДИ ====================

    [HttpGet("bookings")]
    public ActionResult<IReadOnlyList<BookingResponseDto>> GetBookings(
        [FromQuery] string? status = null,
        [FromQuery] string? unitId = null)
    {
        var user = _auth.ResolveCurrentUser(HttpContext, _repo);
        if (user is null)
            return ProblemResponse<IReadOnlyList<BookingResponseDto>>(401, "UNAUTHORIZED", "Потрібна автентифікація", "Увійдіть до системи для перегляду списку бронювань.");

        string? filterClientUserId = user.Role == UserRole.MANAGER ? null : user.Id;
        var bookings = _repo.GetBookings(filterClientUserId, status, unitId)
            .Select(b => RentalApplicationService.MapBooking(b))
            .ToList();

        return Ok(bookings);
    }

    [HttpGet("bookings/{id}")]
    public ActionResult<BookingResponseDto> GetBookingById(string id)
    {
        var user = _auth.ResolveCurrentUser(HttpContext, _repo);
        if (user is null)
            return ProblemResponse<BookingResponseDto>(401, "UNAUTHORIZED", "Потрібна автентифікація", "Увійдіть до системи для перегляду заявки.");

        var booking = _repo.GetBookingById(id);
        if (booking is null)
            return ProblemResponse<BookingResponseDto>(404, "BOOKING_NOT_FOUND", "Бронювання не знайдено", $"Заявку із ідентифікатором «{id}» не знайдено.");

        if (user.Role == UserRole.CLIENT && !string.Equals(booking.ClientUserId, user.Id, StringComparison.OrdinalIgnoreCase))
        {
            _logger.LogWarning("Unauthorized access attempt by {UserId} to booking {BookingId} owned by {OwnerId}",
                user.Id, booking.Id, booking.ClientUserId);
            return ProblemResponse<BookingResponseDto>(403, "FORBIDDEN_NOT_OWNER", "Доступ заборонено", "Ви не маєте права переглядати приватні дані чужого бронювання.");
        }

        var events = _repo.GetEventsForBooking(booking.Id);
        return Ok(RentalApplicationService.MapBooking(booking, events));
    }

    [HttpPost("bookings")]
    public ActionResult<BookingResponseDto> CreateBooking([FromBody] CreateBookingRequestDto request)
    {
        var user = _auth.ResolveCurrentUser(HttpContext, _repo);
        if (user is null)
            return ProblemResponse<BookingResponseDto>(401, "UNAUTHORIZED", "Потрібна автентифікація", "Для оформлення заявки на оренду необхідно увійти в систему.");

        if (!TryParseTimestamp(request.StartsAt, out var startsAt) || !TryParseTimestamp(request.EndsAt, out var endsAt))
            return ProblemResponse<BookingResponseDto>(400, "INVALID_DATE", "Некоректний формат дати", "Некоректно вказано часовий інтервал оренди.");

        try
        {
            var created = _repo.CreateBookingAtomic(
                user.Id,
                request.UnitId,
                startsAt,
                endsAt,
                request.Purpose,
                RentalApplicationService.DefaultDemoNow);

            var events = _repo.GetEventsForBooking(created.Id);
            _logger.LogInformation("Booking {BookingNumber} created for unit {UnitId} by {UserId} [TraceId={TraceId}]",
                created.BookingNumber, created.UnitId, user.Id, HttpContext.TraceIdentifier);

            return StatusCode(201, RentalApplicationService.MapBooking(created, events));
        }
        catch (DomainRuleException ex)
        {
            _logger.LogWarning("Booking creation rejected ({Code}): {Message} [TraceId={TraceId}]",
                ex.Code, ex.Message, HttpContext.TraceIdentifier);
            return ProblemResponse<BookingResponseDto>(ex.SuggestedHttpStatus, ex.Code, "Відмова у створенні бронювання", ex.Message);
        }
    }

    [HttpPost("bookings/{id}/extend")]
    public ActionResult<BookingResponseDto> ExtendBooking(string id, [FromBody] ExtendBookingRequestDto request)
    {
        var user = _auth.ResolveCurrentUser(HttpContext, _repo);
        if (user is null)
            return ProblemResponse<BookingResponseDto>(401, "UNAUTHORIZED", "Потрібна автентифікація", "Увійдіть до системи.");

        if (!TryParseTimestamp(request.NewEndsAt, out var newEndsAt))
            return ProblemResponse<BookingResponseDto>(400, "INVALID_DATE", "Некоректна дата", "Вкажіть коректну нову дату завершення оренди.");

        try
        {
            var updated = _repo.ExtendBookingAtomic(id, user, newEndsAt, RentalApplicationService.DefaultDemoNow);
            var events = _repo.GetEventsForBooking(updated.Id);
            return Ok(RentalApplicationService.MapBooking(updated, events));
        }
        catch (DomainRuleException ex)
        {
            return ProblemResponse<BookingResponseDto>(ex.SuggestedHttpStatus, ex.Code, "Неможливо продовжити оренду", ex.Message);
        }
    }

    [HttpPost("bookings/{id}/cancel")]
    public ActionResult<BookingResponseDto> CancelBooking(string id, [FromBody] ManagerDecisionRequestDto? request)
    {
        var user = _auth.ResolveCurrentUser(HttpContext, _repo);
        if (user is null)
            return ProblemResponse<BookingResponseDto>(401, "UNAUTHORIZED", "Потрібна автентифікація", "Увійдіть до системи.");

        try
        {
            var updated = _repo.CancelBookingAtomic(id, user, request?.Notes ?? "Скасовано за запитом користувача", RentalApplicationService.DefaultDemoNow);
            var events = _repo.GetEventsForBooking(updated.Id);
            return Ok(RentalApplicationService.MapBooking(updated, events));
        }
        catch (DomainRuleException ex)
        {
            return ProblemResponse<BookingResponseDto>(ex.SuggestedHttpStatus, ex.Code, "Помилка скасування бронювання", ex.Message);
        }
    }

    [HttpPost("bookings/{id}/confirm")]
    public ActionResult<BookingResponseDto> ConfirmBooking(string id, [FromBody] ManagerDecisionRequestDto? request)
    {
        var user = _auth.ResolveCurrentUser(HttpContext, _repo);
        if (user is null)
            return ProblemResponse<BookingResponseDto>(401, "UNAUTHORIZED", "Потрібна автентифікація", "Увійдіть до системи.");
        if (user.Role != UserRole.MANAGER)
            return ProblemResponse<BookingResponseDto>(403, "FORBIDDEN_ROLE", "Недостатньо повноважень", "Лише менеджер сервісу оренди має право погоджувати заявки.");

        try
        {
            var updated = _repo.ConfirmBookingAtomic(id, user.Id, request?.Notes ?? "", RentalApplicationService.DefaultDemoNow);
            var events = _repo.GetEventsForBooking(updated.Id);
            return Ok(RentalApplicationService.MapBooking(updated, events));
        }
        catch (DomainRuleException ex)
        {
            return ProblemResponse<BookingResponseDto>(ex.SuggestedHttpStatus, ex.Code, "Помилка погодження заявки", ex.Message);
        }
    }

    [HttpPost("bookings/{id}/reject")]
    public ActionResult<BookingResponseDto> RejectBooking(string id, [FromBody] ManagerDecisionRequestDto? request)
    {
        var user = _auth.ResolveCurrentUser(HttpContext, _repo);
        if (user is null)
            return ProblemResponse<BookingResponseDto>(401, "UNAUTHORIZED", "Потрібна автентифікація", "Увійдіть до системи.");
        if (user.Role != UserRole.MANAGER)
            return ProblemResponse<BookingResponseDto>(403, "FORBIDDEN_ROLE", "Недостатньо повноважень", "Лише менеджер має право відхиляти заявки.");

        try
        {
            var updated = _repo.RejectBookingAtomic(id, user.Id, request?.RejectionReason ?? "", RentalApplicationService.DefaultDemoNow);
            var events = _repo.GetEventsForBooking(updated.Id);
            return Ok(RentalApplicationService.MapBooking(updated, events));
        }
        catch (DomainRuleException ex)
        {
            return ProblemResponse<BookingResponseDto>(ex.SuggestedHttpStatus, ex.Code, "Помилка відхилення заявки", ex.Message);
        }
    }

    [HttpPost("bookings/{id}/issue")]
    public ActionResult<BookingResponseDto> IssueBooking(string id, [FromBody] ManagerDecisionRequestDto? request)
    {
        var user = _auth.ResolveCurrentUser(HttpContext, _repo);
        if (user is null)
            return ProblemResponse<BookingResponseDto>(401, "UNAUTHORIZED", "Потрібна автентифікація", "Увійдіть до системи.");
        if (user.Role != UserRole.MANAGER)
            return ProblemResponse<BookingResponseDto>(403, "FORBIDDEN_ROLE", "Недостатньо повноважень", "Лише менеджер має право оформлювати видачу обладнання.");

        var issuedAt = TryParseTimestamp(request?.ActualTimestamp, out var ts) ? ts : RentalApplicationService.DefaultDemoNow;
        try
        {
            var updated = _repo.IssueEquipmentAtomic(id, user.Id, request?.Notes ?? "", issuedAt);
            var events = _repo.GetEventsForBooking(updated.Id);
            return Ok(RentalApplicationService.MapBooking(updated, events));
        }
        catch (DomainRuleException ex)
        {
            return ProblemResponse<BookingResponseDto>(ex.SuggestedHttpStatus, ex.Code, "Помилка видачі екземпляра", ex.Message);
        }
    }

    [HttpPost("bookings/{id}/return")]
    public ActionResult<BookingResponseDto> ReturnBooking(string id, [FromBody] ManagerDecisionRequestDto? request)
    {
        var user = _auth.ResolveCurrentUser(HttpContext, _repo);
        if (user is null)
            return ProblemResponse<BookingResponseDto>(401, "UNAUTHORIZED", "Потрібна автентифікація", "Увійдіть до системи.");
        if (user.Role != UserRole.MANAGER)
            return ProblemResponse<BookingResponseDto>(403, "FORBIDDEN_ROLE", "Недостатньо повноважень", "Лише менеджер має право оформлювати повернення обладнання.");

        var returnedAt = TryParseTimestamp(request?.ActualTimestamp, out var ts) ? ts : RentalApplicationService.DefaultDemoNow;
        try
        {
            var updated = _repo.ReturnEquipmentAtomic(id, user.Id, request?.Notes ?? "", returnedAt);
            var events = _repo.GetEventsForBooking(updated.Id);
            return Ok(RentalApplicationService.MapBooking(updated, events));
        }
        catch (DomainRuleException ex)
        {
            return ProblemResponse<BookingResponseDto>(ex.SuggestedHttpStatus, ex.Code, "Помилка оформлення повернення", ex.Message);
        }
    }

    // ==================== ЧЕРГА ОЧІКУВАННЯ (WAITLIST) ====================

    [HttpGet("waitlist")]
    public ActionResult<IReadOnlyList<WaitlistEntryDto>> GetWaitlist()
    {
        var user = _auth.ResolveCurrentUser(HttpContext, _repo);
        if (user is null)
            return ProblemResponse<IReadOnlyList<WaitlistEntryDto>>(401, "UNAUTHORIZED", "Потрібна автентифікація", "Увійдіть до системи для перегляду черги очікування.");

        string? clientFilter = user.Role == UserRole.MANAGER ? null : user.Id;
        var entries = _repo.GetWaitlistEntries(clientFilter)
            .Select(w => new WaitlistEntryDto(
                w.Id,
                w.EquipmentTypeId,
                w.EquipmentTitle ?? "",
                w.PreferredUnitId,
                w.PreferredInventoryCode,
                w.ClientUserId,
                w.ClientName ?? "",
                w.DesiredStartsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
                w.DesiredEndsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
                w.Status.ToString(),
                w.ContactNote,
                w.NotifiedAt?.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
                w.CreatedAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
            )).ToList();

        return Ok(entries);
    }

    [HttpPost("waitlist")]
    public ActionResult<WaitlistEntryDto> CreateWaitlistEntry([FromBody] CreateWaitlistRequestDto request)
    {
        var user = _auth.ResolveCurrentUser(HttpContext, _repo);
        if (user is null)
            return ProblemResponse<WaitlistEntryDto>(401, "UNAUTHORIZED", "Потрібна автентифікація", "Увійдіть до системи, щоб стати в чергу очікування.");

        if (!TryParseTimestamp(request.DesiredStartsAt, out var startsAt) ||
            !TryParseTimestamp(request.DesiredEndsAt, out var endsAt))
        {
            return ProblemResponse<WaitlistEntryDto>(400, "INVALID_DATE", "Некоректна дата", "Вкажіть коректний бажаний інтервал часу.");
        }

        try
        {
            var w = _repo.AddWaitlistEntry(
                user.Id,
                request.EquipmentTypeId,
                request.PreferredUnitId,
                startsAt,
                endsAt,
                request.ContactNote,
                RentalApplicationService.DefaultDemoNow);

            return StatusCode(201, new WaitlistEntryDto(
                w.Id,
                w.EquipmentTypeId,
                w.EquipmentTitle ?? "",
                w.PreferredUnitId,
                w.PreferredInventoryCode,
                w.ClientUserId,
                w.ClientName ?? "",
                w.DesiredStartsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
                w.DesiredEndsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
                w.Status.ToString(),
                w.ContactNote,
                w.NotifiedAt?.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
                w.CreatedAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
            ));
        }
        catch (DomainRuleException ex)
        {
            return ProblemResponse<WaitlistEntryDto>(ex.SuggestedHttpStatus, ex.Code, "Помилка запису в чергу очікування", ex.Message);
        }
    }

    [HttpPost("waitlist/{id}/cancel")]
    public ActionResult<WaitlistEntryDto> CancelWaitlist(string id)
    {
        var user = _auth.ResolveCurrentUser(HttpContext, _repo);
        if (user is null)
            return ProblemResponse<WaitlistEntryDto>(401, "UNAUTHORIZED", "Потрібна автентифікація", "Увійдіть до системи.");

        try
        {
            var w = _repo.CancelWaitlistEntry(id, user);
            return Ok(new WaitlistEntryDto(
                w.Id,
                w.EquipmentTypeId,
                w.EquipmentTitle ?? "",
                w.PreferredUnitId,
                w.PreferredInventoryCode,
                w.ClientUserId,
                w.ClientName ?? "",
                w.DesiredStartsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
                w.DesiredEndsAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
                w.Status.ToString(),
                w.ContactNote,
                w.NotifiedAt?.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"),
                w.CreatedAt.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
            ));
        }
        catch (DomainRuleException ex)
        {
            return ProblemResponse<WaitlistEntryDto>(ex.SuggestedHttpStatus, ex.Code, "Помилка скасування черги", ex.Message);
        }
    }

    // ==================== КЕРУВАННЯ ЕКЗЕМПЛЯРАМИ (МЕНЕДЖЕР) ====================

    public sealed record UpdateUnitConditionDto(string ConditionStatus, string Notes);

    [HttpPut("units/{unitId}/condition")]
    public ActionResult<object> UpdateUnitCondition(string unitId, [FromBody] UpdateUnitConditionDto request)
    {
        var user = _auth.ResolveCurrentUser(HttpContext, _repo);
        if (user is null)
            return ProblemResponse<object>(401, "UNAUTHORIZED", "Потрібна автентифікація", "Увійдіть до системи.");
        if (user.Role != UserRole.MANAGER)
            return ProblemResponse<object>(403, "FORBIDDEN_ROLE", "Недостатньо повноважень", "Лише менеджер може змінювати технічний статус фізичного екземпляра.");

        if (!Enum.TryParse<UnitConditionStatus>(request.ConditionStatus, true, out var parsedStatus))
            return ProblemResponse<object>(400, "INVALID_CONDITION_STATUS", "Некоректний статус", "Допустимі стани: AVAILABLE, IN_MAINTENANCE, RETIRED.");

        try
        {
            _repo.UpdateUnitCondition(unitId, parsedStatus, request.Notes ?? "");
            return Ok(new { unitId, conditionStatus = parsedStatus.ToString(), notes = request.Notes ?? "" });
        }
        catch (DomainRuleException ex)
        {
            return ProblemResponse<object>(ex.SuggestedHttpStatus, ex.Code, "Помилка оновлення екземпляра", ex.Message);
        }
    }
}
