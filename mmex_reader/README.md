# MMEX Kivy Reader

A simple Kivy-based Python application to read and display financial 
transactions from a MoneyManagerEx (MMEX) `.mmb` database file.

## Features

- Connects to an MMEX SQLite database.
- Allows users to specify a date range for querying transactions.
- Displays transactions in a clear, aligned grid format, including:
  - Date
  - Account Name
  - Payee
  - Category
  - Notes
  - Amount
- Configurable font for displaying data, supporting non-English characters.
- Basic error handling for database connection and queries.

## Prerequisites

- Python 3.x
- Kivy framework (version 2.1.0 or as specified in `mmex_kivy_app.py`)
- Pandas library
- python-dotenv library

## Setup

1. **Clone the repository (or ensure you have the `my_small_tools` project).**

2. **Install Dependencies:**
   Navigate to the root directory of the `my_small_tools` project (or where 
   your Python environment is managed) and install the required Python packages:

   ```bash
   pip install kivy pandas python-dotenv
   ```

   *(Note: Kivy installation can sometimes be more involved depending on your 
   operating system. Please refer to the official Kivy installation guide if you 
   encounter issues.)*

3. **Prepare the Font:**
   - This application requires a font file capable of displaying the characters 
     present in your MMEX database (especially if you use non-English languages).
   - The application is currently configured to look for `NotoSansCJKtc-Regular.
     otf` inside a `fonts` subdirectory within the `mmex_reader` directory 
     (`mmex_reader/fonts/`).
   - **Action:**
     1. Create a directory named `fonts` inside the `mmex_reader` directory.
     2. Download a suitable Unicode font. For example, 
        `NotoSansCJKtc-Regular.otf` (for Traditional Chinese, Japanese, Korean 
        support) can be found via Google Noto Fonts.
     3. Place the downloaded `.otf` or `.ttf` font file into the 
        `mmex_reader/fonts/` directory.
     4. If you use a different font file name or location, update the 
        `UNICODE_FONT_PATH` variable at the top of `mmex_kivy_app.py`.

4. **Configure Database Path:**
   - Create a file named `.env` in the `mmex_reader` directory (i.e., 
     `mmex_reader/.env`).
   - Add the following line to the `.env` file, replacing 
     `path/to/your/database.mmb` with the actual absolute path to your 
     MoneyManagerEx `.mmb` database file:

     ```bash
     DB_FILE_PATH="path/to/your/database.mmb"
     ```

     **Example:**

     ```bash
     DB_FILE_PATH="C:/Users/YourUser/Documents/Finances/mymoney.mmb"
     ```

     or on Linux/macOS:

     ```bash
     DB_FILE_PATH="/home/youruser/Documents/Finances/mymoney.mmb"
     ```

## Running the Application

1. Navigate to the `mmex_reader` directory in your terminal:
   ```bash
   cd path/to/my_small_tools/mmex_reader
   ```
2. Run the Python script:
   ```bash
   python mmex_kivy_app.py
   ```
    
## Command-Line Utility (`mmex_reader.py`)

This directory also includes `mmex_reader.py`, a command-line script for basic 
interactions with the MMEX database.

**Features:**
- Connects to the database specified in `.env`.
- Lists all database tables.
- Prints sample data from the account list table.
- Queries and prints transactions to the console based on a hardcoded date range 
  within the script.

**Running `mmex_reader.py`:**
1. Ensure Python dependencies (`pandas`, `python-dotenv`) are installed and the 
   `.env` file is configured as described in the main **Setup** section.
2. Navigate to the `mmex_reader` directory.
3. Execute:
   ```bash
   python mmex_reader.py
   ```
   *Note: To change the query date range for this script, you must edit the 
   `START_DATE_STR` and `END_DATE_STR` variables directly in `mmex_reader.py`.*

## MMEX Database Schema

Both `mmex_kivy_app.py` (the GUI application) and `mmex_reader.py` (the 
command-line utility) interact with the MMEX database and make assumptions about 
its schema (table and field names).

- **`mmex_kivy_app.py`**: Uses configurable constants defined at the top of the 
  script (e.g., `DB_TABLE_TRANSACTIONS`, `DB_FIELD_TRANS_DATE`) to refer to MMEX 
  database table and field names.
- **`mmex_reader.py`**: Currently uses hardcoded table and field names (e.g., 
  `CHECKINGACCOUNT_V1`, `TRANSDATE`) directly within its SQL query strings.

These are currently set for a common version of the MMEX schema. If you are 
using an MMEX version with a significantly altered schema, you may need to 
update the constants in `mmex_kivy_app.py` and/or the hardcoded names in 
`mmex_reader.py` to match your database structure.

## Contributing

Feel free to fork the project and submit pull requests for improvements or bug 
fixes.
