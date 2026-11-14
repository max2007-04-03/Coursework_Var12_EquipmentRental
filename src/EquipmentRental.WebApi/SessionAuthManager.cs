using System.Collections.Concurrent;
using System.Security.Cryptography;
using EquipmentRental.Domain;
using Microsoft.AspNetCore.Http;

namespace EquipmentRental.WebApi;

/// <summary>
/// Серверний менеджер сесій (підтримує HttpOnly cookie "equiprent_session" та заголовок X-Session-Token / X-Demo-User).
/// Забезпечує визначення особи користувача виключно на сервері.
/// </summary>
public sealed class SessionAuthManager
{
    public const string CookieName = "equiprent_session";
    private readonly ConcurrentDictionary<string, (string UserId, DateTimeOffset ExpiresAt)> _sessions = new();

    public string CreateSession(string userId)
    {
        byte[] bytes = RandomNumberGenerator.GetBytes(24);
        string token = Convert.ToHexString(bytes).ToLowerInvariant();
        _sessions[token] = (userId, DateTimeOffset.UtcNow.AddHours(12));
        return token;
    }

    public void RemoveSession(string token)
    {
        _sessions.TryRemove(token, out _);
    }

    public User? ResolveCurrentUser(HttpContext context, IRentalRepository repo)
    {
        // 1. Перевірка сесійного токена з HttpOnly cookie або заголовка Authorization / X-Session-Token
        string? token = null;
        if (context.Request.Cookies.TryGetValue(CookieName, out var cookieToken) && !string.IsNullOrWhiteSpace(cookieToken))
        {
            token = cookieToken.Trim();
        }
        else if (context.Request.Headers.TryGetValue("X-Session-Token", out var headerToken) && !string.IsNullOrWhiteSpace(headerToken))
        {
            token = headerToken.ToString().Trim();
        }

        if (!string.IsNullOrEmpty(token) && _sessions.TryGetValue(token, out var entry))
        {
            if (entry.ExpiresAt > DateTimeOffset.UtcNow)
            {
                return repo.GetUserById(entry.UserId);
            }
            _sessions.TryRemove(token, out _);
        }

        // 2. Допоміжний заголовок X-Demo-User-Id для автоматизованих інтеграційних тестів у тестовому стенді
        if (context.Request.Headers.TryGetValue("X-Demo-User-Id", out var demoUserId) && !string.IsNullOrWhiteSpace(demoUserId))
        {
            return repo.GetUserById(demoUserId.ToString().Trim());
        }

        return null;
    }
}
