/**
 * Large constants file for comprehensive testing
 * Contains 100+ constants of various types for thorough testing
 */

#ifndef LARGE_CONSTANTS_H
#define LARGE_CONSTANTS_H

#include <string>
#include <vector>

// Basic preprocessor defines (1-20)
#define MAX_BUFFER_SIZE 1024
#define MIN_BUFFER_SIZE 64
#define DEFAULT_TIMEOUT 30000
#define PI 3.14159265359
#define VERSION_MAJOR 2
#define VERSION_MINOR 1
#define VERSION_PATCH 0
#define BUILD_NUMBER 12345
#define EULER_NUMBER 2.71828182846
#define GOLDEN_RATIO 1.61803398875
#define SQRT_2 1.41421356237
#define DEFAULT_PORT 8080
#define MAX_CONNECTIONS 100
#define SOCKET_TIMEOUT 5000
#define RETRY_COUNT 3
#define MAX_PATH_LENGTH 260
#define MAX_FILENAME_LENGTH 255
#define TEMP_DIR_PREFIX "tmp_"
#define DEBUG_LEVEL 3
#define ENABLE_LOGGING 1

// String defines (21-35)
#define DEFAULT_CONFIG_FILE "config.ini"
#define LOG_FILE_PREFIX "app_log_"
#define ERROR_MESSAGE_PREFIX "[ERROR] "
#define WARNING_MESSAGE_PREFIX "[WARN] "
#define INFO_MESSAGE_PREFIX "[INFO] "
#define DATABASE_HOST "localhost"
#define DATABASE_NAME "testdb"
#define API_VERSION "v1"
#define USER_AGENT_STRING "TestApp/1.0"
#define CONTENT_TYPE_JSON "application/json"
#define CONTENT_TYPE_XML "application/xml"
#define CHARSET_UTF8 "UTF-8"
#define LOCALE_EN_US "en_US"
#define TIMEZONE_UTC "UTC"
#define ENCRYPTION_ALGORITHM "AES-256"

// Numeric constants (36-55)
#define SECONDS_PER_MINUTE 60
#define MINUTES_PER_HOUR 60
#define HOURS_PER_DAY 24
#define DAYS_PER_WEEK 7
#define MONTHS_PER_YEAR 12
#define KB 1024
#define MB (1024 * KB)
#define GB (1024 * MB)
#define TB (1024 * GB)
#define BIT_0 (1 << 0)
#define BIT_1 (1 << 1)
#define BIT_2 (1 << 2)
#define BIT_3 (1 << 3)
#define BIT_4 (1 << 4)
#define BIT_5 (1 << 5)
#define BIT_6 (1 << 6)
#define BIT_7 (1 << 7)
#define ALL_BITS_8 0xFF
#define ALL_BITS_16 0xFFFF
#define ALL_BITS_32 0xFFFFFFFF

// Color constants (56-70)
#define COLOR_RED 0xFF0000
#define COLOR_GREEN 0x00FF00
#define COLOR_BLUE 0x0000FF
#define COLOR_WHITE 0xFFFFFF
#define COLOR_BLACK 0x000000
#define COLOR_YELLOW 0xFFFF00
#define COLOR_CYAN 0x00FFFF
#define COLOR_MAGENTA 0xFF00FF
#define COLOR_GRAY 0x808080
#define COLOR_DARK_GRAY 0x404040
#define COLOR_LIGHT_GRAY 0xC0C0C0
#define COLOR_ORANGE 0xFF8000
#define COLOR_PURPLE 0x800080
#define COLOR_BROWN 0x8B4513
#define COLOR_PINK 0xFFC0CB

// Const variables (71-85)
const int ARRAY_SIZE = 256;
const double CONVERSION_FACTOR = 2.54;
const bool ENABLE_CACHE = true;
const char DELIMITER = ',';
const float FLOAT_PRECISION = 0.001f;
const long LONG_MAX_VALUE = 2147483647L;
const short SHORT_MAX_VALUE = 32767;
const unsigned int UINT_MAX_VALUE = 4294967295U;
const size_t SIZE_T_MAX = static_cast<size_t>(-1);
const double DOUBLE_EPSILON = 1e-9;
const float FLOAT_EPSILON = 1e-6f;
const int NEGATIVE_ONE = -1;
const int ZERO = 0;
const int ONE = 1;
const int TWO = 2;

// Constexpr variables (86-100)
constexpr int COMPILE_TIME_CONSTANT = 42;
constexpr double PHYSICS_CONSTANT = 9.81;
constexpr size_t HASH_TABLE_SIZE = 1024;
constexpr bool IS_PRODUCTION = false;
constexpr int MAX_THREADS = 8;
constexpr double TEMPERATURE_ABSOLUTE_ZERO = -273.15;
constexpr int ASCII_SPACE = 32;
constexpr int ASCII_NEWLINE = 10;
constexpr int ASCII_TAB = 9;
constexpr int ASCII_CARRIAGE_RETURN = 13;
constexpr long NANOSECONDS_PER_SECOND = 1000000000L;
constexpr int MICROSECONDS_PER_MILLISECOND = 1000;
constexpr int MILLISECONDS_PER_SECOND = 1000;
constexpr double RADIANS_PER_DEGREE = 0.017453292519943295;
constexpr double DEGREES_PER_RADIAN = 57.29577951308232;

// String constants (101-115)
const std::string DATABASE_URL = "localhost:5432";
const std::string API_ENDPOINT = "/api/v1/";
const std::string DEFAULT_USER = "admin";
const std::string DEFAULT_PASSWORD = "password123";
const std::string SESSION_COOKIE_NAME = "SESSIONID";
const std::string CSRF_TOKEN_HEADER = "X-CSRF-Token";
const std::string AUTHORIZATION_HEADER = "Authorization";
const std::string ACCEPT_HEADER = "Accept";
const std::string CACHE_CONTROL_HEADER = "Cache-Control";
const std::string EXPIRES_HEADER = "Expires";
const std::string LAST_MODIFIED_HEADER = "Last-Modified";
const std::string ETAG_HEADER = "ETag";
const std::string LOCATION_HEADER = "Location";
const std::string REFERER_HEADER = "Referer";
const std::string USER_AGENT_HEADER = "User-Agent";

// Namespace constants (116-130)
namespace Network {
    const int HTTP_OK = 200;
    const int HTTP_CREATED = 201;
    const int HTTP_NO_CONTENT = 204;
    const int HTTP_BAD_REQUEST = 400;
    const int HTTP_UNAUTHORIZED = 401;
    const int HTTP_FORBIDDEN = 403;
    const int HTTP_NOT_FOUND = 404;
    const int HTTP_METHOD_NOT_ALLOWED = 405;
    const int HTTP_CONFLICT = 409;
    const int HTTP_INTERNAL_SERVER_ERROR = 500;
    const int HTTP_NOT_IMPLEMENTED = 501;
    const int HTTP_BAD_GATEWAY = 502;
    const int HTTP_SERVICE_UNAVAILABLE = 503;
    const int HTTP_GATEWAY_TIMEOUT = 504;
    const std::string USER_AGENT = "TestApp/1.0";
}

namespace Config {
    const int MAX_RETRIES = 5;
    const double THRESHOLD = 0.95;
    const std::string CONFIG_SECTION = "main";
    const int CONNECTION_POOL_SIZE = 10;
    const int QUERY_TIMEOUT = 30;
    const bool AUTO_COMMIT = true;
    const std::string LOG_LEVEL = "INFO";
}

namespace Security {
    const int MIN_PASSWORD_LENGTH = 8;
    const int MAX_PASSWORD_LENGTH = 128;
    const int SALT_LENGTH = 16;
    const int HASH_ITERATIONS = 10000;
    const std::string ENCRYPTION_KEY_SIZE = "256";
}

// Additional complex constants for thorough testing
#define FEATURE_FLAG_A 1
#define FEATURE_FLAG_B 0
#define FEATURE_FLAG_C 1
#define FEATURE_FLAG_D 0
#define FEATURE_FLAG_E 1

// Platform-specific constants
#ifdef _WIN32
#define PATH_SEPARATOR '\\'
#define LINE_ENDING "\r\n"
#define SHARED_LIB_EXT ".dll"
#else
#define PATH_SEPARATOR '/'
#define LINE_ENDING "\n"
#define SHARED_LIB_EXT ".so"
#endif

// Conditional compilation constants
#ifdef DEBUG
#define ASSERT_ENABLED 1
#define MEMORY_DEBUGGING 1
#define PERFORMANCE_PROFILING 1
#else
#define ASSERT_ENABLED 0
#define MEMORY_DEBUGGING 0
#define PERFORMANCE_PROFILING 0
#endif

#endif // LARGE_CONSTANTS_H