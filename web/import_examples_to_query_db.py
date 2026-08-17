#!/usr/bin/env python3
"""
Script to import all prompts from the examples folder into the query.db database.
This script will:
1. Create the community table in query.db if it doesn't exist
2. Read all prompt files from the examples folder
3. Import them into the database with appropriate metadata
"""

import os
import sqlite3
import uuid
import re
from pathlib import Path

# Database path
QUERY_DB_PATH = "/home/azzar/project/prompt-sanctuary/web/database/community/query.db"


def get_db_connection():
    """Get a connection to the SQLite database."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(QUERY_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(QUERY_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_community_table():
    """Create the community table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create the community table with the correct schema
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS community (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            random_val TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            tittle TEXT NOT NULL,
            prompt TEXT NOT NULL,
            tag TEXT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()
    print("✓ Community table created/verified in query.db")


def generate_random_val():
    """Generate a unique random value."""
    return str(uuid.uuid4())


def generate_appropriate_title(filename, category, content):
    """Generate an appropriate title based on filename, category, and content."""
    # Remove file extension
    base_name = os.path.splitext(filename)[0]

    title_mappings = {
        "Agent Prompt": "Cursor Agent Assistant Prompt",
        "Chat Prompt": "Cursor Chat Assistant Prompt",
        "Prompt": "AI Assistant Prompt",
        "Tools": "Tools Configuration",
        "Agent Loop": "Manus Agent Loop Configuration",
        "Modules": "Manus Agent Modules",
        "Model": "Model Configuration",
    }

    # Handle category-specific titles
    category_title_map = {
        "Devin AI": {"Prompt": "Devin AI Software Engineer Assistant"},
        "Windsurf": {
            "Prompt": "Windsurf AI Coding Assistant",
            "Tools": "Windsurf Tools Configuration",
        },
        "Replit": {"Prompt": "Replit AI Assistant Prompt", "Tools": "Replit Tools Configuration"},
        "VSCode Agent": {"Prompt": "VSCode Agent Assistant Prompt"},
        "Same.dev": {"Prompt": "Same.dev AI Assistant Prompt"},
        "Lovable": {"Prompt": "Lovable AI Development Assistant"},
        "dia": {"Prompt": "Dia AI Assistant Prompt"},
        "Trae": {"Chat Prompt": "Trae Chat Assistant Prompt"},
        "v0 Prompts and Tools": {
            "Prompt": "V0 AI Assistant Prompt",
            "Model": "V0 Model Configuration",
        },
    }

    # Check category-specific mappings first
    if category in category_title_map and base_name in category_title_map[category]:
        return category_title_map[category][base_name]

    # Check general mappings
    if base_name in title_mappings:
        return title_mappings[base_name]

    # For Open Source prompts, try to get more specific titles
    if category == "Open Source prompts":
        # Get the subcategory from the path
        path_parts = Path(content).parts if hasattr(content, "parts") else []
        if len(path_parts) > 0:
            subcategory = path_parts[-2] if len(path_parts) >= 2 else "Unknown"
            if subcategory == "Bolt":
                return "Bolt AI Development Assistant"
            elif subcategory == "Cline":
                return "Cline AI Code Assistant"
            elif subcategory == "Codex CLI":
                return "Codex CLI Assistant"
            elif subcategory == "RooCode":
                return "RooCode AI Assistant"

    # Fallback to cleaned filename
    title = re.sub(r"[_-]", " ", base_name)
    title = " ".join(word.capitalize() for word in title.split())

    # Add category context if it makes sense
    if category and category != "General":
        if "Prompt" in title:
            title = title.replace("Prompt", f"{category} AI Assistant")
        elif not any(word in title.lower() for word in ["assistant", "agent", "ai"]):
            title = f"{title} - {category}"

    return title


def get_category_from_path(file_path):
    """Extract category from the file path."""
    path_parts = Path(file_path).parts
    # Find the examples directory and get the next part
    try:
        examples_index = path_parts.index("examples")
        if examples_index + 1 < len(path_parts):
            return path_parts[examples_index + 1]
    except ValueError:
        pass
    return "General"


def get_open_source_specific_title(file_path):
    """Get specific title for Open Source prompts based on subdirectory."""
    path_parts = Path(file_path).parts
    try:
        examples_index = path_parts.index("examples")
        if examples_index + 2 < len(path_parts):
            subcategory = path_parts[examples_index + 2]
            if subcategory == "Bolt":
                return "Bolt AI Development Assistant"
            elif subcategory == "Cline":
                return "Cline AI Code Assistant"
            elif subcategory == "Codex CLI":
                return "Codex CLI Assistant"
            elif subcategory == "RooCode":
                return "RooCode AI Assistant"
    except (ValueError, IndexError):
        pass
    return None


def read_prompt_file(file_path):
    """Read the content of a prompt file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None


def import_prompt_to_db(random_val, username, title, prompt_content, tag):
    """Import a single prompt to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO community (random_val, username, tittle, prompt, tag)
            VALUES (?, ?, ?, ?, ?)
        """,
            (random_val, username, title, prompt_content, tag),
        )

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"  ⚠️  Skipping {title} - already exists (random_val: {random_val})")
        return False
    except Exception as e:
        print(f"  ❌ Error importing {title}: {e}")
        return False
    finally:
        conn.close()


def find_prompt_files(examples_dir):
    """Find all prompt files in the examples directory."""
    prompt_files = []
    examples_path = Path(examples_dir)

    if not examples_path.exists():
        print(f"❌ Examples directory not found: {examples_dir}")
        return prompt_files

    # Supported prompt file extensions
    prompt_extensions = [".txt", ".md", ".json"]

    for root, dirs, files in os.walk(examples_path):
        for file in files:
            if any(file.endswith(ext) for ext in prompt_extensions):
                file_path = os.path.join(root, file)
                prompt_files.append(file_path)

    return prompt_files


def main():
    """Main function to import all examples to the database."""
    print("🚀 Starting import of examples to query.db...")

    # Create the database table
    create_community_table()

    # Find all prompt files
    examples_dir = "/home/azzar/project/prompt-sanctuary/web/examples"
    prompt_files = find_prompt_files(examples_dir)

    if not prompt_files:
        print("❌ No prompt files found in examples directory")
        return

    print(f"📁 Found {len(prompt_files)} prompt files to import")

    # Import each file
    imported_count = 0
    skipped_count = 0

    for file_path in prompt_files:
        # Read the prompt content
        prompt_content = read_prompt_file(file_path)
        if prompt_content is None:
            skipped_count += 1
            continue

        # Generate metadata
        filename = os.path.basename(file_path)
        category = get_category_from_path(file_path)

        # Generate appropriate title
        if category == "Open Source prompts":
            title = get_open_source_specific_title(file_path)
            if not title:
                title = generate_appropriate_title(filename, category, file_path)
        else:
            title = generate_appropriate_title(filename, category, file_path)

        random_val = generate_random_val()

        # Use category as username for examples
        username = f"examples_{category.lower().replace(' ', '_')}"

        print(f"📝 Importing: {title} (Category: {category})")

        # Import to database
        if import_prompt_to_db(random_val, username, title, prompt_content, category):
            imported_count += 1
        else:
            skipped_count += 1

    print("\n✅ Import completed!")
    print(f"   📊 Imported: {imported_count} prompts")
    print(f"   ⏭️  Skipped: {skipped_count} prompts")
    print(f"   📁 Total processed: {len(prompt_files)} files")

    # Show summary by category
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT tag, COUNT(*) as count FROM community GROUP BY tag ORDER BY count DESC")
    results = cursor.fetchall()

    print("\n📈 Summary by category:")
    for row in results:
        print(f"   {row['tag']}: {row['count']} prompts")

    conn.close()


if __name__ == "__main__":
    main()
