# GUI Usage Guide

## AniList to MariaDB Backup - Graphical User Interface

This GUI application provides a user-friendly interface for all the backup operations available in the command-line scripts.

### Prerequisites

1. **Python 3.9+** installed on your system
2. **MariaDB/MySQL** database server running
3. **PyQt6** and other dependencies installed (see Installation)

### Installation

1. Install all required dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your database credentials:
   - Copy `api_keys_template.py` to `api_keys.py`
   - Edit `api_keys.py` and fill in your database credentials:
     ```python
     user_name = "your_database_user"
     db_password = "your_database_password"
     host_name = "localhost"  # or your database server IP
     db_name = "your_database_name"
     ```

### Running the GUI

Launch the application with:
```bash
python gui_main.py
```

### Using the GUI

![GUI Screenshot](https://github.com/user-attachments/assets/95b134bc-9104-406b-b3ee-8b538b01f93f)

#### 1. Database Configuration
- The top section displays your current database configuration
- Configuration is loaded from `api_keys.py`
- Verify that the connection details are correct before starting any operation

#### 2. AniList User
- Choose between **User ID** or **Username**
  - **User ID**: If you know your AniList user ID (numeric)
  - **Username**: If you prefer to use your AniList username (the app will fetch your ID automatically)
- Enter your AniList User ID or Username in the input field

#### 3. Operation Selection
Choose one of four available operations:

- **Full Anime List Backup**: Downloads your complete anime list from AniList
  - Creates the `anime_list2` table if it doesn't exist
  - Adds new entries and updates existing ones
  - Best for initial backup or complete synchronization

- **Full Manga List Backup**: Downloads your complete manga list from AniList
  - Creates the `manga_list` table if it doesn't exist
  - Adds new entries and updates existing ones
  - Best for initial backup or complete synchronization

- **Update Recent Anime**: Updates only recently modified anime entries
  - Requires `anime_list` table to exist (run full backup first)
  - Faster than full backup
  - Fetches only the 50 most recently updated entries
  - Best for daily/regular updates

- **Update Recent Manga**: Updates only recently modified manga entries
  - Requires `manga_list` table to exist (run full backup first)
  - Faster than full backup
  - Fetches only the 50 most recently updated entries
  - Best for daily/regular updates

#### 4. Running an Operation

1. Fill in your AniList User ID or Username
2. Select the desired operation
3. Click the **Start** button
4. Monitor progress in the Log Output area
5. The operation can be stopped at any time using the **Stop** button

#### 5. Log Output
- The log area displays real-time progress
- Color-coded messages:
  - **Green**: Success messages, table creation, completion
  - **Blue**: Processing information, record updates
  - **Magenta**: New records added
  - **Cyan**: Status messages, page fetching
  - **Yellow**: Summary statistics
  - **Red**: Errors or warnings

### Features

- **Non-blocking UI**: Operations run in background threads, keeping the interface responsive
- **Real-time logging**: See exactly what's happening during the backup process
- **Stop capability**: Cancel operations at any time
- **Automatic user ID fetching**: When using username, the app automatically fetches your user ID
- **Progress tracking**: Visual feedback during long operations
- **Error handling**: Clear error messages if something goes wrong

### Troubleshooting

**"Please configure api_keys.py"**
- Make sure you've created `api_keys.py` from `api_keys_template.py`
- Verify all fields are filled in correctly

**"Could not fetch user ID from username"**
- Check your internet connection
- Verify the username is spelled correctly
- Make sure the username exists on AniList

**"Table doesn't exist"**
- For "Update Recent" operations, you must run a "Full Backup" first
- This creates the necessary database tables

**Database connection errors**
- Verify your MariaDB/MySQL server is running
- Check that the credentials in `api_keys.py` are correct
- Ensure the database exists
- Verify network connectivity to the database server

### Tips

1. **First time users**: Start with a Full Backup operation to create tables and populate initial data
2. **Regular updates**: Use "Update Recent" operations for faster daily synchronization
3. **Multiple lists**: You can backup both anime and manga lists independently
4. **Monitor logs**: Keep an eye on the log output for any issues or statistics

### Command-Line Alternative

If you prefer using the command line, the original scripts are still available:
- `take_full_anime_list.py` - Full anime backup
- `take_full_manga_list.py` - Full manga backup
- `update_only_anime.py` - Update recent anime
- `update_only_manga.py` - Update recent manga

The GUI provides the same functionality with a more user-friendly interface.
