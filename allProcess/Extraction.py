#!/usr/bin/env python
# coding: utf-8

# https://dev.to/twitterdev/a-comprehensive-guide-for-using-the-twitter-api-v2-using-tweepy-in-python-15d9
# https://developer.twitter.com/en/docs/twitter-api/tweets/counts/integrate/build-a-query


import tweepy
from datetime import datetime
from datetime import timedelta
import time
import openpyxl
import argparse
import pandas as pd
import os

def search_tweets(lon, lat, dist, keywords_path, t, client):

    # Read the keyword filter file if the user decided to apply an "a priori filter"
    if not keywords_path is None:
        with open(keywords_path, 'r', encoding='utf-8') as f:
            # To split
            keywords = f.readline().split(', ')

    # Replace with time period of your choice
    start_time = '2006-03-27T00:00:00Z'

    # Replace with time period of your choice
    my_date = datetime.now()
    subtract_seconds = my_date - timedelta(days=1)
    end_time = subtract_seconds.strftime("%Y-%m-%dT%H:%M:%SZ")

    num = 0
    queries = []
    #Prepare the query in case the user doesn't want to use keyword filtering
    if keywords_path is None:
        query = 'point_radius:[' + str(lon) + ' ' + str(lat) + ' ' + str(dist) + 'km]'
        queries.append(query)
    #Prepare a query taking into account the a priori filter given by the user
    else:
        query = "("
        isFirst = True
        for x in keywords:
            aux_query = query + " OR " + x + ") point_radius:[" + str(lon) + " " + str(lat) + " " + str(
                dist) + "km]"
            aux = len(aux_query)
            if(aux > 100):
                act_query = query + ") point_radius:[" + str(lon) + " " + str(lat) + " " + str(
                dist) + "km]"
                queries.append(act_query)
                query = "( "
                isFirst = True
            if num < len(keywords)-1:
                if isFirst:
                    query += x
                    isFirst = False
                else:
                    query += " OR " + x
            else:
                query += " OR " + x + ") point_radius:[" + str(lon) + " " + str(lat) + " " + str(
                dist) + "km]"
                queries.append(query)
            num += 1

    query_done = False
    has_next_token = False
    _next_token = ""
    sleep = 1
    tweets = []

    # Submit the queries to the Twitter API and get the resulting tweets
    for query in queries:
        while not query_done:
            try:
                if not has_next_token:
                    result = client.search_all_tweets(query, start_time=start_time, end_time=end_time, max_results=500,
                                                      expansions='author_id', tweet_fields=['created_at', 'public_metrics'], )
                    if result.data:
                        tweets = tweets+result.data

                else:
                    result = client.search_all_tweets(query, start_time=start_time, end_time=end_time, max_results=500,
                                                  expansions='author_id', tweet_fields=['created_at', 'public_metrics'], next_token = _next_token)
                    if result.data:
                        tweets = tweets+result.data
                if "next_token" in result.meta:
                    _next_token = result.meta["next_token"]
                    print(_next_token)
                    has_next_token = True
                else:
                    query_done = True
            except Exception as e:
                print(e, sleep)
                time.sleep(sleep)
                sleep *= 2

    if not tweets: return None

    tweets_return = []

    # Get all the necessary information from each tweet
    for tweet in tweets:
        #print(tweet)
        tweet_id = tweet.id
        author_id = tweet.author_id
        user_home = '-'
        tweet_text = tweet.text
        created_at = tweet.created_at

        likes = 0
        n_replies = 0
        n_retweet = 0

        if 'public_metrics' in tweet:
            likes = tweet.public_metrics['like_count']
            n_replies = tweet.public_metrics['reply_count']
            n_retweet = tweet.public_metrics['retweet_count']

        tweets_return.append(
            {'tweet_id': tweet_id, 'tweet_text': tweet_text, 'author_id': author_id, 'user_home': user_home,
                'n_retweet': n_retweet, 'n_replies': n_replies, 'likes': likes, 'created_at': created_at})

    return tweets_return

# Append the obtained tweets to the resulting excel file
def append_df_to_excel(filename, df, sheet_name='Sheet1'):
    try:
        df_2 = pd.read_excel(filename, sheet_name)
        df = pd.concat([df_2, df], axis=0)
        df.drop_duplicates(subset=['tweet_id'], inplace=True)

    except Exception as e:
        pass

    df.to_excel(filename, sheet_name, header=True, index=False)

def extraction(path, api_key, destination_path, keywords_path = None):

    client = tweepy.Client(api_key)

    ws_ptr = pd.read_excel(path)

    # Read the information of each point that maps the river
    for index, row in ws_ptr.iterrows():
        print(index)

        id = row["id"]
        dist = row["Dist"]/1000
        if dist > 40:
            dist = 40
        coord_y = row["ycoord"]
        coord_x = row["xcoord"]

        # Get the tweets for the current point
        response = search_tweets(coord_x, coord_y, dist, keywords_path,  1, client)

        # If we got any tweets for the point save the information to the dataframe
        if response is not None and len(response) > 0:
            df_rows = []
            for tweet in response:
                tweet['id'] = id
                tweet['coord_x'] = coord_x
                tweet['coord_y'] = coord_y

                df_rows.append(tweet)

            df = pd.DataFrame(df_rows)
            df['created_at'] = df['created_at'].apply(lambda a: pd.to_datetime(a).date())
            filepath = destination_path+"\export_dataframe.xlsx"
            # Append the information to the "export_dataframe" excel
            append_df_to_excel(filepath, df)

    print("-------------------------- END --------------------------")