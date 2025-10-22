import hashlib
import json
from datetime import datetime, timezone
import re
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Use a dictionary as an in-memory database
# The key is the sha256_hash of the string's value
db = {}

def compute_string_properties(value):
    """Computes all the required properties for a given string."""
    lower_value = value.lower()
    char_map = {}
    for char in value:
        char_map[char] = char_map.get(char, 0) + 1

    return {
        "length": len(value),
        "is_palindrome": lower_value == lower_value[::-1],
        "unique_characters": len(set(value)),
        "word_count": len(value.split()),
        "character_frequency_map": char_map
    }

def get_sha256_hash(value):
    """Calculates the SHA-256 hash of a string."""
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def strings_view(request):
    """
    Handles creating new strings (POST) and retrieving all strings with filtering (GET).
    Maps to /strings
    """
    # POST /strings
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

        if 'value' not in data:
            return JsonResponse({"error": "Missing 'value' field in request body"}, status=404)

        value = data['value']
        if not isinstance(value, str):
            return JsonResponse({"error": "'value' must be a string"}, status=422)

        sha256_hash = get_sha256_hash(value)

        if sha256_hash in db:
            return JsonResponse({"error": "String already exists in the system"}, status=409)

        properties = compute_string_properties(value)
        properties["sha256_hash"] = sha256_hash

        new_entry = {
            "id": sha256_hash,
            "value": value,
            "properties": properties,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        db[sha256_hash] = new_entry
        return JsonResponse(new_entry, status=201)

    # GET /strings
    elif request.method == 'GET':
        filters = {}
        filtered_data = list(db.values())

        try:
            if 'is_palindrome' in request.GET:
                is_palindrome = request.GET.get('is_palindrome').lower() == 'true'
                filters['is_palindrome'] = is_palindrome
                filtered_data = [s for s in filtered_data if s['properties']['is_palindrome'] == is_palindrome]

            if 'min_length' in request.GET:
                min_len = int(request.GET.get('min_length'))
                filters['min_length'] = min_len
                filtered_data = [s for s in filtered_data if s['properties']['length'] >= min_len]

            if 'max_length' in request.GET:
                max_len = int(request.GET.get('max_length'))
                filters['max_length'] = max_len
                filtered_data = [s for s in filtered_data if s['properties']['length'] <= max_len]

            if 'word_count' in request.GET:
                w_count = int(request.GET.get('word_count'))
                filters['word_count'] = w_count
                filtered_data = [s for s in filtered_data if s['properties']['word_count'] == w_count]

            if 'contains_character' in request.GET:
                char = request.GET.get('contains_character')
                if len(char) != 1:
                    return JsonResponse({"error": "Invalid value for 'contains_character'. Must be a single character."}, status=400)
                filters['contains_character'] = char
                filtered_data = [s for s in filtered_data if char in s['value']]

        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid query parameter value or type"}, status=400)

        response = {
            "data": filtered_data,
            "count": len(filtered_data),
            "filters_applied": filters
        }
        return JsonResponse(response, status=200)
        
    return JsonResponse({"error": "Method not allowed"}, status=405)



def string_detail_view(request, string_value):
    """
    Handles retrieving a specific string (GET) and deleting it (DELETE).
    Maps to /strings/{string_value}
    """
    sha256_hash = get_sha256_hash(string_value)
    if sha256_hash not in db:
        return JsonResponse({"error": "String does not exist in the system"}, status=404)

    # GET /strings/{string_value}
    if request.method == 'GET':
        return JsonResponse(db[sha256_hash], status=200)

    # DELETE /strings/{string_value}
    elif request.method == 'DELETE':
        del db[sha256_hash]
        return HttpResponse(status=204) # No Content
        
    return JsonResponse({"error": "Method not allowed"}, status=405)


def parse_natural_language_query(query):
    """
    Parses a natural language query into a dictionary of filters.
    This is a simplified heuristic-based parser.
    """
    filters = {}
    original_query = query
    query = query.lower()

    if "palindromic" in query or "palindrome" in query:
        filters["is_palindrome"] = True

    word_count_match = re.search(r'(\b(one|two|three|four|five|single)\b|\d+)\s+word', query)
    if word_count_match:
        count_str = word_count_match.group(1)
        word_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "single": 1}
        if count_str in word_map:
            filters["word_count"] = word_map[count_str]
        elif count_str.isdigit():
            filters["word_count"] = int(count_str)

    min_length_match = re.search(r'longer than (\d+)', query)
    if min_length_match:
        filters["min_length"] = int(min_length_match.group(1)) + 1

    max_length_match = re.search(r'shorter than (\d+)', query)
    if max_length_match:
        filters["max_length"] = int(max_length_match.group(1)) - 1
        
    length_match = re.search(r'exactly (\d+) characters', query)
    if length_match:
        length = int(length_match.group(1))
        filters["min_length"] = length
        filters["max_length"] = length

    contains_match = re.search(r'contain(?:s|ing) the letter ([a-z])', query)
    if contains_match:
        filters["contains_character"] = contains_match.group(1)
        
    if "first vowel" in query:
        filters["contains_character"] = "a"

    if not filters:
        return None

    return { "original": original_query, "parsed_filters": filters }


def filter_by_natural_language(request):
    """
    Endpoint to filter strings using a natural language query.
    Maps to /strings/filter-by-natural-language
    """
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    query = request.GET.get('query')
    if not query:
        return JsonResponse({"error": "Missing 'query' parameter"}, status=400)

    interpreted_query = parse_natural_language_query(query)
    if not interpreted_query:
        return JsonResponse({"error": "Unable to parse natural language query"}, status=400)

    parsed_filters = interpreted_query['parsed_filters']
    
    if 'min_length' in parsed_filters and 'max_length' in parsed_filters:
        if parsed_filters['min_length'] > parsed_filters['max_length']:
            return JsonResponse({
                "error": "Query parsed but resulted in conflicting filters",
                "conflicts": f"min_length ({parsed_filters['min_length']}) cannot be greater than max_length ({parsed_filters['max_length']})"
            }, status=422)
            
    filtered_data = list(db.values())
    
    if parsed_filters.get('is_palindrome'):
        filtered_data = [s for s in filtered_data if s['properties']['is_palindrome']]
    if 'word_count' in parsed_filters:
        wc = parsed_filters['word_count']
        filtered_data = [s for s in filtered_data if s['properties']['word_count'] == wc]
    if 'min_length' in parsed_filters:
        ml = parsed_filters['min_length']
        filtered_data = [s for s in filtered_data if s['properties']['length'] >= ml]
    if 'max_length' in parsed_filters:
        mxl = parsed_filters['max_length']
        filtered_data = [s for s in filtered_data if s['properties']['length'] <= mxl]
    if 'contains_character' in parsed_filters:
        char = parsed_filters['contains_character']
        filtered_data = [s for s in filtered_data if char in s['value']]

    response = {
        "data": filtered_data,
        "count": len(filtered_data),
        "interpreted_query": interpreted_query
    }
    return JsonResponse(response, status=200)



def home_view(request):
    """A simple view for the root URL and health checks."""
    return JsonResponse({
        "status": "ok", 
        "message": "String Analyzer API is running."
    }, status=200)