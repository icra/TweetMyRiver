import pandas as pd
import time
import re
import os

from deep_translator import GoogleTranslator

# ----------------------------- FUNCTIONS -----------------------------

#Removes the emojis of a given text ("data")
def remove_emojis(data):
    if not isinstance(data, str):
        return ""
    emoj = re.compile("["
        u"\U00002700-\U000027BF"  # Dingbats
        u"\U0001F600-\U0001F64F"  # Emoticons
        u"\U00002600-\U000026FF"  # Miscellaneous Symbols
        u"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols And Pictographs
        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        u"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
                      "]+", re.UNICODE)
    return re.sub(emoj, '', data)

# Changes the hashtags in "text" for "" if they are in the middle of the text or "." if they are at the end of the text
def changeHashtags(text):
    res = re.split('(#[^\s]+)', text)
    res = list(map(str.strip, res))
    res = list(filter(lambda x: x != '', res))
    atTheEnd = True
    for i in range(len(res) - 1, -1, -1):
        if "#" in res[i]:
            if atTheEnd:
                res[i] = res[i]+"."
            res[i] = res[i].replace("#", "")
        else:
            atTheEnd = False

    res = ' '.join(res)
    return res

# ------------------------------ MAIN ------------------------------ #
def translation(initial_path):

    # Read the Excel with all the tweets as a DataFrame
    df = pd.read_excel(initial_path)

    # Copy the DataFrame into a new DataFrame which is going to be modified with the translations
    translations_df = df.copy()

    translations = open("translations.txt", "w", encoding="utf-8")

    ind_deleted = []

    # Iterate through every row on the DataFrame
    for ind in df.index:
        print("Translating tweet", ind)
        text = remove_emojis(df["tweet_text"][ind])
        # Delete links:
        text = re.sub(r'http\S+', "", text)
        # Delete tagged people (@name)
        text = re.sub(r'@\S+', "", text)
        text = text.replace("@", "")
        # Replace "#" for "" or "." depending on the case
        text = changeHashtags(text)
        # Check the resulting string after the modifications isn't blank
        if text and text.strip():
            query_done = False
            sleep = 1
            while not query_done:
                # Try to translate the tweet text
                try:
                    translated = GoogleTranslator(source="auto", target="en").translate(text)
                    translations_df.at[ind, "tweet_text"] = translated
                    query_done = True
                # In case the API says we have done too many queries wait "sleep" seconds and try again
                except IndexError:
                    print("Error solved")
                    query_done = True
                except Exception as e:
                    print(e)
                    print(text)
                    sleep *= 2
                    if sleep > 32:
                        query_done = True
                        print("Last sleep")
                    print("Too many requests, waiting", sleep, "seconds")
                    time.sleep(sleep)
        # If the string is blank, save the row index to delete it later
        else:
            ind_deleted.append(ind)

    # Delete all the rows which have blank text
    translations_df.drop(ind_deleted, inplace=True)

    # Filter data before saving it
    keywords = "stream river creek pond wetland riverscape valley canyon pool riffle cascade fall fish frog riparian reservoir dam levee bird bridge lake lever excursion bicycle insect water flood walk watch flow landscape views sunset beach sea plant station ditch source fountain nature mill weir sunrise iconic bath swim storm protect kayak gorge torrent paradise path footpath trail adventure invasive drought dirty polluted duck wonderful great calm quiet peaceful peace tranquillity rowing trekking"
    mask = (pd.concat([translations_df["tweet_text"].str.contains(word,regex=False) for word in keywords.split()],axis=1)).sum(1) > 1
    final_translations = translations_df[mask]

    # Convert the "created_at" column to datetime and extract the date
    final_translations["date"] = pd.to_datetime(final_translations["created_at"]).dt.date

    # Drop duplicates of tweets from the same author, location and date, keeping the first occurrence
    final_translations = final_translations.drop_duplicates(subset=["author_id", "id", "date"], keep="first")

    # Remove the "date" column from the DataFrame
    final_translations = final_translations.drop(columns=["date"])

    # Save the new DataFrame (translations_df) as an Excel file
    dir_path = os.path.dirname(initial_path)
    new_excel_path = os.path.join(dir_path, "Data_Translated.xlsx")
    final_translations.to_excel(new_excel_path)

    print("END")

    translations.close()