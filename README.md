# My Small Tools

This repository hosts a collection of small, useful tools. Currently, it 
includes:
- **MMEX Kivy Reader**: A Kivy-based desktop application for reading and 
  displaying financial transactions from a MoneyManagerEx (MMEX) SQLite database 
  file. (See section 1)
- **Bookmarklets Project**: A collection of useful browser bookmarklets. (See 
  section 2)

## 1. MMEX Kivy Reader

### Description

The MMEX Kivy Reader is a simple Python application built with the Kivy 
framework. It allows users to connect to an MMEX SQLite database (`.mmb` or 
`.mmdf` file), specify a date range, and view financial transactions. 
Transactions can be viewed for all accounts combined or filtered per individual 
account in separate tabs. The application supports custom fonts for displaying 
non-ASCII characters.

For detailed information on features, prerequisites, setup, usage, and 
troubleshooting, please refer to the MMEX Kivy Reader specific README.

### Companion CLI Tool

A command-line utility (`mmex_reader.py`) is also available within the 
`mmex_reader` directory. This tool offers basic interactions with the MMEX 
database, such as listing tables or querying transactions directly to the 
console. For detailed setup and usage instructions for the CLI tool, please 
refer to the dedicated README in the mmex_reader directory.

## 2. Bookmarklets Project

### Description



### Location

The bookmarklets can be found in the `bookmarklets/` directory (or specify the 
correct path).

### Usage



## Contributing

Contributions to `my_small_tools` are welcome! Feel free to fork the project, 
make improvements, and submit pull requests. If you're adding a new tool, please 
consider adding a section for it in this README and providing its own detailed 
README if necessary.

---

*This README will be updated as more tools are added to the repository.*