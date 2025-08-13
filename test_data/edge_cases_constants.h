/**
 * Edge cases constants file for testing parser robustness
 * Contains various edge cases and special scenarios
 */

#ifndef EDGE_CASES_CONSTANTS_H
#define EDGE_CASES_CONSTANTS_H

#include <string>

// Constants with special characters in values
#define REGEX_PATTERN "^[a-zA-Z0-9_]+$"
#define SQL_QUERY "SELECT * FROM users WHERE id = ?"
#define JSON_TEMPLATE "{\"status\": \"ok\", \"data\": null}"
#define UNICODE_STRING u8"Hello, 世界"
#define ESCAPED_QUOTES "He said \"Hello\" to me"
#define BACKSLASH_PATH "C:\\Program Files\\MyApp\\"

// Multi-line string constants
#define MULTILINE_STRING "Line 1\n" \
                         "Line 2\n" \
                         "Line 3"

#define HELP_TEXT "Usage: app [options] <input_file>\n" \
                  "Options:\n" \
                  "  -h, --help     Show this help message\n" \
                  "  -v, --verbose  Enable verbose output\n"

// Constants with calculations
#define CIRCLE_AREA(r) (3.14159 * (r) * (r))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define MIN(a, b) ((a) < (b) ? (a) : (b))

// Constants with complex expressions
#define BUFFER_SIZE (1024 * 1024)
#define TIMEOUT_MS (30 * 1000)
#define BITMASK ((1 << 8) - 1)

// Very long constant name
#define VERY_LONG_CONSTANT_NAME_THAT_EXCEEDS_NORMAL_LENGTH_EXPECTATIONS_AND_TESTS_PARSER_LIMITS 42

// Constants with unusual spacing
#define    SPACED_DEFINE     123
#define	TAB_SEPARATED	456
#define MIXED_SPACING   	789

// Constants with comments
#define DOCUMENTED_CONSTANT 100  // This is a documented constant
#define ANOTHER_CONSTANT 200     /* Block comment */

// Conditional constants
#ifdef DEBUG
    #define DEBUG_BUFFER_SIZE 2048
    #define DEBUG_ENABLED 1
#else
    #define DEBUG_BUFFER_SIZE 1024
    #define DEBUG_ENABLED 0
#endif

// Platform-specific constants
#ifdef _WIN32
    #define PLATFORM_NAME "Windows"
    #define PATH_SEP '\\'
#elif defined(__linux__)
    #define PLATFORM_NAME "Linux"
    #define PATH_SEP '/'
#elif defined(__APPLE__)
    #define PLATFORM_NAME "macOS"
    #define PATH_SEP '/'
#else
    #define PLATFORM_NAME "Unknown"
    #define PATH_SEP '/'
#endif

// Constants with different numeric formats
#define HEX_CONSTANT 0xFF00
#define OCTAL_CONSTANT 0755
#define BINARY_CONSTANT 0b11110000
#define FLOAT_CONSTANT 3.14159f
#define DOUBLE_CONSTANT 2.71828
#define SCIENTIFIC_NOTATION 1.23e-4

// String constants with various formats
const char* C_STRING = "C-style string";
const std::string CPP_STRING = "C++ string";
const char CHAR_CONSTANT = 'A';
const wchar_t WIDE_CHAR = L'W';

// Const variables with complex types
const int ARRAY_CONSTANTS[] = {1, 2, 3, 4, 5};
const struct {
    int x;
    int y;
} POINT_CONSTANT = {10, 20};

// Constexpr with complex expressions
constexpr int COMPILE_TIME_CALC = 10 * 20 + 5;
constexpr double PI_OVER_2 = 3.14159 / 2.0;

// Namespace constants with edge cases
namespace EdgeCases {
    const int NESTED_CONSTANT = 999;
    
    namespace Nested {
        const int DEEPLY_NESTED = 888;
    }
}

// Template-related constants (if parser supports)
template<int N>
constexpr int TEMPLATE_CONSTANT = N * 2;

// Constants with unusual but valid C++ syntax
#define STRINGIZE(x) #x
#define CONCAT(a, b) a ## b

// Empty define
#define EMPTY_DEFINE

// Define with only whitespace
#define WHITESPACE_DEFINE   

// Constants that might confuse parsers
#define TRICKY_COMMENT /* comment */ 123 /* another comment */
#define NESTED_PARENS ((((42))))

#endif // EDGE_CASES_CONSTANTS_H