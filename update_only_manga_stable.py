import json
from turtle import st
import time
import requests
import mysql.connector
import api_keys
from db_config import conn

# ANSI escape sequences for colors
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"


j = 0
how_many_anime_in_one_request = 50 #max 50
total_updated = 0
total_added = 0

id_or_name = input(f"Do you want to use, {GREEN}user id{RESET} or {GREEN}name?{RESET} (exit for exit :o)\n 1: id \n 2: name \n {CYAN}choice: {RESET}")
if id_or_name == "exit":
    print(f"{GREEN}bye bye :<{RESET}")
    exit()
elif id_or_name == "1":
    user_id = input(f"{BLUE}Your id: {RESET}")
    
    if user_id == "":
        # plese put your user id
        print(f"{RED}You need to put your user id!{RESET}")
        exit()
    else:
        print(f"{BLUE}your user id is: {user_id}{RESET}")
elif id_or_name == "2":
    user_name = input(f"{BLUE}Your name: {RESET}")
    if user_name == "":
        # plese put your name
        print(f"{RED}You need to put your user name!{RESET}")
        exit()
    else:
        print(f"{BLUE}your user name is: {GREEN}{user_name}{RESET}")
elif id_or_name == "":
    # plese choose something
    print(f"{RED}You need to choose something!{RESET}")
    exit()
#need to fetch id from anilist API for user name
if id_or_name == "2":
    variables_in_api = {
        'name' : user_name
    }

    api_request  = '''
        query ($name: String) {
            User(name: $name) {
                id
                name
                }
            }
        '''
    url = 'https://graphql.anilist.co'
        # sending api request
    response_frop_anilist = requests.post(url, json={'query': api_request, 'variables': variables_in_api})
        # take api response to python dictionary to parse json
    parsed_json = json.loads(response_frop_anilist.text)
    user_id = parsed_json["data"]["User"]["id"]
    print(f"{BLUE}your user id is: {GREEN}{user_id}{RESET}")

def how_many_rows(query):
    """Add a pair of question and answer to the general table in the database"""
    global conn
    cursor = conn.cursor()
    cursor.execute(query)
    output = cursor.fetchall()
    print(f"{BLUE}Total number of rows in table: {cursor.rowcount}{RESET}")
    conn.commit()
    return output

def check_record(media_id):
    """Check if a record with the given media_id exists in the manga_list table in the database"""
    global conn
    check_record_query = "SELECT * FROM manga_list WHERE id_anilist = %s"
    cursor.execute(check_record_query, (media_id,))
    record = cursor.fetchone()
    return record

def update_querry_to_db(query):
    """Update a record in the manga_list table in the database"""
    global conn
    global cleaned_romaji
    cursor = conn.cursor()
    cursor.execute(query)
    print(f"{MAGENTA}updated record ^^ {CYAN}{cleaned_romaji}{RESET}")

def insert_querry_to_db(query):
    """Insert a record into the manga_list table in the database"""
    global conn   
    cursor = conn.cursor()
    cursor.execute(query)
    print("...added ^^ manga to database.")

 
try: # open connection to database
    connection = conn
        # class cursor : Allows Python code to execute PostgreSQL command in a database session. Cursors are created by the connection.cursor() method
    cursor = connection.cursor()
        # need to take all records from database to compare entries
    take_all_records = "select id_anilist, last_updated_on_site from manga_list"
    
    all_records = how_many_rows(take_all_records)
        # get all records
   
    total_anime = 0
  
    variables_in_api = {
    'page' : 1,
    'perPage' : how_many_anime_in_one_request,
    'userId' : user_id
    }

    api_request  = '''
        query ($page: Int, $perPage: Int, $userId: Int) {
Page(page: $page, perPage: $perPage) {
    pageInfo {
    perPage
    currentPage
    lastPage
    hasNextPage
    }
    mediaList(userId: $userId, type: MANGA, sort: UPDATED_TIME_DESC) {
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
        chapters
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
        # sending api request
    response_frop_anilist = requests.post(url, json={'query': api_request, 'variables': variables_in_api})

        # take api response to python dictionary to parse json
    parsed_json = json.loads(response_frop_anilist.text)

    # this loop is defined by how many perPage is on one request (50 by default and max)

    for j in range(len(parsed_json["data"]["Page"]["mediaList"])):   # it needs to add one anime at 1 loop go

        on_list_status = mediaId = score = progress = repeat = updatedAt = entry_createdAt = notes = parsed_json["data"]["Page"]["mediaList"][j]
        
            # title
        english = romaji = parsed_json["data"]["Page"]["mediaList"][j]["media"]["title"]
            # mediaList - media
        idMal = formatt = status  = chapters = isFavourite = siteUrl = description = parsed_json["data"]["Page"]["mediaList"][j]["media"]
            # coverimage
        large = parsed_json["data"]["Page"]["mediaList"][j]["media"]["coverImage"]
            # user startedAt
        user_startedAt = parsed_json["data"]["Page"]["mediaList"][j]["startedAt"]
            # user completedAt
        user_completedAt = parsed_json["data"]["Page"]["mediaList"][j]["completedAt"]


        on_list_status_parsed = on_list_status["status"]
        mediaId_parsed = mediaId["mediaId"]
        score_parsed = score["score"]
        progress_parsed = progress["progress"]
        repeat_parsed = repeat["repeat"]
        english_parsed = english["english"]
        romaji_parsed = romaji["romaji"]
        idMal_parsed = idMal["idMal"]
        format_parsed = formatt["format"]
        status_parsed = status["status"]
        
        updatedAt_parsed = updatedAt["updatedAt"]
        
        chapters_parsed = chapters["chapters"]
        large_parsed = large["large"]
        isFavourite_parsed = isFavourite["isFavourite"]
        siteUrl_parsed = siteUrl["siteUrl"]
        notes_parsed = notes["notes"]
        description_parsed = description["description"]
        entry_createdAt_parsed = entry_createdAt["createdAt"]

            # started at 
        user_startedAt_year = user_startedAt["year"]
        user_startedAt_month = user_startedAt["month"]
        user_startedAt_day = user_startedAt["day"]
        
            # completed at
        user_completedAt_year = user_completedAt["year"]
        user_completedAt_month = user_completedAt["month"]
        user_completedAt_day = user_completedAt["day"]

            # cleaning strings and formating
        cleaned_english = str(english_parsed).replace("'" , '"')
        cleaned_romaji = str(romaji_parsed).replace("'" , '"')
        cleaned_notes = str(notes_parsed).replace("'" , '"')
        isFavourite_parsed = str(isFavourite_parsed).replace("True" , "1")
        isFavourite_parsed = str(isFavourite_parsed).replace("False" , "0")
        cleaned_description = str(description_parsed).replace("<br><br>" , '<br>')
        cleaned_description = str(cleaned_description).replace("'" , '"')       
        mal_url_parsed = "https://myanimelist.net/manga/" + str(idMal_parsed)

            # reformating user started and completed to date format from sql
        user_startedAt_parsed = str(user_startedAt_year) + "-" + str(user_startedAt_month) + "-" + str(user_startedAt_day)
        user_completedAt_parsed = str(user_completedAt_year) + "-" + str(user_completedAt_month) + "-" + str(user_completedAt_day)

            # if null make null to add to databese user started and completed
        cleanded_user_startedAt = user_startedAt_parsed.replace('None-None-None' , 'not started')
        cleanded_user_completedAt = user_completedAt_parsed.replace('None-None-None' , 'not completed')
        chapters_parsed = 'NULL' if chapters_parsed is None else chapters_parsed
        if idMal_parsed is None:
            idMal_parsed = 0

        print(f"{GREEN}Checking for mediaId: {mediaId_parsed}{RESET}")
        
        if entry_createdAt_parsed == 'NULL' or entry_createdAt_parsed == 0:
            entry_createdAt_parsed = None
        else:
            entry_createdAt_parsed = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(entry_createdAt_parsed))

        if updatedAt_parsed == 'NULL' or updatedAt_parsed == 0:
            updatedAt_parsed = None
        else:
            updatedAt_parsed = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(updatedAt_parsed))

        record = check_record(mediaId_parsed)

        if record:
                # Record exists
            if record[16] is not None:
                    db_timestamp = int(time.mktime(record[16].timetuple()))
            else:
                db_timestamp = None

            if db_timestamp is not None and updatedAt_parsed is not None:
                updatedAt_timestamp = int(time.mktime(time.strptime(updatedAt_parsed, '%Y-%m-%d %H:%M:%S')))
            else:
                updatedAt_timestamp = None

            if db_timestamp != updatedAt_timestamp:         
                update_querry = """ UPDATE `manga_list` SET  
                    id_anilist = {0},
                    id_mal = {1},
                    title_english = '{2}',
                    title_romaji = '{3}',
                    on_list_status = '{4}',
                    status = '{5}',
                    media_format = '{6}',
                    all_chapters = {7},
                    chapters_progress = {8},
                    score = {9},
                    reread_times = {10},
                    cover_image = '{11}',
                    is_favourite = '{12}',
                    anilist_url = '{13}',
                    mal_url = '{14}',
                    last_updated_on_site = '{15}',
                    entry_createdAt = '{16}',
                    user_stardetAt = '{17}',
                    user_completedAt = '{18}',
                    notes = '{19}',
                    description = '{20}'
                    WHERE id_anilist = {0};
                    """
                        # inserting variables to ^^ {x} 
                update_record = (update_querry.format(mediaId_parsed, idMal_parsed, cleaned_english ,cleaned_romaji , on_list_status_parsed, status_parsed, format_parsed,
                 chapters_parsed, progress_parsed,score_parsed , repeat_parsed, large_parsed, isFavourite_parsed, siteUrl_parsed, mal_url_parsed, updatedAt_parsed,
                entry_createdAt_parsed, cleanded_user_startedAt, cleanded_user_completedAt, cleaned_notes,cleaned_description))
                    # using function from different file, I can't do this different 
                
                update_querry_to_db(update_record)
                
                #updated anime
                conn.commit()
                total_updated += 1
                

            else: # INSTEAD OF BREAKING, JUST SKIP TO NEXT ANIME BECAUSE NEXT ONE COULD BE NEW, NEED TO CHECK MORE ANIME
                print(f"{RED}No new updates for {RESET}{CYAN}{cleaned_romaji}{RESET}{RED}, going to next...{RESET}")
                
                    
        else:
            
            print(f"{CYAN}This manga is not in a table: {cleaned_romaji}{RESET}")
            add_querry = """ INSERT INTO `manga_list` SET  
                    id_anilist = {0},
                    id_mal = {1},
                    title_english = '{2}',
                    title_romaji = '{3}',
                    on_list_status = '{4}',
                    status = '{5}',
                    media_format = '{6}',
                    all_chapters = {7},
                    chapters_progress = {8},
                    score = {9},
                    reread_times = {10},
                    cover_image = '{11}',
                    is_favourite = '{12}',
                    anilist_url = '{13}',
                    mal_url = '{14}',
                    last_updated_on_site = '{15}',
                    entry_createdAt = '{16}',
                    user_stardetAt = '{17}',
                    user_completedAt = '{18}',
                    notes = '{19}',
                    description = '{20}';
                    """
                        # inserting variables to ^^ {x} 
            add_record = (add_querry.format(mediaId_parsed, idMal_parsed, cleaned_english ,cleaned_romaji , on_list_status_parsed, status_parsed, format_parsed,
                chapters_parsed, progress_parsed,score_parsed , repeat_parsed, large_parsed, isFavourite_parsed, siteUrl_parsed, mal_url_parsed, updatedAt_parsed,
            entry_createdAt_parsed, cleanded_user_startedAt, cleanded_user_completedAt, cleaned_notes,cleaned_description))
                # using function from different file, I can't do this different 
            insert_querry_to_db(add_record)

            print("...added ^^ manga to database.")
            total_added+= 1 
             
    print(f"{YELLOW}Total added: {total_added}{RESET}")
    print(f"{MAGENTA}Total updated: {total_updated}{RESET}")
    conn.commit()
        
except mysql.connector.Error as e: #if cannot connect to database
    print("Error reading data from MySQL table", e)
finally: # close connection after completing program
    if connection.is_connected():
        connection.close()
        cursor.close()
        print("MySQL connection is closed")