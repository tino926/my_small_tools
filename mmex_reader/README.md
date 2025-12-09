# MMEX Kivy Reader

A comprehensive Kivy-based Python application for reading, analyzing, and visualizing financial transactions from MoneyManagerEx (MMEX) `.mmb` database files. This application provides both GUI and command-line interfaces with advanced features for financial data management.

## Features

### Core Functionality
- **Database Connection**: Connects to MMEX SQLite databases with connection pooling for optimal performance
- **Date Range Filtering**: Flexible date range selection with date picker widgets
- **Multi-Account Support**: View transactions across all accounts or filter by specific accounts in dedicated tabs
- **Transaction Management**: View, edit, update, and delete transactions with detailed popup interfaces

### Advanced UI Features
- **Search & Filter**: Real-time search across multiple fields (payee, category, notes, tags) with advanced filtering options
- **Data Visualization**: Interactive charts and graphs including:
  - Spending by category (pie charts)
  - Spending over time (line charts)
  - Income vs expenses comparison
  - Top payees analysis
- **Sortable Columns**: Click column headers to sort transactions in ascending/descending order
- **Responsive Layout**: Automatically adapts to different screen sizes with mobile, tablet, and desktop layouts
- **Account Balance Tracking**: Real-time balance calculations for each account
- **Keyboard Shortcuts**: Press `ESC` to dismiss popups for quicker navigation

### Technical Features
- **Modular Architecture**: Clean separation of concerns with dedicated modules:
  - `db_utils.py`: Database operations and connection pooling with optimized SQL queries
  - `ui_components.py`: Reusable UI components and widgets with consistent styling
  - `visualization.py`: Chart generation and data visualization with enhanced income/expense analysis
  - `error_handling.py`: Centralized error handling and validation with detailed logging
  - `config_manager.py`: Configuration management with validation
  - `kv_components.py`: Kivy language compatible components
- **Performance Optimized**: Eliminates N+1 queries, uses SQL aggregation, and implements efficient data loading
- **Caching**: Caches transaction results to accelerate repeated loads and pagination
- **Unicode Support**: Configurable fonts for displaying international characters
- **Robust Error Handling**: Comprehensive error handling with user-friendly feedback and detailed error logging

## Prerequisites

- Python 3.x
- Required Python packages:
  - Kivy framework (version 2.1.0 or higher)
  - Pandas library for data manipulation
  - Matplotlib for data visualization
  - python-dotenv for environment configuration
  - Kivy Garden matplotlib backend for chart integration

## Setup

1. **Clone the repository (or ensure you have the `my_small_tools` project).**

2. **Install Dependencies:**
   Navigate to the root directory of the `my_small_tools` project (or where 
   your Python environment is managed) and install the required Python packages:

   ```bash
   pip install kivy pandas matplotlib python-dotenv
   pip install kivy-garden
   garden install matplotlib
   ```

   *(Note: Kivy installation can sometimes be more involved depending on your 
   operating system. Please refer to the official Kivy installation guide if 
   you encounter issues. The matplotlib garden package is required for chart visualization features.)*

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

### GUI Application

1. Navigate to the `mmex_reader` directory in your terminal:

   ```bash
   cd path/to/my_small_tools/mmex_reader
   ```

2. Run the main application:

   ```bash
   python mmex_kivy_app.py
   ```

### Application Usage

Once the application starts, you can:

- **Set Date Range**: Use the date picker buttons to select start and end dates for transaction queries
- **Search Transactions**: Use the search box to filter transactions by payee, category, notes, or tags
- **Filter by Type**: Use the filter dropdown to show only income, expenses, or transfers
- **Sort Data**: Click on column headers to sort transactions by that field
- **View by Account**: Switch between the "All Transactions" tab and individual account tabs
- **Visualize Data**: Click the "Charts" tab to view spending analysis and trends
- **Edit Transactions**: Click on any transaction row to view details and make edits
- **Account Balances**: View real-time account balances in each account tab
    
## Command-Line Utility (`mmex_reader.py`)

This directory also includes `mmex_reader.py`, a command-line script for basic 
interactions with the MMEX database.

**Features:**

- Connects to the database specified in `.env`.
- Lists all database tables.
- Prints sample data from the account list table.
- Queries and prints transactions to the console based on a hardcoded date 
  range within the script.

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

### Command-Line Options

`mmex_reader.py` 支援以下參數以改善命令列使用體驗：

- `--start-date YYYY-MM-DD`：設定交易查詢起始日期（預設來自環境變數 `MMEX_START_DATE`）。
- `--end-date YYYY-MM-DD`：設定交易查詢結束日期（預設來自環境變數 `MMEX_END_DATE`）。
- `--db-path <path>`：指定 `.mmb` 資料庫檔案路徑，優先於 `.env` 的 `DB_FILE_PATH`。
- `--no-schema`：不顯示資料庫結構。
- `--no-transactions`：不顯示交易資料。

範例：

```bash
python mmex_reader.py --db-path "C:/data/mymoney.mmb" --start-date 2025-01-01 --end-date 2025-05-31
```

顯示說明：

```bash
python mmex_reader.py --help
```

## MMEX Database Schema

The application interacts with MMEX database schema and is designed to work with standard MMEX database structures. The modular architecture allows for easy adaptation to different schema versions:

- **`mmex_kivy_app.py`**: Main application with configurable database constants
- **`db_utils.py`**: Database utility functions with schema constants and connection pooling
- **Schema Flexibility**: Constants can be easily updated to match different MMEX versions

Key database tables used:
- `CHECKINGACCOUNT_V1`: Transaction records
- `ACCOUNTLIST_V1`: Account information and balances  
- `PAYEE_V1`: Payee/recipient information
- `CATEGORY_V1` & `SUBCATEGORY_V1`: Transaction categorization
- `TAG_V1` & `TAGLINK_V1`: Transaction tagging system

If you are using an MMEX version with a different schema, you can update the constants in `db_utils.py` to match your database structure.

## Contributing

We welcome contributions to improve the MMEX Kivy Reader! Here are some ways you can contribute:

### Current Architecture
The application follows a modular design pattern:
- **Database Layer** (`db_utils.py`): Handles all database operations with connection pooling and optimized SQL queries
- **UI Layer** (`ui_components.py`): Reusable UI components and widgets with consistent styling  
- **Visualization Layer** (`visualization.py`): Chart generation and data visualization with enhanced income/expense analysis
- **Error Handling** (`error_handling.py`): Centralized error management with detailed logging
- **Configuration Layer** (`config_manager.py`): Configuration management with validation
- **Kivy Components** (`kv_components.py`): Kivy language compatible components
- **Main Application** (`mmex_kivy_app.py`): Application logic and coordination

### Areas for Contribution
- Performance optimizations and caching improvements (ongoing improvements in progress)
- Additional chart types and visualization options
- Enhanced mobile responsiveness
- Export functionality (CSV, PDF)
- Additional database schema support
- UI/UX improvements and accessibility features
- Asynchronous data loading for better user experience
- Summary statistics and budget tracking features

Feel free to fork the project and submit pull requests for improvements or bug fixes. Please ensure your code follows the existing modular architecture and includes appropriate error handling.
