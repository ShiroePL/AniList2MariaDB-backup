# AniList to MariaDB Backup
This Python application allows you to back up your anime and manga lists from the [AniList] website to a local MariaDB database. The program offers two main functionalities:
1. **Full Backup**: Backs up your complete list of anime/manga.
2. **Recent Update**: Automatically updates the list, adding or changing anime/manga entries until it detects that there are no more new or recently updated items to add.
   
### Screenshots
#### Full Backup
<table>
  <tr>
    <td><img src="screenshots/full_backup_1.png" width="550"></td>
    <td><img src="screenshots/full_backup_2.png" width="550"></td>
  </tr>
</table>

#### Recent Update
<table>
  <tr>
    <td><img src="screenshots/update_only_1.png" width="450"></td>
    <td><img src="screenshots/update_only_2.png" width="450"></td>
  </tr>
</table>

### Instructions
**Setup**
1. **Configure API Keys**: Rename the file ```api_keys_template.py``` to ```api_keys.py``` and populate it with your credentials:
    ```python
    # MariaDB Configuration
    user_name = ""
    db_password = ""
    host_name = ""  # IP of MariaDB instance
    db_name = ""
    ```

2. **Install Dependencies**: This has been tested on Python 3.9.0. To install the necessary packages, run:
   ```bash 
   pip install -r requirements.txt
### Usage
To run the program, execute one of the following scripts:
* Full Anime List Backup::
  ```bash
  python  take_full_anime_list.py
* Full Manga List Backup:
  ```bash
  python  take_full_manga_list.py
* Recent Anime List Update:
  ```bash
  python  update_only_anime.py
* Recent Manga List Update:
  ```bash
  python  update_only_manga.py

**Links**

[Anilist] : https://anilist.co/home

[Anilist]: https://anilist.co/home