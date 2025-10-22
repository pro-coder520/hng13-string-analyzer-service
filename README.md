# String Analyzer API

A Django-based REST API that analyzes and stores string properties with advanced filtering capabilities.

## Features

- Store and analyze strings with unique properties
- Compute string characteristics including:
  - Length
  - Palindrome status
  - Unique character count
  - Word count
  - Character frequency map
- Advanced filtering options
- Natural language query support
- SHA-256 hash-based deduplication

## API Endpoints

### POST /strings
Creates a new string entry with computed properties.

```json
{
    "value": "Your string here"
}
```

### GET /strings
Retrieves all strings with optional filters:
- `is_palindrome` (boolean)
- `min_length` (integer)
- `max_length` (integer)
- `word_count` (integer)
- `contains_character` (single character)

### GET /strings/{string_value}
Retrieves details for a specific string.

### DELETE /strings/{string_value}
Removes a string from the system.

### GET /strings/filter-by-natural-language
Filters strings using natural language queries.

Example queries:
- "Show me palindromic strings"
- "Find strings with exactly 5 words"
- "Show strings longer than 10 characters"
- "Find strings containing the letter a"

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install django
```
3. Run migrations:
```bash
python manage.py migrate
```
4. Start the development server:
```bash
python manage.py runserver
```

## Example Usage

```bash
# Create a new string
curl -X POST http://localhost:8000/strings \
  -H "Content-Type: application/json" \
  -d '{"value": "Hello World"}'

# Get all palindromes
curl "http://localhost:8000/strings?is_palindrome=true"

# Natural language query
curl "http://localhost:8000/strings/filter-by-natural-language?query=Show%20me%20palindromic%20strings"
```

## Technical Details

- Built with Django
- In-memory storage using Python dictionary
- SHA-256 hashing for string identification
- CSRF exempt for API endpoints
- UTC timestamp for creation time

## Error Handling

The API returns appropriate HTTP status codes:
- 200: Success
- 201: Created
- 204: No Content (successful deletion)
- 400: Bad Request
- 404: Not Found
- 405: Method Not Allowed
- 409: Conflict (duplicate string)
- 422: Unprocessable Entity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Submit a pull request

## License

This project is open source and available under the MIT License.