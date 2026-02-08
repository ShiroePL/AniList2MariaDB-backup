import sys
import json
import time
import requests
import mysql.connector
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                              QRadioButton, QButtonGroup, QTextEdit, QComboBox,
                              QProgressBar, QGroupBox, QMessageBox, QTabWidget)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QTextCursor, QFont
import api_keys


class WorkerThread(QThread):
    """Worker thread for background operations"""
    progress_update = pyqtSignal(int)
    log_message = pyqtSignal(str, str)  # message, color
    finished = pyqtSignal(str)
    
    def __init__(self, operation_type, user_id, db_config):
        super().__init__()
        self.operation_type = operation_type
        self.user_id = user_id
        self.db_config = db_config
        self.is_running = True
        
    def run(self):
        """Execute the selected operation"""
        try:
            if self.operation_type == "full_anime":
                self.full_backup_anime()
            elif self.operation_type == "full_manga":
                self.full_backup_manga()
            elif self.operation_type == "update_anime":
                self.update_only_anime()
            elif self.operation_type == "update_manga":
                self.update_only_manga()
        except Exception as e:
            self.log_message.emit(f"Error: {str(e)}", "red")
            self.finished.emit(f"Failed: {str(e)}")
        
    def stop(self):
        """Stop the worker thread"""
        self.is_running = False
        
    def full_backup_anime(self):
        """Full anime list backup"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check if table exists, create if not
            check_if_table_exists = "SHOW TABLES LIKE 'anime_list2'"
            cursor.execute(check_if_table_exists)
            result = cursor.fetchone()
            
            if not result:
                self.log_message.emit("Creating anime_list2 table...", "yellow")
                create_table_query = """CREATE TABLE `anime_list2` (
                `id_default` int(5) NOT NULL AUTO_INCREMENT,
                `id_anilist` int(11) NOT NULL,
                `id_mal` int(11) DEFAULT NULL,
                `title_english` varchar(255) DEFAULT NULL,
                `title_romaji` varchar(255) DEFAULT NULL,
                `on_list_status` varchar(255) DEFAULT NULL,
                `air_status` varchar(255) DEFAULT NULL,
                `media_format` varchar(255) DEFAULT NULL,
                `season_year` text DEFAULT NULL,
                `season_period` text DEFAULT NULL,
                `all_episodes` int(11) DEFAULT NULL,
                `episodes_progress` int(11) DEFAULT NULL,
                `score` float DEFAULT NULL,
                `rewatched_times` int(11) DEFAULT NULL,
                `cover_image` varchar(255) DEFAULT NULL,
                `is_favourite` varchar(10) DEFAULT '0',
                `anilist_url` varchar(255) DEFAULT NULL,
                `mal_url` varchar(255) DEFAULT NULL,
                `last_updated_on_site` timestamp NULL DEFAULT NULL,
                `entry_createdAt` timestamp NULL DEFAULT NULL,
                `user_stardetAt` text DEFAULT 'not started',
                `user_completedAt` text DEFAULT 'not completed',
                `notes` text DEFAULT NULL,
                `description` text DEFAULT NULL,
                PRIMARY KEY (`id_default`)
                ) ENGINE=InnoDB AUTO_INCREMENT=1297 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"""
                cursor.execute(create_table_query)
                self.log_message.emit("Table created successfully", "green")
            else:
                self.log_message.emit("Table anime_list2 exists", "green")
            
            # Get all records
            take_all_records = "select id_anilist, last_updated_on_site from anime_list2"
            cursor.execute(take_all_records)
            all_records = cursor.fetchall()
            self.log_message.emit(f"Total records in table: {len(all_records)}", "blue")
            
            # Fetch data from AniList
            page = 1
            has_next_page = True
            total_updated = 0
            total_added = 0
            how_many_anime_in_one_request = 50
            
            while has_next_page and self.is_running:
                variables_in_api = {
                    'page': page,
                    'perPage': how_many_anime_in_one_request,
                    'userId': int(self.user_id)
                }
                
                api_request = '''
                    query ($page: Int, $perPage: Int, $userId: Int) {
                Page(page: $page, perPage: $perPage) {
                pageInfo {
                perPage
                currentPage
                lastPage
                hasNextPage
                }
                mediaList(userId: $userId, type: ANIME) {
                status
                mediaId
                score
                progress
                repeat
                updatedAt
                createdAt
                startedAt {
                    year
                    month
                    day
                }
                completedAt {
                    year
                    month
                    day
                }
                media {
                    title {
                    romaji
                    english
                    }
                    idMal
                    format
                    status
                    description
                    seasonYear
                    season
                    episodes
                    coverImage {
                    large
                    }
                    isFavourite
                    siteUrl
                }
                notes
                    }
                }
                }
                    '''
                
                url = 'https://graphql.anilist.co'
                response_from_anilist = requests.post(url, json={'query': api_request, 'variables': variables_in_api})
                parsed_json = json.loads(response_from_anilist.text)
                
                self.log_message.emit(f"Fetching page {page}...", "cyan")
                
                has_next_page = parsed_json["data"]["Page"]["pageInfo"]["hasNextPage"]
                
                for j in range(len(parsed_json["data"]["Page"]["mediaList"])):
                    if not self.is_running:
                        break
                        
                    media_data = parsed_json["data"]["Page"]["mediaList"][j]
                    
                    mediaId_parsed = media_data["mediaId"]
                    score_parsed = media_data["score"]
                    progress_parsed = media_data["progress"]
                    repeat_parsed = media_data["repeat"]
                    on_list_status_parsed = media_data["status"]
                    updatedAt_parsed = media_data["updatedAt"]
                    entry_createdAt_parsed = media_data["createdAt"]
                    notes_parsed = media_data["notes"]
                    
                    # Media info
                    media = media_data["media"]
                    english_parsed = media["title"]["english"]
                    romaji_parsed = media["title"]["romaji"]
                    idMal_parsed = media["idMal"] if media["idMal"] else 0
                    format_parsed = media["format"]
                    air_status_parsed = media["status"]
                    seasonYear_parsed = media["seasonYear"]
                    season_period_parsed = media["season"]
                    episodes_parsed = media["episodes"] if media["episodes"] else 0
                    large_parsed = media["coverImage"]["large"]
                    isFavourite_parsed = "1" if media["isFavourite"] else "0"
                    siteUrl_parsed = media["siteUrl"]
                    description_parsed = media["description"]
                    
                    # User dates
                    user_startedAt = media_data["startedAt"]
                    user_completedAt = media_data["completedAt"]
                    
                    # Clean strings
                    cleaned_english = str(english_parsed).replace("'", '"') if english_parsed else ""
                    cleaned_romaji = str(romaji_parsed).replace("'", '"')
                    cleaned_notes = str(notes_parsed).replace("'", '"') if notes_parsed else ""
                    cleaned_description = str(description_parsed).replace("<br><br>", '<br>').replace("'", '"') if description_parsed else ""
                    mal_url_parsed = f"https://myanimelist.net/anime/{idMal_parsed}"
                    
                    # Format dates
                    user_startedAt_parsed = f"{user_startedAt['year']}-{user_startedAt['month']}-{user_startedAt['day']}"
                    user_completedAt_parsed = f"{user_completedAt['year']}-{user_completedAt['month']}-{user_completedAt['day']}"
                    user_startedAt_parsed = user_startedAt_parsed.replace('None-None-None', 'not started')
                    user_completedAt_parsed = user_completedAt_parsed.replace('None-None-None', 'not completed')
                    
                    # Check if record exists
                    check_record_query = "SELECT * FROM anime_list2 WHERE id_anilist = %s"
                    cursor.execute(check_record_query, (mediaId_parsed,))
                    record = cursor.fetchone()
                    
                    # Convert timestamp
                    updatedAt_datetime = datetime.fromtimestamp(updatedAt_parsed) if updatedAt_parsed else None
                    updatedAt_str = updatedAt_datetime.strftime('%Y-%m-%d %H:%M:%S') if updatedAt_datetime else None
                    
                    entry_createdAt_datetime = datetime.fromtimestamp(entry_createdAt_parsed) if entry_createdAt_parsed else None
                    entry_createdAt_str = entry_createdAt_datetime.strftime('%Y-%m-%d %H:%M:%S') if entry_createdAt_datetime else None
                    
                    if record:
                        # Update existing record
                        if record[18] is not None:
                            db_timestamp = int(time.mktime(record[18].timetuple()))
                        else:
                            db_timestamp = None
                        
                        updatedAt_timestamp = int(time.mktime(updatedAt_datetime.timetuple())) if updatedAt_datetime else None
                        
                        if db_timestamp != updatedAt_timestamp:
                            update_query = """UPDATE `anime_list2` SET  
                                id_mal = %s,
                                title_english = %s,
                                title_romaji = %s,
                                on_list_status = %s,
                                air_status = %s,
                                media_format = %s,
                                season_year = %s,
                                season_period = %s,
                                all_episodes = %s,
                                episodes_progress = %s,
                                score = %s,
                                rewatched_times = %s,
                                cover_image = %s,
                                is_favourite = %s,
                                anilist_url = %s,
                                mal_url = %s,
                                last_updated_on_site = %s,
                                entry_createdAt = %s,
                                user_stardetAt = %s,
                                user_completedAt = %s,
                                notes = %s,
                                description = %s
                                WHERE id_anilist = %s
                                """
                            
                            cursor.execute(update_query, (idMal_parsed, cleaned_english, cleaned_romaji, 
                                                        on_list_status_parsed, air_status_parsed, format_parsed, 
                                                        seasonYear_parsed, season_period_parsed, episodes_parsed, 
                                                        progress_parsed, score_parsed, repeat_parsed, 
                                                        large_parsed, isFavourite_parsed, siteUrl_parsed, 
                                                        mal_url_parsed, updatedAt_str, entry_createdAt_str,
                                                        user_startedAt_parsed, user_completedAt_parsed, 
                                                        cleaned_notes, cleaned_description, mediaId_parsed))
                            total_updated += 1
                            self.log_message.emit(f"Updated: {cleaned_romaji}", "blue")
                    else:
                        # Insert new record
                        insert_query = """INSERT INTO `anime_list2`(`id_anilist`, `id_mal`, `title_english`, `title_romaji`, 
                        `on_list_status`, `air_status`, `media_format`, `season_year`, `season_period`, `all_episodes`, 
                        `episodes_progress`, `score`,`rewatched_times`, `cover_image`, `is_favourite`, `anilist_url`, 
                        `mal_url`, `last_updated_on_site`, `entry_createdAt`, `user_stardetAt`, `user_completedAt`, 
                        `notes`, `description`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        %s, %s, %s, %s, %s, %s, %s)
                        """
                        
                        cursor.execute(insert_query, (mediaId_parsed, idMal_parsed, cleaned_english, cleaned_romaji,
                                                     on_list_status_parsed, air_status_parsed, format_parsed, 
                                                     seasonYear_parsed, season_period_parsed, episodes_parsed,
                                                     progress_parsed, score_parsed, repeat_parsed, large_parsed,
                                                     isFavourite_parsed, siteUrl_parsed, mal_url_parsed, 
                                                     updatedAt_str, entry_createdAt_str, user_startedAt_parsed,
                                                     user_completedAt_parsed, cleaned_notes, cleaned_description))
                        total_added += 1
                        self.log_message.emit(f"Added: {cleaned_romaji}", "magenta")
                
                conn.commit()
                page += 1
            
            cursor.close()
            conn.close()
            
            self.log_message.emit(f"Total added: {total_added}", "yellow")
            self.log_message.emit(f"Total updated: {total_updated}", "yellow")
            self.finished.emit(f"Completed! Added: {total_added}, Updated: {total_updated}")
            
        except Exception as e:
            self.log_message.emit(f"Error in full_backup_anime: {str(e)}", "red")
            self.finished.emit(f"Failed: {str(e)}")
    
    def full_backup_manga(self):
        """Full manga list backup - similar to anime but for manga"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check if table exists, create if not
            check_if_table_exists = "SHOW TABLES LIKE 'manga_list'"
            cursor.execute(check_if_table_exists)
            result = cursor.fetchone()
            
            if not result:
                self.log_message.emit("Creating manga_list table...", "yellow")
                create_table_query = """CREATE TABLE `manga_list` (
                `id_default` int(5) NOT NULL AUTO_INCREMENT,
                `id_anilist` int(11) NOT NULL,
                `id_mal` int(11) DEFAULT NULL,
                `title_english` varchar(255) DEFAULT NULL,
                `title_romaji` varchar(255) DEFAULT NULL,
                `on_list_status` varchar(255) DEFAULT NULL,
                `publish_status` varchar(255) DEFAULT NULL,
                `media_format` varchar(255) DEFAULT NULL,
                `start_year` text DEFAULT NULL,
                `all_chapters` int(11) DEFAULT NULL,
                `chapters_progress` int(11) DEFAULT NULL,
                `all_volumes` int(11) DEFAULT NULL,
                `volumes_progress` int(11) DEFAULT NULL,
                `score` float DEFAULT NULL,
                `reread_times` int(11) DEFAULT NULL,
                `cover_image` varchar(255) DEFAULT NULL,
                `is_favourite` varchar(10) DEFAULT '0',
                `anilist_url` varchar(255) DEFAULT NULL,
                `mal_url` varchar(255) DEFAULT NULL,
                `last_updated_on_site` timestamp NULL DEFAULT NULL,
                `entry_createdAt` timestamp NULL DEFAULT NULL,
                `user_stardetAt` text DEFAULT 'not started',
                `user_completedAt` text DEFAULT 'not completed',
                `notes` text DEFAULT NULL,
                `description` text DEFAULT NULL,
                PRIMARY KEY (`id_default`)
                ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci"""
                cursor.execute(create_table_query)
                self.log_message.emit("Table created successfully", "green")
            else:
                self.log_message.emit("Table manga_list exists", "green")
            
            # Similar implementation to anime but for manga
            page = 1
            has_next_page = True
            total_updated = 0
            total_added = 0
            how_many_manga_in_one_request = 50
            
            while has_next_page and self.is_running:
                variables_in_api = {
                    'page': page,
                    'perPage': how_many_manga_in_one_request,
                    'userId': int(self.user_id)
                }
                
                api_request = '''
                    query ($page: Int, $perPage: Int, $userId: Int) {
                Page(page: $page, perPage: $perPage) {
                pageInfo {
                hasNextPage
                }
                mediaList(userId: $userId, type: MANGA) {
                status
                mediaId
                score
                progress
                progressVolumes
                repeat
                updatedAt
                createdAt
                startedAt {
                    year
                    month
                    day
                }
                completedAt {
                    year
                    month
                    day
                }
                media {
                    title {
                    romaji
                    english
                    }
                    idMal
                    format
                    status
                    description
                    startDate {
                        year
                    }
                    chapters
                    volumes
                    coverImage {
                    large
                    }
                    isFavourite
                    siteUrl
                }
                notes
                    }
                }
                }
                    '''
                
                url = 'https://graphql.anilist.co'
                response_from_anilist = requests.post(url, json={'query': api_request, 'variables': variables_in_api})
                parsed_json = json.loads(response_from_anilist.text)
                
                self.log_message.emit(f"Fetching page {page}...", "cyan")
                
                has_next_page = parsed_json["data"]["Page"]["pageInfo"]["hasNextPage"]
                
                for media_data in parsed_json["data"]["Page"]["mediaList"]:
                    if not self.is_running:
                        break
                    
                    mediaId_parsed = media_data["mediaId"]
                    score_parsed = media_data["score"]
                    progress_parsed = media_data["progress"]
                    progressVolumes_parsed = media_data["progressVolumes"]
                    repeat_parsed = media_data["repeat"]
                    on_list_status_parsed = media_data["status"]
                    updatedAt_parsed = media_data["updatedAt"]
                    entry_createdAt_parsed = media_data["createdAt"]
                    notes_parsed = media_data["notes"]
                    
                    media = media_data["media"]
                    english_parsed = media["title"]["english"]
                    romaji_parsed = media["title"]["romaji"]
                    idMal_parsed = media["idMal"] if media["idMal"] else 0
                    format_parsed = media["format"]
                    publish_status_parsed = media["status"]
                    start_year = media["startDate"]["year"] if media["startDate"]["year"] else None
                    chapters_parsed = media["chapters"] if media["chapters"] else 0
                    volumes_parsed = media["volumes"] if media["volumes"] else 0
                    large_parsed = media["coverImage"]["large"]
                    isFavourite_parsed = "1" if media["isFavourite"] else "0"
                    siteUrl_parsed = media["siteUrl"]
                    description_parsed = media["description"]
                    
                    user_startedAt = media_data["startedAt"]
                    user_completedAt = media_data["completedAt"]
                    
                    cleaned_english = str(english_parsed).replace("'", '"') if english_parsed else ""
                    cleaned_romaji = str(romaji_parsed).replace("'", '"')
                    cleaned_notes = str(notes_parsed).replace("'", '"') if notes_parsed else ""
                    cleaned_description = str(description_parsed).replace("<br><br>", '<br>').replace("'", '"') if description_parsed else ""
                    mal_url_parsed = f"https://myanimelist.net/manga/{idMal_parsed}"
                    
                    user_startedAt_parsed = f"{user_startedAt['year']}-{user_startedAt['month']}-{user_startedAt['day']}"
                    user_completedAt_parsed = f"{user_completedAt['year']}-{user_completedAt['month']}-{user_completedAt['day']}"
                    user_startedAt_parsed = user_startedAt_parsed.replace('None-None-None', 'not started')
                    user_completedAt_parsed = user_completedAt_parsed.replace('None-None-None', 'not completed')
                    
                    check_record_query = "SELECT * FROM manga_list WHERE id_anilist = %s"
                    cursor.execute(check_record_query, (mediaId_parsed,))
                    record = cursor.fetchone()
                    
                    updatedAt_datetime = datetime.fromtimestamp(updatedAt_parsed) if updatedAt_parsed else None
                    updatedAt_str = updatedAt_datetime.strftime('%Y-%m-%d %H:%M:%S') if updatedAt_datetime else None
                    
                    entry_createdAt_datetime = datetime.fromtimestamp(entry_createdAt_parsed) if entry_createdAt_parsed else None
                    entry_createdAt_str = entry_createdAt_datetime.strftime('%Y-%m-%d %H:%M:%S') if entry_createdAt_datetime else None
                    
                    if record:
                        if record[19] is not None:
                            db_timestamp = int(time.mktime(record[19].timetuple()))
                        else:
                            db_timestamp = None
                        
                        updatedAt_timestamp = int(time.mktime(updatedAt_datetime.timetuple())) if updatedAt_datetime else None
                        
                        if db_timestamp != updatedAt_timestamp:
                            update_query = """UPDATE `manga_list` SET  
                                id_mal = %s, title_english = %s, title_romaji = %s, on_list_status = %s,
                                publish_status = %s, media_format = %s, start_year = %s, all_chapters = %s,
                                chapters_progress = %s, all_volumes = %s, volumes_progress = %s, score = %s,
                                reread_times = %s, cover_image = %s, is_favourite = %s, anilist_url = %s,
                                mal_url = %s, last_updated_on_site = %s, entry_createdAt = %s,
                                user_stardetAt = %s, user_completedAt = %s, notes = %s, description = %s
                                WHERE id_anilist = %s
                                """
                            
                            cursor.execute(update_query, (idMal_parsed, cleaned_english, cleaned_romaji,
                                                        on_list_status_parsed, publish_status_parsed, format_parsed,
                                                        start_year, chapters_parsed, progress_parsed, volumes_parsed,
                                                        progressVolumes_parsed, score_parsed, repeat_parsed,
                                                        large_parsed, isFavourite_parsed, siteUrl_parsed,
                                                        mal_url_parsed, updatedAt_str, entry_createdAt_str,
                                                        user_startedAt_parsed, user_completedAt_parsed,
                                                        cleaned_notes, cleaned_description, mediaId_parsed))
                            total_updated += 1
                            self.log_message.emit(f"Updated: {cleaned_romaji}", "blue")
                    else:
                        insert_query = """INSERT INTO `manga_list`(`id_anilist`, `id_mal`, `title_english`, `title_romaji`, 
                        `on_list_status`, `publish_status`, `media_format`, `start_year`, `all_chapters`, `chapters_progress`, 
                        `all_volumes`, `volumes_progress`, `score`, `reread_times`, `cover_image`, `is_favourite`, 
                        `anilist_url`, `mal_url`, `last_updated_on_site`, `entry_createdAt`, `user_stardetAt`, 
                        `user_completedAt`, `notes`, `description`) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        
                        cursor.execute(insert_query, (mediaId_parsed, idMal_parsed, cleaned_english, cleaned_romaji,
                                                     on_list_status_parsed, publish_status_parsed, format_parsed,
                                                     start_year, chapters_parsed, progress_parsed, volumes_parsed,
                                                     progressVolumes_parsed, score_parsed, repeat_parsed,
                                                     large_parsed, isFavourite_parsed, siteUrl_parsed,
                                                     mal_url_parsed, updatedAt_str, entry_createdAt_str,
                                                     user_startedAt_parsed, user_completedAt_parsed,
                                                     cleaned_notes, cleaned_description))
                        total_added += 1
                        self.log_message.emit(f"Added: {cleaned_romaji}", "magenta")
                
                conn.commit()
                page += 1
            
            cursor.close()
            conn.close()
            
            self.log_message.emit(f"Total added: {total_added}", "yellow")
            self.log_message.emit(f"Total updated: {total_updated}", "yellow")
            self.finished.emit(f"Completed! Added: {total_added}, Updated: {total_updated}")
            
        except Exception as e:
            self.log_message.emit(f"Error in full_backup_manga: {str(e)}", "red")
            self.finished.emit(f"Failed: {str(e)}")
    
    def update_only_anime(self):
        """Update only recently changed anime"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            take_all_records = "select id_anilist, last_updated_on_site from anime_list"
            try:
                cursor.execute(take_all_records)
                all_records = cursor.fetchall()
                self.log_message.emit(f"Total records in table: {len(all_records)}", "blue")
            except:
                self.log_message.emit("Table anime_list doesn't exist. Please run full backup first.", "red")
                self.finished.emit("Failed: Table doesn't exist")
                return
            
            total_updated = 0
            total_added = 0
            
            variables_in_api = {
                'page': 1,
                'perPage': 50,
                'userId': int(self.user_id)
            }
            
            api_request = '''
                query ($page: Int, $perPage: Int, $userId: Int) {
            Page(page: $page, perPage: $perPage) {
                mediaList(userId: $userId, type: ANIME, sort: UPDATED_TIME_DESC) {
                status
                mediaId
                score
                progress
                repeat
                updatedAt
                createdAt
                startedAt { year month day }
                completedAt { year month day }
                media {
                    title { romaji english }
                    idMal format status description seasonYear season episodes
                    coverImage { large }
                    isFavourite siteUrl
                }
                notes
                }
            }
            }
                '''
            
            url = 'https://graphql.anilist.co'
            response_from_anilist = requests.post(url, json={'query': api_request, 'variables': variables_in_api})
            parsed_json = json.loads(response_from_anilist.text)
            
            for media_data in parsed_json["data"]["Page"]["mediaList"]:
                if not self.is_running:
                    break
                
                mediaId_parsed = media_data["mediaId"]
                score_parsed = media_data["score"]
                progress_parsed = media_data["progress"]
                repeat_parsed = media_data["repeat"]
                on_list_status_parsed = media_data["status"]
                updatedAt_parsed = media_data["updatedAt"]
                entry_createdAt_parsed = media_data["createdAt"]
                notes_parsed = media_data["notes"]
                
                media = media_data["media"]
                english_parsed = media["title"]["english"]
                romaji_parsed = media["title"]["romaji"]
                idMal_parsed = media["idMal"] if media["idMal"] else 0
                format_parsed = media["format"]
                air_status_parsed = media["status"]
                seasonYear_parsed = media["seasonYear"]
                season_period_parsed = media["season"]
                episodes_parsed = media["episodes"] if media["episodes"] else 0
                large_parsed = media["coverImage"]["large"]
                isFavourite_parsed = "1" if media["isFavourite"] else "0"
                siteUrl_parsed = media["siteUrl"]
                description_parsed = media["description"]
                
                user_startedAt = media_data["startedAt"]
                user_completedAt = media_data["completedAt"]
                
                cleaned_english = str(english_parsed).replace("'", '"') if english_parsed else ""
                cleaned_romaji = str(romaji_parsed).replace("'", '"')
                cleaned_notes = str(notes_parsed).replace("'", '"') if notes_parsed else ""
                cleaned_description = str(description_parsed).replace("<br><br>", '<br>').replace("'", '"') if description_parsed else ""
                mal_url_parsed = f"https://myanimelist.net/anime/{idMal_parsed}"
                
                user_startedAt_parsed = f"{user_startedAt['year']}-{user_startedAt['month']}-{user_startedAt['day']}"
                user_completedAt_parsed = f"{user_completedAt['year']}-{user_completedAt['month']}-{user_completedAt['day']}"
                user_startedAt_parsed = user_startedAt_parsed.replace('None-None-None', 'not started')
                user_completedAt_parsed = user_completedAt_parsed.replace('None-None-None', 'not completed')
                
                updatedAt_str = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(updatedAt_parsed)) if updatedAt_parsed else None
                entry_createdAt_str = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(entry_createdAt_parsed)) if entry_createdAt_parsed else None
                
                check_record_query = "SELECT * FROM anime_list WHERE id_anilist = %s"
                cursor.execute(check_record_query, (mediaId_parsed,))
                record = cursor.fetchone()
                
                if record:
                    if record[18] is not None:
                        db_timestamp = int(time.mktime(record[18].timetuple()))
                    else:
                        db_timestamp = None
                    
                    updatedAt_timestamp = int(time.mktime(time.strptime(updatedAt_str, '%Y-%m-%d %H:%M:%S'))) if updatedAt_str else None
                    
                    if db_timestamp != updatedAt_timestamp:
                        update_query = """UPDATE `anime_list` SET  
                            id_mal = %s, title_english = %s, title_romaji = %s, on_list_status = %s,
                            air_status = %s, media_format = %s, season_year = %s, season_period = %s,
                            all_episodes = %s, episodes_progress = %s, score = %s, rewatched_times = %s,
                            cover_image = %s, is_favourite = %s, anilist_url = %s, mal_url = %s,
                            last_updated_on_site = %s, entry_createdAt = %s, user_stardetAt = %s,
                            user_completedAt = %s, notes = %s, description = %s
                            WHERE id_anilist = %s
                            """
                        
                        cursor.execute(update_query, (idMal_parsed, cleaned_english, cleaned_romaji,
                                                     on_list_status_parsed, air_status_parsed, format_parsed,
                                                     seasonYear_parsed, season_period_parsed, episodes_parsed,
                                                     progress_parsed, score_parsed, repeat_parsed,
                                                     large_parsed, isFavourite_parsed, siteUrl_parsed,
                                                     mal_url_parsed, updatedAt_str, entry_createdAt_str,
                                                     user_startedAt_parsed, user_completedAt_parsed,
                                                     cleaned_notes, cleaned_description, mediaId_parsed))
                        total_updated += 1
                        self.log_message.emit(f"Updated: {cleaned_romaji}", "blue")
                    else:
                        self.log_message.emit(f"No updates for: {cleaned_romaji}", "cyan")
                else:
                    insert_query = """INSERT INTO `anime_list`(`id_anilist`, `id_mal`, `title_english`, `title_romaji`, 
                    `on_list_status`, `air_status`, `media_format`, `season_year`, `season_period`, `all_episodes`, 
                    `episodes_progress`, `score`,`rewatched_times`, `cover_image`, `is_favourite`, `anilist_url`, 
                    `mal_url`, `last_updated_on_site`, `entry_createdAt`, `user_stardetAt`, `user_completedAt`, 
                    `notes`, `description`) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(insert_query, (mediaId_parsed, idMal_parsed, cleaned_english, cleaned_romaji,
                                                 on_list_status_parsed, air_status_parsed, format_parsed,
                                                 seasonYear_parsed, season_period_parsed, episodes_parsed,
                                                 progress_parsed, score_parsed, repeat_parsed, large_parsed,
                                                 isFavourite_parsed, siteUrl_parsed, mal_url_parsed,
                                                 updatedAt_str, entry_createdAt_str, user_startedAt_parsed,
                                                 user_completedAt_parsed, cleaned_notes, cleaned_description))
                    total_added += 1
                    self.log_message.emit(f"Added: {cleaned_romaji}", "magenta")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.log_message.emit(f"Total added: {total_added}", "yellow")
            self.log_message.emit(f"Total updated: {total_updated}", "yellow")
            self.finished.emit(f"Completed! Added: {total_added}, Updated: {total_updated}")
            
        except Exception as e:
            self.log_message.emit(f"Error in update_only_anime: {str(e)}", "red")
            self.finished.emit(f"Failed: {str(e)}")
    
    def update_only_manga(self):
        """Update only recently changed manga"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            take_all_records = "select id_anilist, last_updated_on_site from manga_list"
            try:
                cursor.execute(take_all_records)
                all_records = cursor.fetchall()
                self.log_message.emit(f"Total records in table: {len(all_records)}", "blue")
            except:
                self.log_message.emit("Table manga_list doesn't exist. Please run full backup first.", "red")
                self.finished.emit("Failed: Table doesn't exist")
                return
            
            total_updated = 0
            total_added = 0
            
            variables_in_api = {
                'page': 1,
                'perPage': 50,
                'userId': int(self.user_id)
            }
            
            api_request = '''
                query ($page: Int, $perPage: Int, $userId: Int) {
            Page(page: $page, perPage: $perPage) {
                mediaList(userId: $userId, type: MANGA, sort: UPDATED_TIME_DESC) {
                status mediaId score progress progressVolumes repeat updatedAt createdAt
                startedAt { year month day }
                completedAt { year month day }
                media {
                    title { romaji english }
                    idMal format status description
                    startDate { year }
                    chapters volumes
                    coverImage { large }
                    isFavourite siteUrl
                }
                notes
                }
            }
            }
                '''
            
            url = 'https://graphql.anilist.co'
            response_from_anilist = requests.post(url, json={'query': api_request, 'variables': variables_in_api})
            parsed_json = json.loads(response_from_anilist.text)
            
            for media_data in parsed_json["data"]["Page"]["mediaList"]:
                if not self.is_running:
                    break
                
                mediaId_parsed = media_data["mediaId"]
                score_parsed = media_data["score"]
                progress_parsed = media_data["progress"]
                progressVolumes_parsed = media_data["progressVolumes"]
                repeat_parsed = media_data["repeat"]
                on_list_status_parsed = media_data["status"]
                updatedAt_parsed = media_data["updatedAt"]
                entry_createdAt_parsed = media_data["createdAt"]
                notes_parsed = media_data["notes"]
                
                media = media_data["media"]
                english_parsed = media["title"]["english"]
                romaji_parsed = media["title"]["romaji"]
                idMal_parsed = media["idMal"] if media["idMal"] else 0
                format_parsed = media["format"]
                publish_status_parsed = media["status"]
                start_year = media["startDate"]["year"] if media["startDate"]["year"] else None
                chapters_parsed = media["chapters"] if media["chapters"] else 0
                volumes_parsed = media["volumes"] if media["volumes"] else 0
                large_parsed = media["coverImage"]["large"]
                isFavourite_parsed = "1" if media["isFavourite"] else "0"
                siteUrl_parsed = media["siteUrl"]
                description_parsed = media["description"]
                
                user_startedAt = media_data["startedAt"]
                user_completedAt = media_data["completedAt"]
                
                cleaned_english = str(english_parsed).replace("'", '"') if english_parsed else ""
                cleaned_romaji = str(romaji_parsed).replace("'", '"')
                cleaned_notes = str(notes_parsed).replace("'", '"') if notes_parsed else ""
                cleaned_description = str(description_parsed).replace("<br><br>", '<br>').replace("'", '"') if description_parsed else ""
                mal_url_parsed = f"https://myanimelist.net/manga/{idMal_parsed}"
                
                user_startedAt_parsed = f"{user_startedAt['year']}-{user_startedAt['month']}-{user_startedAt['day']}"
                user_completedAt_parsed = f"{user_completedAt['year']}-{user_completedAt['month']}-{user_completedAt['day']}"
                user_startedAt_parsed = user_startedAt_parsed.replace('None-None-None', 'not started')
                user_completedAt_parsed = user_completedAt_parsed.replace('None-None-None', 'not completed')
                
                updatedAt_str = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(updatedAt_parsed)) if updatedAt_parsed else None
                entry_createdAt_str = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(entry_createdAt_parsed)) if entry_createdAt_parsed else None
                
                check_record_query = "SELECT * FROM manga_list WHERE id_anilist = %s"
                cursor.execute(check_record_query, (mediaId_parsed,))
                record = cursor.fetchone()
                
                if record:
                    if record[19] is not None:
                        db_timestamp = int(time.mktime(record[19].timetuple()))
                    else:
                        db_timestamp = None
                    
                    updatedAt_timestamp = int(time.mktime(time.strptime(updatedAt_str, '%Y-%m-%d %H:%M:%S'))) if updatedAt_str else None
                    
                    if db_timestamp != updatedAt_timestamp:
                        update_query = """UPDATE `manga_list` SET  
                            id_mal = %s, title_english = %s, title_romaji = %s, on_list_status = %s,
                            publish_status = %s, media_format = %s, start_year = %s, all_chapters = %s,
                            chapters_progress = %s, all_volumes = %s, volumes_progress = %s, score = %s,
                            reread_times = %s, cover_image = %s, is_favourite = %s, anilist_url = %s,
                            mal_url = %s, last_updated_on_site = %s, entry_createdAt = %s,
                            user_stardetAt = %s, user_completedAt = %s, notes = %s, description = %s
                            WHERE id_anilist = %s
                            """
                        
                        cursor.execute(update_query, (idMal_parsed, cleaned_english, cleaned_romaji,
                                                     on_list_status_parsed, publish_status_parsed, format_parsed,
                                                     start_year, chapters_parsed, progress_parsed, volumes_parsed,
                                                     progressVolumes_parsed, score_parsed, repeat_parsed,
                                                     large_parsed, isFavourite_parsed, siteUrl_parsed,
                                                     mal_url_parsed, updatedAt_str, entry_createdAt_str,
                                                     user_startedAt_parsed, user_completedAt_parsed,
                                                     cleaned_notes, cleaned_description, mediaId_parsed))
                        total_updated += 1
                        self.log_message.emit(f"Updated: {cleaned_romaji}", "blue")
                    else:
                        self.log_message.emit(f"No updates for: {cleaned_romaji}", "cyan")
                else:
                    insert_query = """INSERT INTO `manga_list`(`id_anilist`, `id_mal`, `title_english`, `title_romaji`, 
                    `on_list_status`, `publish_status`, `media_format`, `start_year`, `all_chapters`, `chapters_progress`, 
                    `all_volumes`, `volumes_progress`, `score`, `reread_times`, `cover_image`, `is_favourite`, 
                    `anilist_url`, `mal_url`, `last_updated_on_site`, `entry_createdAt`, `user_stardetAt`, 
                    `user_completedAt`, `notes`, `description`) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(insert_query, (mediaId_parsed, idMal_parsed, cleaned_english, cleaned_romaji,
                                                 on_list_status_parsed, publish_status_parsed, format_parsed,
                                                 start_year, chapters_parsed, progress_parsed, volumes_parsed,
                                                 progressVolumes_parsed, score_parsed, repeat_parsed,
                                                 large_parsed, isFavourite_parsed, siteUrl_parsed,
                                                 mal_url_parsed, updatedAt_str, entry_createdAt_str,
                                                 user_startedAt_parsed, user_completedAt_parsed,
                                                 cleaned_notes, cleaned_description))
                    total_added += 1
                    self.log_message.emit(f"Added: {cleaned_romaji}", "magenta")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.log_message.emit(f"Total added: {total_added}", "yellow")
            self.log_message.emit(f"Total updated: {total_updated}", "yellow")
            self.finished.emit(f"Completed! Added: {total_added}, Updated: {total_updated}")
            
        except Exception as e:
            self.log_message.emit(f"Error in update_only_manga: {str(e)}", "red")
            self.finished.emit(f"Failed: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.initUI()
        
    def initUI(self):
        """Initialize the user interface"""
        self.setWindowTitle('AniList to MariaDB Backup Tool')
        self.setGeometry(100, 100, 900, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Title
        title = QLabel('AniList to MariaDB Backup')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Database Configuration Group
        db_group = QGroupBox("Database Configuration")
        db_layout = QVBoxLayout()
        
        # Get current config
        try:
            host_info = QLabel(f"Host: {api_keys.host_name}")
            db_info = QLabel(f"Database: {api_keys.db_name}")
            user_info = QLabel(f"User: {api_keys.user_name}")
            db_layout.addWidget(host_info)
            db_layout.addWidget(db_info)
            db_layout.addWidget(user_info)
            db_layout.addWidget(QLabel("✓ Database configuration loaded from api_keys.py"))
        except:
            db_layout.addWidget(QLabel("⚠ Please configure api_keys.py"))
        
        db_group.setLayout(db_layout)
        main_layout.addWidget(db_group)
        
        # User Input Group
        user_group = QGroupBox("AniList User")
        user_layout = QVBoxLayout()
        
        # Radio buttons for ID or Name
        radio_layout = QHBoxLayout()
        self.radio_id = QRadioButton("User ID")
        self.radio_name = QRadioButton("Username")
        self.radio_id.setChecked(True)
        radio_layout.addWidget(self.radio_id)
        radio_layout.addWidget(self.radio_name)
        user_layout.addLayout(radio_layout)
        
        # Input field
        input_layout = QHBoxLayout()
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Enter your AniList User ID or Username")
        input_layout.addWidget(QLabel("Input:"))
        input_layout.addWidget(self.user_input)
        user_layout.addLayout(input_layout)
        
        user_group.setLayout(user_layout)
        main_layout.addWidget(user_group)
        
        # Operation Selection Group
        operation_group = QGroupBox("Operation")
        operation_layout = QVBoxLayout()
        
        self.operation_combo = QComboBox()
        self.operation_combo.addItems([
            "Full Anime List Backup",
            "Full Manga List Backup",
            "Update Recent Anime",
            "Update Recent Manga"
        ])
        operation_layout.addWidget(QLabel("Select operation:"))
        operation_layout.addWidget(self.operation_combo)
        
        operation_group.setLayout(operation_layout)
        main_layout.addWidget(operation_group)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_operation)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_operation)
        self.stop_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        main_layout.addLayout(button_layout)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Log Output
        log_label = QLabel("Log Output:")
        main_layout.addWidget(log_label)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(250)
        main_layout.addWidget(self.log_output)
        
        # Status Bar
        self.statusBar().showMessage('Ready')
        
    def start_operation(self):
        """Start the selected operation"""
        # Validate input
        user_input_text = self.user_input.text().strip()
        if not user_input_text:
            QMessageBox.warning(self, "Input Error", "Please enter your AniList User ID or Username")
            return
        
        # Get user ID
        try:
            if self.radio_name.isChecked():
                # Fetch user ID from username
                self.log_output.append(f"<span style='color: blue;'>Fetching user ID for username: {user_input_text}</span>")
                user_id = self.get_user_id_from_name(user_input_text)
                if not user_id:
                    QMessageBox.warning(self, "Error", "Could not fetch user ID from username")
                    return
                self.log_output.append(f"<span style='color: green;'>User ID: {user_id}</span>")
            else:
                user_id = user_input_text
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get user ID: {str(e)}")
            return
        
        # Get database config
        try:
            db_config = {
                'host': api_keys.host_name,
                'database': api_keys.db_name,
                'user': api_keys.user_name,
                'password': api_keys.db_password
            }
        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", 
                               "Please configure api_keys.py with your database credentials")
            return
        
        # Determine operation type
        operation_index = self.operation_combo.currentIndex()
        operation_types = ["full_anime", "full_manga", "update_anime", "update_manga"]
        operation_type = operation_types[operation_index]
        
        # Clear log
        self.log_output.clear()
        self.log_output.append(f"<span style='color: green;'>Starting operation: {self.operation_combo.currentText()}</span>")
        
        # Disable start button, enable stop button
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        
        # Create and start worker thread
        self.worker = WorkerThread(operation_type, user_id, db_config)
        self.worker.log_message.connect(self.append_log)
        self.worker.finished.connect(self.operation_finished)
        self.worker.start()
        
        self.statusBar().showMessage('Running...')
    
    def stop_operation(self):
        """Stop the current operation"""
        if self.worker:
            self.worker.stop()
            self.log_output.append("<span style='color: red;'>Stopping operation...</span>")
            self.statusBar().showMessage('Stopping...')
    
    def append_log(self, message, color):
        """Append a message to the log output"""
        self.log_output.append(f"<span style='color: {color};'>{message}</span>")
        # Auto-scroll to bottom
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_output.setTextCursor(cursor)
    
    def operation_finished(self, message):
        """Handle operation completion"""
        self.log_output.append(f"<span style='color: green;font-weight: bold;'>{message}</span>")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage('Ready')
        
        QMessageBox.information(self, "Operation Complete", message)
    
    def get_user_id_from_name(self, username):
        """Fetch user ID from AniList API using username"""
        try:
            variables_in_api = {'name': username}
            api_request = '''
                query ($name: String) {
                    User(name: $name) {
                        id
                        name
                    }
                }
            '''
            url = 'https://graphql.anilist.co'
            response = requests.post(url, json={'query': api_request, 'variables': variables_in_api})
            parsed_json = json.loads(response.text)
            return parsed_json["data"]["User"]["id"]
        except Exception as e:
            self.log_output.append(f"<span style='color: red;'>Error fetching user ID: {str(e)}</span>")
            return None


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
