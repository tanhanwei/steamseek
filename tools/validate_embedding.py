import json

def validate_embeddings(filename):
    print("Starting embedding validation...")
    stats = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "dimension_errors": 0,
        "missing_fields": 0
    }
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                stats["total"] += 1
                try:
                    record = json.loads(line)
                    
                    # Check required fields
                    if not all(field in record for field in ["appid", "name", "embedding"]):
                        print(f"Line {line_num}: Missing required fields")
                        stats["missing_fields"] += 1
                        continue
                    
                    # Check embedding format and dimension
                    embedding = record["embedding"]
                    if not isinstance(embedding, list):
                        print(f"Line {line_num}: Embedding is not a list")
                        stats["invalid"] += 1
                        continue
                        
                    if len(embedding) != 3072:
                        print(f"Line {line_num}: Wrong embedding dimension: {len(embedding)}")
                        stats["dimension_errors"] += 1
                        continue
                    
                    # Check for non-numeric values
                    if not all(isinstance(x, (int, float)) for x in embedding):
                        print(f"Line {line_num}: Non-numeric values in embedding")
                        stats["invalid"] += 1
                        continue
                    
                    stats["valid"] += 1
                    
                except json.JSONDecodeError:
                    print(f"Line {line_num}: Invalid JSON")
                    stats["invalid"] += 1
                except Exception as e:
                    print(f"Line {line_num}: Unexpected error: {e}")
                    stats["invalid"] += 1
                
                if line_num % 1000 == 0:
                    print(f"Processed {line_num} records...")
                    
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
        
    print("\nValidation Results:")
    print(f"Total records: {stats['total']}")
    print(f"Valid records: {stats['valid']}")
    print(f"Invalid records: {stats['invalid']}")
    print(f"Dimension errors: {stats['dimension_errors']}")
    print(f"Missing fields: {stats['missing_fields']}")
    
    return stats

# Usage:
stats = validate_embeddings("embeddings.jsonl")