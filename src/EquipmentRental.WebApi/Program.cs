using EquipmentRental.Application;
using EquipmentRental.Domain;
using EquipmentRental.Infrastructure;
using EquipmentRental.WebApi;
using Microsoft.AspNetCore.Mvc;

var builder = WebApplication.CreateBuilder(args);

static string FindRepoRoot(string startDir)
{
    var dir = new DirectoryInfo(startDir);
    while (dir != null)
    {
        if (File.Exists(Path.Combine(dir.FullName, "sql", "init.sql")))
        {
            return dir.FullName;
        }
        dir = dir.Parent;
    }
    return startDir;
}

string rootDir = FindRepoRoot(builder.Environment.ContentRootPath);
if (!File.Exists(Path.Combine(rootDir, "sql", "init.sql")))
{
    rootDir = FindRepoRoot(AppContext.BaseDirectory);
}

string webRootCandidate = Path.Combine(rootDir, "src", "EquipmentRental.WebApi", "wwwroot");
if (Directory.Exists(webRootCandidate))
{
    builder.Environment.WebRootPath = webRootCandidate;
}

string dbPath = Environment.GetEnvironmentVariable("EQUIPRENT_DB_PATH")
    ?? Path.Combine(rootDir, "Data", "equipment_rental.db");
string initSqlPath = Path.Combine(rootDir, "sql", "init.sql");
string seedSqlPath = Path.Combine(rootDir, "sql", "seed.sql");

var repository = new SqliteRentalRepository(dbPath);
if (File.Exists(initSqlPath))
{
    repository.EnsureDatabaseInitialized(initSqlPath, seedSqlPath);
}

builder.Services.AddSingleton<IRentalRepository>(repository);
builder.Services.AddSingleton<RentalApplicationService>();
builder.Services.AddSingleton<SessionAuthManager>();

builder.Services.AddControllers()
    .ConfigureApiBehaviorOptions(options =>
    {
        options.InvalidModelStateResponseFactory = context =>
        {
            var fieldErrors = context.ModelState
                .Where(kvp => kvp.Value?.Errors.Count > 0)
                .SelectMany(kvp => kvp.Value!.Errors.Select(err =>
                    new FieldErrorDto(kvp.Key, err.ErrorMessage)))
                .ToList();

            var response = new ApiErrorResponse(
                Type: "https://equiprent.op.edu.ua/problems/validation-error",
                Title: "Помилка валідації вхідних даних",
                Status: 400,
                Detail: fieldErrors.FirstOrDefault()?.Message ?? "Перевірте правильність заповнення полів форми.",
                Code: "VALIDATION_ERROR",
                TraceId: context.HttpContext.TraceIdentifier,
                FieldErrors: fieldErrors
            );
            return new BadRequestObjectResult(response);
        };
    });

var app = builder.Build();

app.UseDefaultFiles();
app.UseStaticFiles();
app.MapControllers();
app.MapFallbackToFile("index.html");

app.Run();

public partial class Program { }
