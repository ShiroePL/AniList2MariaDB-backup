import json
import time
import requests
import mysql.connector
from db_config import conn
from tqdm import tqdm
from datetime import datetime

# ANSI escape sequences for colors
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

i = 1
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
        user_id = 444059
        print(f"{BLUE}Hello Madrus{RESET}")
    else:
        print(f"{BLUE}your user id is: {user_id}{RESET}")
elif id_or_name == "2":
    user_name = input(f"{BLUE}Your name: {RESET}")
    if user_name == "":
        user_name = "Madrus"
        print(f"{BLUE}Hello Madrus{RESET}")
    else:
        print(f"{BLUE}your user name is: {GREEN}{user_name}{RESET}")

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
        #wait 1 second so you can see number of rows in table
    time.sleep(1)
    return output

def check_record(media_id):
    """Check if a record with the given media_id exists in the manga_list table in the database"""
    global conn
    check_record_query = "SELECT * FROM manga_list2 WHERE id_anilist = %s"
    cursor.execute(check_record_query, (media_id,))
    record = cursor.fetchone()
    return record

def update_querry_to_db(query):
    """Update a record in the manga_list table in the database"""
    global conn
    global cleaned_romaji
    cursor = conn.cursor()
    cursor.execute(query)
    print(f"{BLUE}updated record ^^ {cleaned_romaji}{RESET}")

def insert_querry_to_db(query):
    """Insert a record into the manga_list table in the database"""
    global conn   
    cursor = conn.cursor()
    cursor.execute(query)
    print(f"{MAGENTA}...added ^^ manga to database.{RESET}")
    
try: # open connection to database
    connection = conn
        # class cursor : Allows Python code to execute PostgreSQL command in a database session. Cursors are created by the connection.cursor() method
    cursor = connection.cursor()
        # need to take all records from database to compare entries
    take_all_records = "select id_anilist, last_updated_on_site from manga_list2"
    #cursor.execute(take_all_records)
    all_records = how_many_rows(take_all_records)
        # get all records
    
    # Customize the progress bar format
    bar_format = "Fetching page:"+ f"{RED}" +" {n} "+f"{RESET}"+ f"{CYAN}" + "[{elapsed}, {rate_fmt}{postfix}]" + f"{RESET}"

    has_next_page = True
    with tqdm(desc="Fetching pages", unit="page", ncols=100, initial=1, bar_format=bar_format) as progress_bar:
        while has_next_page:
            
            variables_in_api = {
            'page' : i,
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
                chapters
                volumes
                coverImage {
                large
                }
                isFavourite
                siteUrl
                countryOfOrigin
                startDate {
                year
                month
                day
              }
              endDate {
                year
                month
                day
              }
              genres
              externalLinks {
                url
              }
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
            print(f"{RED}page {i}{RESET}")

            has_next_page = parsed_json["data"]["Page"]["pageInfo"]["hasNextPage"]
        # this variable is for adding new record, it needs to be the same as amount of all records in database to fullfill condition to add record 
            # total_updated = 0
            # total_added = 0
            # this loop is defined by how many perPage is on one request (50 by default and max)
            for j in range(len(parsed_json["data"]["Page"]["mediaList"])):   # it needs to add one anime at 1 loop go

                on_list_status = mediaId = score = progress = volumes_progress = repeat = updatedAt = entry_createdAt = notes = parsed_json["data"]["Page"]["mediaList"][j]
                
                    # title
                english = romaji = parsed_json["data"]["Page"]["mediaList"][j]["media"]["title"]
                    # mediaList - media
                idMal = formatt = status  = chapters = volumes = isFavourite = siteUrl = description = country = genres = parsed_json["data"]["Page"]["mediaList"][j]["media"]
                    # coverimage
                large = parsed_json["data"]["Page"]["mediaList"][j]["media"]["coverImage"]
                    # user startedAt
                user_startedAt = parsed_json["data"]["Page"]["mediaList"][j]["startedAt"]
                    # user completedAt
                user_completedAt = parsed_json["data"]["Page"]["mediaList"][j]["completedAt"]


                    # media startedAt
                media_startDate = parsed_json["data"]["Page"]["mediaList"][j]["media"]["startDate"]
                    # media completedAt
                media_endDate = parsed_json["data"]["Page"]["mediaList"][j]["media"]["endDate"]
                    # media external links
                media_externalLinks = parsed_json["data"]["Page"]["mediaList"][j]["media"]["externalLinks"]

                on_list_status_parsed = on_list_status["status"]
                mediaId_parsed = mediaId["mediaId"]
                score_parsed = score["score"]
                progress_parsed = progress["progress"]
                volumes_progress_parsed = volumes_progress["progressVolumes"]
                repeat_parsed = repeat["repeat"]
                english_parsed = english["english"]
                romaji_parsed = romaji["romaji"]
                idMal_parsed = idMal["idMal"]
                format_parsed = formatt["format"]
                status_parsed = status["status"]
                
                updatedAt_parsed = updatedAt["updatedAt"]
                
                chapters_parsed = chapters["chapters"]
                volumes_parsed = volumes["volumes"]
                large_parsed = large["large"]
                isFavourite_parsed = isFavourite["isFavourite"]
                siteUrl_parsed = siteUrl["siteUrl"]
                notes_parsed = notes["notes"]
                description_parsed = description["description"]
                entry_createdAt_parsed = entry_createdAt["createdAt"]
                country_parsed = country["countryOfOrigin"]

                    # started at 
                user_startedAt_year = user_startedAt["year"]
                user_startedAt_month = user_startedAt["month"]
                user_startedAt_day = user_startedAt["day"]
                
                    # completed at
                user_completedAt_year = user_completedAt["year"]
                user_completedAt_month = user_completedAt["month"]
                user_completedAt_day = user_completedAt["day"]

                    # media start date
                media_startDate_year = media_startDate["year"]
                media_startDate_month = media_startDate["month"]
                media_startDate_day = media_startDate["day"]
                
                    # media end date
                media_endDate_year = media_endDate["year"]
                media_endDate_month = media_endDate["month"]
                media_endDate_day = media_endDate["day"]


                # Initialize an empty list to store the parsed URLs
                media_externalLinks_parsed = []

                # Iterate through each item in the media_externalLinks list
                for link in media_externalLinks:
                    # Extract the URL and append it to the media_externalLinks_parsed list
                    url = link["url"]
                    media_externalLinks_parsed.append(url)


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

                    # reformating MEDIA start date and completed to date format from sql
                media_startDate_parsed = str(media_startDate_year) + "-" + str(media_startDate_month) + "-" + str(media_startDate_day)
                media_endDate_parsed = str(media_endDate_year) + "-" + str(media_endDate_month) + "-" + str(media_endDate_day)

                    # if null make null to add to databese user started and completed
                cleanded_user_startedAt = user_startedAt_parsed.replace('None-None-None' , 'not started')
                cleanded_user_completedAt = user_completedAt_parsed.replace('None-None-None' , 'not completed')
                chapters_parsed = '0' if chapters_parsed is None else chapters_parsed
                volumes_parsed = '0' if volumes_parsed is None else volumes_parsed

                #print(f"{RED}entry_createdAt_parsed : {cleanded_user_completedAt}{RESET}")
                updated_at_for_loop = updatedAt["updatedAt"]

                #cheat sheet numbers of columns from database
                #(0 id_anilist, 1 id_mal, 2 title_english, 3 title_romaji, 4 on_list_status, 5 status,6 media_format,7 season_year,8 season_period,9 all_episodes,10 episodes_progress,
                #11 score,12 rewatched_times, 13 cover_image, 14 is_favourite, 15 anilist_url, 16 mal_url, 17 last_updated_on_site, 18 entry_createdAt, 19 user_stardetAt, 20 user_completedAt,
                #21 notes, 22 description)
    
                
                tqdm.write(f"{GREEN}Checking for mediaId: {mediaId_parsed}{RESET}")
                record = check_record(mediaId_parsed)
                #print(f"{RED}record : {record}{RESET}")
                
                if entry_createdAt_parsed == 'NULL':
                    created_at_for_db = 'NULL'
                elif entry_createdAt_parsed == 0:
                    created_at_for_db = 'NULL'
                else:
                    created_at_for_db = f"FROM_UNIXTIME({entry_createdAt_parsed})"

                if updatedAt_parsed == 'NULL':
                    updatedAt_parsed_for_db = 'NULL'
                elif updatedAt_parsed == 0:
                    updatedAt_parsed_for_db = 'NULL'
                else:
                    updatedAt_parsed_for_db = f"FROM_UNIXTIME({updatedAt_parsed})"

                #print("idMal_parsed : ", idMal_parsed)
                if idMal_parsed is None:
                    idMal_parsed = 0
                #print("changed idMal_parsed : ", idMal_parsed)
                # Convert the Unix timestamp to a Python datetime object
                updatedAt_datetime = datetime.fromtimestamp(updatedAt_parsed)

                # Convert the datetime object to a string in the correct format
                updatedAt_parsed = updatedAt_datetime.strftime('%Y-%m-%d %H:%M:%S')
                #print("cleanded_user_startedAt : ", cleanded_user_startedAt)
                #print("cleanded_user_completedAt : ", cleanded_user_completedAt)

                if record:
                    #print(f"rekors 16 : {record[16]} for anime {romaji_parsed}")
                    # # Record exists
                    print(f"{RED}record : {record}{RESET}")
                    if record[16] is not None: #
                        db_timestamp = int(time.mktime(record[16].timetuple()))
                    else:
                        db_timestamp = None

                    if db_timestamp is not None and updatedAt_parsed is not None:
                        updatedAt_timestamp = int(time.mktime(time.strptime(updatedAt_parsed, '%Y-%m-%d %H:%M:%S')))
                    else:
                        updatedAt_timestamp = None

                    # print(f"updatedAt_parsed: {updatedAt_parsed}")
                    # print("db_timestamp: " + str(db_timestamp))
                    # print("updatedAt_timestamp: " + str(updatedAt_timestamp))
                    # print(f"rekors 18 : {record[18]} for anime {romaji_parsed}")
                    #       
                    if db_timestamp != updatedAt_timestamp:
                        
                    #if record[18] != updatedAt_parsed:
                        update_querry = """ UPDATE `manga_list2` SET  
                            id_anilist = {0},
                            id_mal = {1},
                            title_english = '{2}',
                            title_romaji = '{3}',
                            on_list_status = '{4}',
                            status = '{5}',
                            media_format = '{6}',
                            all_chapters = {7},
                            all_volumes = {8},
                            chapters_progress = {9},
                            volumes_progress = {10},
                            score = {11},
                            reread_times = {12},
                            cover_image = '{13}',
                            is_favourite = {14},
                            anilist_url = '{15}',
                            mal_url = '{16}',
                            last_updated_on_site = {17},
                            entry_createdAt = {18},
                            user_stardetAt = '{19}',
                            user_completedAt = '{20}',
                            notes = '{21}',
                            description = '{22}',
                            country_of_origin = '{23}',
                            media_start_date = '{24}',
                            media_end_date = '{25}',
                            genres = '{26}',
                            external_links = '{27}'
                            WHERE id_anilist = {0};
                            """
                                # inserting variables to ^^ {x} 
                        update_record = (update_querry.format(mediaId_parsed, idMal_parsed, cleaned_english ,cleaned_romaji , on_list_status_parsed, status_parsed, format_parsed, 
                        chapters_parsed, volumes_parsed , progress_parsed,volumes_progress ,score_parsed , repeat_parsed, large_parsed, isFavourite_parsed, siteUrl_parsed, mal_url_parsed, updatedAt_parsed_for_db,
                        created_at_for_db, cleanded_user_startedAt, cleanded_user_completedAt, cleaned_notes,cleaned_description, country_parsed, media_startDate_parsed, media_endDate_parsed, genres, media_externalLinks_parsed))
                            # using function from different file, I can't do this different 
                        #print("update_record : ", update_record)
                        update_querry_to_db(update_record)

                        total_updated += 1
                        

                else:
                    print(f"{CYAN}This manga is not in a table: {cleaned_romaji}{RESET}")
                        # building querry to insert to table
                    insert_querry = """INSERT INTO `manga_list2`(`id_anilist`, `id_mal`, `title_english`, `title_romaji`, `on_list_status`, `status`, `media_format`, 
                     `all_chapters`, `all_volumes`, `chapters_progress`, `volumes_progress`, `score`,`reread_times`, `cover_image`, `is_favourite`, `anilist_url`, `mal_url`, `last_updated_on_site`,
                    `entry_createdAt`, `user_stardetAt`, `user_completedAt`, `notes`, `description`, `country_of_origin`, `media_start_date`, `media_end_date`, `genres`, `external_links`) 
                    VALUES
                    ({0}, {1}, '{2}', '{3}', '{4}', '{5}', '{6}', {7}, {8}, {9}, {10}, {11}, {12}, '{13}', {14}, '{15}', '{16}', {17}, {18}, '{19}', '{20}', '{21}', '{22}', '{23}', '{24}', '{25}', '{26}', '{27}');
                    """
                        # inserting variables to ^^ {x}
                    insert_record = (insert_querry.format(mediaId_parsed, idMal_parsed, cleaned_english ,cleaned_romaji , on_list_status_parsed, status_parsed, format_parsed, 
                    chapters_parsed, volumes_parsed, progress_parsed, volumes_progress, score_parsed , repeat_parsed, large_parsed, isFavourite_parsed, siteUrl_parsed, mal_url_parsed, updatedAt_parsed_for_db,
                    created_at_for_db, cleanded_user_startedAt, cleanded_user_completedAt, cleaned_notes,cleaned_description, country_parsed, media_startDate_parsed, media_endDate_parsed, genres, media_externalLinks_parsed))             
                        # using function from different file, I can't do this different
                    #print("insert_record: "+insert_record)
                    print("insert record: ", insert_record)
                    insert_querry_to_db(insert_record)
                    print("inserted??")
                    total_added+= 1    
                    
            print(f"{YELLOW}Total added: {total_added}{RESET}")
            print(f"{YELLOW}Total updated: {total_updated}{RESET}")
            
            conn.commit()
            progress_bar.update(1)
            
            i += 1

except mysql.connector.Error as e: #if cannot connect to database
    print("Error reading data from MySQL table", e)
finally: # close connection after completing program
    if connection.is_connected():
        connection.close()
        cursor.close()
        print("MySQL connection is closed")
