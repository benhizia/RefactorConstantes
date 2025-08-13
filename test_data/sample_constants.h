/**
 * Sample constants file for testing the C++ constants refactor tool
 * Contains various types of constants to test parsing and categorization
 */

#ifndef SAMPLE_CONSTANTS_H
#define SAMPLE_CONSTANTS_H

#include <string>

// Preprocessor defines
#define MAX_BUFFER_SIZE 1024
#define MIN_BUFFER_SIZE 64
#define DEFAULT_TIMEOUT 30000
#define PI 3.14159265359
#define VERSION_MAJOR 2
#define VERSION_MINOR 1
#define VERSION_PATCH 0
#define BUILD_NUMBER 12345

// String defines
#define DEFAULT_CONFIG_FILE "config.ini"
#define LOG_FILE_PREFIX "app_log_"
#define ERROR_MESSAGE_PREFIX "[ERROR] "
#define WARNING_MESSAGE_PREFIX "[WARN] "

// Conditional defines
#ifdef DEBUG
#define DEBUG_LEVEL 3
#define ENABLE_LOGGING 1
#else
#define DEBUG_LEVEL 0
#define ENABLE_LOGGING 0
#endif

// Math constants
#define EULER_NUMBER 2.71828182846
#define GOLDEN_RATIO 1.61803398875
#define SQRT_2 1.41421356237

// Network constants
#define DEFAULT_PORT 8080
#define MAX_CONNECTIONS 100
#define SOCKET_TIMEOUT 5000
#define RETRY_COUNT 3

// File system constants
#define MAX_PATH_LENGTH 260
#define MAX_FILENAME_LENGTH 255
#define TEMP_DIR_PREFIX "tmp_"

// Const variables
const int ARRAY_SIZE = 256;
const double CONVERSION_FACTOR = 2.54;
const bool ENABLE_CACHE = true;
const char DELIMITER = ',';

// Constexpr variables
constexpr int COMPILE_TIME_CONSTANT = 42;
constexpr double PHYSICS_CONSTANT = 9.81;
constexpr size_t HASH_TABLE_SIZE = 1024;
constexpr bool IS_PRODUCTION = false;

// String constants
const std::string DATABASE_URL = "localhost:5432";
const std::string API_ENDPOINT = "/api/v1/";
const std::string DEFAULT_USER = "admin";

// Namespace constants
namespace Config {
    const int MAX_RETRIES = 5;
    const double THRESHOLD = 0.95;
    const std::string CONFIG_SECTION = "main";
}

namespace Network {
    const int HTTP_OK = 200;
    const int HTTP_NOT_FOUND = 404;
    const int HTTP_SERVER_ERROR = 500;
    const std::string USER_AGENT = "TestApp/1.0";
}

// Enum constants
enum class LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARNING = 2,
    ERROR = 3,
    CRITICAL = 4
};

enum Status {
    STATUS_OK = 0,
    STATUS_ERROR = -1,
    STATUS_PENDING = 1,
    STATUS_TIMEOUT = 2
};

// Complex constants with comments
const int BUFFER_POOL_SIZE = 64;  // Size of the buffer pool for memory management
const double PERFORMANCE_THRESHOLD = 0.85;  // Minimum acceptable performance ratio
const bool ENABLE_PROFILING = false;  // Enable performance profiling in debug builds

// Array constants
const int PRIORITY_LEVELS[] = {1, 2, 3, 4, 5};
const char* ERROR_CODES[] = {"E001", "E002", "E003", "E004"};

// Multi-line constants
const std::string HELP_TEXT = 
    "Usage: app [options] <input_file>\n"
    "Options:\n"
    "  -h, --help     Show this help message\n"
    "  -v, --verbose  Enable verbose output\n"
    "  -o, --output   Specify output file\n";

// Constants with special characters
#define REGEX_PATTERN "^[a-zA-Z0-9_]+$"
#define SQL_QUERY "SELECT * FROM users WHERE id = ?"
#define JSON_TEMPLATE "{\"status\": \"ok\", \"data\": null}"

// Bit manipulation constants
#define BIT_0 (1 << 0)
#define BIT_1 (1 << 1)
#define BIT_2 (1 << 2)
#define BIT_3 (1 << 3)
#define ALL_BITS 0xFFFFFFFF

// Size constants
#define KB 1024
#define MB (1024 * KB)
#define GB (1024 * MB)

// Time constants
#define SECONDS_PER_MINUTE 60
#define MINUTES_PER_HOUR 60
#define HOURS_PER_DAY 24
#define DAYS_PER_WEEK 7

// Color constants (hex values)
#define COLOR_RED 0xFF0000
#define COLOR_GREEN 0x00FF00
#define COLOR_BLUE 0x0000FF
#define COLOR_WHITE 0xFFFFFF
#define COLOR_BLACK 0x000000

// Feature flags
#define FEATURE_ENCRYPTION_ENABLED 1
#define FEATURE_COMPRESSION_ENABLED 1
#define FEATURE_ANALYTICS_ENABLED 0
#define FEATURE_BETA_UI_ENABLED 0

// Version information
#define VERSION_STRING "2.1.0-beta"
#define BUILD_DATE __DATE__
#define BUILD_TIME __TIME__

// Platform-specific constants
#ifdef _WIN32
#define PATH_SEPARATOR '\\'
#define LINE_ENDING "\r\n"
#else
#define PATH_SEPARATOR '/'
#define LINE_ENDING "\n"
#endif

// Constants with calculations
#define CIRCLE_AREA(r) (PI * (r) * (r))
#define RECTANGLE_AREA(w, h) ((w) * (h))
#define CELSIUS_TO_FAHRENHEIT(c) (((c) * 9.0 / 5.0) + 32.0)

#endif // SAMPLE_CONSTANTS_H