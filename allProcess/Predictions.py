#Necessary Libraries
import numpy as np
import pandas as pd
import nltk
import xlsxwriter
import sklearn
import sklearn.metrics._pairwise_distances_reduction._datasets_pair
import sklearn.metrics._pairwise_distances_reduction._middle_term_computer
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import GridSearchCV
import re
import os

def predict(path_predict, allowed_error, path=None, categs=None):

    #Reading the Excel containing the data as a Dataframe
    dir_path = os.path.dirname(path_predict)
    dataframepath = os.path.join(dir_path, "Data_Translated_3categ.xlsx")
    if not path is None:
        dataframepath = path
    original_data = pd.read_excel(dataframepath)

    #Selecting only the columns that we need, which are the tweet text and its category
    data = original_data[['tweet_text', 'CES']]
    n_categ = 3
    if not categs is None:
        n_categ = int(categs)

    # Data cleaning and processing

    cleanedData = []

    lemma = WordNetLemmatizer()
    swords = stopwords.words("english")
    for text in data['tweet_text']:
        text = str(text)
        text = re.sub(r'http\S+', '', text)
        text = re.sub("[^a-zA-Z0-9]", " ", text)
        text = nltk.word_tokenize(text.lower())
        text = [lemma.lemmatize(word) for word in text]
        text = [word for word in text if word not in swords]
        text = " ".join(text)

        cleanedData.append(text)

    vectorizer = CountVectorizer(max_features=10000)
    BOW = vectorizer.fit_transform(cleanedData)

    #Splitting dataset in two parts, one containging 70% of data used for training
    #and the other one containging the 30% left used for test and validation
    from sklearn.model_selection import train_test_split
    x_train,x_test,y_train,y_test = train_test_split(BOW,np.asarray(data["CES"]), test_size=0.3)

    #Creating the algorithm using cross validation

    clf = MultinomialNB()
    #We use Repeated Stratified K Fold to implement Cross Validation
    rskf = RepeatedStratifiedKFold()
    parameters = {
        'alpha': np.logspace(-9, 0, 100)
    }

    gs = GridSearchCV(clf, parameters, cv=rskf, scoring='neg_log_loss')
    gs.fit(x_train, y_train)

    #Test the model and get the predictions for the test set
    predicted = gs.predict(x_test)
    #Get the probabilities of each prediction for each class
    class_probabilities = gs.predict_proba(x_test)

    #Here we define the percentatge of incorreclty classified tweets that we want to handle
    margin = int(allowed_error)/100

    margin_act = 0

    #Define the limit for each category as the value of the highest probaility in it
    #limit = [max(categ1), max(categ2), max(categ3)]
    limit = []
    for i in range(n_categ):
        limit.append(max([row[i] for row in class_probabilities]))

    #For every category
    for x in range(len(limit)):
        #While the percentatge of wrongly classified tweets is lesser than the one we defined and the limit is greater than 0
        #(if the limit is lesser than 0 means that with the margin set a limit that satisfies it can't be found)
        while margin_act <= margin and limit[x] >= 0:
            n_good = 0
            n = 0
            #Iterate through every prediction and check if it is classified as the current category
            for i in range(len(predicted)):
                classi = predicted[i]-1
                if classi == x:
                    #Check if the probability for this category is at least equal to the current limit
                    if class_probabilities[i][classi] >= limit[x]:
                        #If it is at least equal, check if it is correctly classified
                        if predicted[i] == y_test[i]:
                            n_good += 1
                        n += 1
            #Decrease the limit
            limit[x] -= 0.01
            #Calculate the current margin
            margin_act = 1-(n_good/n)
        margin_act = 0

    #Since an extra iteration is done (because it halts from the loop when the limit is not acceptable any more) and the limit
    #is decreased an extra time, we revert this changes by addind 0.02 to the current limits
    limit[0] += 0.02
    limit[1] += 0.02
    limit[2] += 0.02

    #Validation analisis


    #Classification and predictions
    data_p = pd.read_excel(path_predict)
    training_results_pd = pd.DataFrame(columns=['Category', 'Total Tweets', 'BAM (%)', 'Correclty classified', 'Incorrectly classified'])

    for x in range(n_categ):
        n_good = 0
        n_bad = 0
        n = 0
        BAM = 0
        for i in range(len(predicted)):
            classi = predicted[i]-1
            if classi == x:
                if predicted[i] == y_test[i]:
                    n_good += 1
                else:
                    n_bad += 1
                n += 1
                BAM += class_probabilities[i][classi]
        training_results_pd.loc[len(training_results_pd.index)] = [x+1, n, (BAM/n)*100, n_good, n_bad]

    # Data cleaning and processing

    cleanedData = []

    lemma = WordNetLemmatizer()
    swords = stopwords.words("english")
    for text in data_p['tweet_text']:
        text = str(text)
        text = re.sub(r'http\S+', '', text)
        text = re.sub("[^a-zA-Z0-9]", " ", text)
        text = nltk.word_tokenize(text.lower())
        text = [lemma.lemmatize(word) for word in text]
        text = [word for word in text if word not in swords]
        text = " ".join(text)

        cleanedData.append(text)

    # vectorizer = CountVectorizer(max_features=10000)
    BOW = vectorizer.transform(cleanedData)

    #Test the model and get the predictions for the test set
    predicted = gs.predict(BOW)
    #Get the probabilities of each prediction for each class
    class_probabilities = gs.predict_proba(BOW)

    confidence = []
    for prob in class_probabilities:
        confidence.append(max(prob))

    data_p["predicted_CES"] = predicted
    data_p["Confidence"] = confidence

    #Generate the classification results dataframe
    classification_results_pd = pd.DataFrame(columns=['Category', 'Accepted tweets', 'BAM (%)', 'Discarded Tweets'])

    rows_to_drop = []
    n_taken = [0] * n_categ
    n_discard = [0] * n_categ
    n_BAM = [0] * n_categ
    for ind in data_p.index:
        clss = data_p["predicted_CES"][ind]
        if data_p["Confidence"][ind]<limit[clss-1]:
            rows_to_drop.append(ind)
            n_discard[clss-1] += 1
        else:
            n_taken[clss-1] += 1
            n_BAM[clss-1] += data_p["Confidence"][ind]
    for i in range(n_categ):
        BAM_percentatge = 0
        if n_taken[i] > 0:
            BAM_percentatge = (n_BAM[i]/n_taken[i])*100

        classification_results_pd.loc[len(classification_results_pd.index)] = [i+1, n_taken[i], BAM_percentatge, n_discard[i]]
    data_final = data_p.drop(rows_to_drop)

    # Save the resulting predictions on an excel file
    dir_path = os.path.dirname(path_predict)
    new_excel_path = os.path.join(dir_path, "Predictions.xlsx")
    data_final.to_excel(new_excel_path)

    # Save the results dataframe as an excel file with two sheets, the first one with training results
    # and the second one with classification results
    writerpath = os.path.join(dir_path, "Model_analisis.xlsx")
    writer = pd.ExcelWriter(writerpath, engine='xlsxwriter')
    training_results_pd.to_excel(writer, sheet_name='Training Results')
    classification_results_pd.to_excel(writer, sheet_name='classification Results')
    writer.close()

    # Generating histogram of categories per point as output
    Path_points = os.path.join(dir_path, "River_points.xlsx")
    Points_data = pd.read_excel(Path_points)

    for i in range(n_categ):
        name = "P_" + str(i+1)
        Points_data[name] = 0
    Points_data["P_T"] = 0

    for ind in data_final.index:
        point = data_final["id"][ind]
        categ = data_final["predicted_CES"][ind]
        name = "P_" + str(categ)
        Points_data.at[point-1, name] += 1
        Points_data.at[point-1, "P_T"] += 1

    total = 0
    for x in Points_data["P_T"]:
        total += x

    # Saving the resulting histogram on an excel file
    Points_data = Points_data.drop(columns=['dis', 'distance', 'angle', 'id', 'Dist'])
    histogram_path = os.path.join(dir_path, "PointsHistogram.xlsx")
    Points_data.to_excel(histogram_path, index=False)