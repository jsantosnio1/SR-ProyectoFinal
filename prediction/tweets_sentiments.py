# -*- coding: utf-8 -*-
import datetime
import numpy as np
import pandas as pd 
import os
import matplotlib.pyplot as plt
#!pip install vaderSentiment
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def analysTweets(df, prefijoEmpresa):

    tweets = pd.read_csv(df)
    tweets.columns = ["tweet_id","writer","post_date","body","comment_num","retweet_num","like_num"]

    analyzer = SentimentIntensityAnalyzer()
    sentences = tweets["body"]
    sentenceSample = sentences[:10]
    sentenceSampleDf=pd.DataFrame(sentenceSample)


    # sentenceSampleDf
    def negativityCheck(sentence):
        if(analyzer.polarity_scores(sentence)["neg"]>0.1):
            return 1
        else:
            return 0

    sentenceSampleDf["negative"]=pd.DataFrame(sentenceSample.apply(negativityCheck).tolist())


    # sentenceSampleDf
    def neutralCheck(sentence):
        if(analyzer.polarity_scores(sentence)["neu"]>0.1):
            return 1
        else:
            return 0

    sentenceSampleDf["neutral"]=pd.DataFrame(sentenceSample.apply(neutralCheck).tolist())

    # sentenceSampleDf
    # sentenceSample.head()
    # tweets.shape
    #tweets.head(5)

    def positiveCheck(sentence):
        if(analyzer.polarity_scores(sentence)["pos"]>0.05):
            return 1
        else:
            return 0

    sentenceSampleDf["positive"]=pd.DataFrame(sentenceSample.apply(positiveCheck).tolist())
    #sentenceSampleDf
    #sentenceSample.head()
    #tweets.shape
    tweets["negative_sentiment"] = sentenceSampleDf["negative"]=pd.DataFrame(sentences.apply(negativityCheck).tolist())
    tweets["neutral_sentiment"] = sentenceSampleDf["neutral"]=pd.DataFrame(sentences.apply(neutralCheck).tolist())

    tweets["positive_sentiment"] = sentenceSampleDf["positive"]=pd.DataFrame(sentences.apply(positiveCheck).tolist())
       #tweets.head(5)

    negativeTweeets = tweets.loc[tweets["negative_sentiment"]==1]
    # negativeTweeets.head(5)
    neutralTweeets = tweets.loc[tweets["neutral_sentiment"]==1]
    positiveTweeets = tweets.loc[tweets["positive_sentiment"]==1]

    #tweets.ticker_symbol.unique()

    # """AMAZON"""
    # amazonDf = pd.read_csv("/content/drive/MyDrive/UNIVERSIDAD/8vo/Sistemas de Recomendación con BigData/Tweets about top companies/AMZN.csv")
    # amazonDf.head(5)
    """Negative Tweets Amazon """
    negativeTweetsAmazon = negativeTweeets#.loc[negativeTweeets['ticker_symbol'] =="AMZN"]
    # negativeTopUsersTweetsAmazon = negativeTweeets.loc[negativeTweeets['retweet_num'] > 10]
    """Positive Tweets Amazon"""
    neutralTweetsAmazon = neutralTweeets#.loc[positiveTweeets['ticker_symbol'] =="AMZN"]
    positiveTweetsAmazon = positiveTweeets#.loc[positiveTweeets['ticker_symbol'] =="AMZN"]

    # positiveTopUsersTweetsAmazon = positiveTweeets.loc[positiveTweeets['retweet_num'] > 10]
    # """Positive and Negative Top Users Amazon"""
    # negativeTopUsersTweetsAmazon.head(5)
    # positiveTopUsersTweetsAmazon.head(5)
    """Negative And Positive Tweets of Amazon"""
    # negativeTweetsAmazon.head(5)
    # positiveTweetsAmazon.head(5)
    negativeTweetsAmazon['post_date'] = pd.to_datetime(negativeTweetsAmazon['post_date'],unit='s').dt.strftime('%d-%m-%Y')
    neutralTweetsAmazon['post_date'] = pd.to_datetime(neutralTweetsAmazon['post_date'],unit='s').dt.strftime('%d-%m-%Y')
    positiveTweetsAmazon['post_date'] = pd.to_datetime(positiveTweetsAmazon['post_date'],unit='s').dt.strftime('%d-%m-%Y')
    
    # amazonNegativeInfluence= pd.merge(negativeTweetsAmazon,amazonDf,on="Date",how="inner")
    # amazonPositiveInfluence= pd.merge(positiveTweetsAmazon,amazonDf,on="Date",how="inner")
    # amazonNegativeInfluence.head(5)

    # amazonPositiveInfluence.head(5)

    negativeTweetsOnAmazonDateCount= negativeTweetsAmazon["post_date"].value_counts()
    neutralTweetsOnAmazonDateCount= neutralTweetsAmazon["post_date"].value_counts()
    positiveTweetsOnAmazonDateCount= positiveTweetsAmazon["post_date"].value_counts()


    negativeTweetsOnAmazonDateCount = pd.DataFrame(negativeTweetsOnAmazonDateCount)
    negativeTweetsOnAmazonDateCount.reset_index(inplace=True)

    neutralTweetsOnAmazonDateCount = pd.DataFrame(neutralTweetsOnAmazonDateCount)
    neutralTweetsOnAmazonDateCount.reset_index(inplace=True)

    positiveTweetsOnAmazonDateCount = pd.DataFrame(positiveTweetsOnAmazonDateCount)
    positiveTweetsOnAmazonDateCount.reset_index(inplace=True)

    # positiveTweetsOnAmazonDateCount.head(5)

    # negativeTweetsOnAmazonDateCount.head(5)


    negativeTweetsOnAmazonDateCount["countNegative"] = negativeTweetsOnAmazonDateCount["post_date"]
    negativeTweetsOnAmazonDateCount.drop("post_date",axis=1,inplace=True)
    negativeTweetsOnAmazonDateCount["post_date"] = negativeTweetsOnAmazonDateCount["index"]

    neutralTweetsOnAmazonDateCount["countNeutral"] = neutralTweetsOnAmazonDateCount["post_date"]
    neutralTweetsOnAmazonDateCount.drop("post_date",axis=1,inplace=True)
    neutralTweetsOnAmazonDateCount["post_date"] = neutralTweetsOnAmazonDateCount["index"]

    positiveTweetsOnAmazonDateCount["countPositive"] = positiveTweetsOnAmazonDateCount["post_date"]
    positiveTweetsOnAmazonDateCount.drop("post_date",axis=1,inplace=True)
    positiveTweetsOnAmazonDateCount["post_date"] = positiveTweetsOnAmazonDateCount["index"]



    amazonInfluenceByNo= negativeTweetsOnAmazonDateCount#pd.merge(negativeTweetsOnAmazonDateCount,amazonDf,on="post_date",how="inner")

    amazonInfluenceByNeu= neutralTweetsOnAmazonDateCount#pd.merge(positiveTweetsOnAmazonDateCount,amazonDf,on="post_date",how="inner")

    amazonInfluenceByYes= positiveTweetsOnAmazonDateCount#pd.merge(positiveTweetsOnAmazonDateCount,amazonDf,on="post_date",how="inner")

    # amazonInfluenceByNo.head(5)

    # amazonInfluenceByYes.head(5)


    fig, ax = plt.subplots(figsize=(15,15))

    amazonInfluenceByNo["dateTime"] = pd.to_datetime(amazonInfluenceByNo["post_date"])
    amazonInfluenceByNo = amazonInfluenceByNo.sort_values(by="dateTime")

    amazonInfluenceByNeu["dateTime"] = pd.to_datetime(amazonInfluenceByNeu["post_date"])
    amazonInfluenceByNeu = amazonInfluenceByNeu.sort_values(by="dateTime")  
    
    amazonInfluenceByYes["dateTime"] = pd.to_datetime(amazonInfluenceByYes["post_date"])
    amazonInfluenceByYes = amazonInfluenceByYes.sort_values(by="dateTime")  


    #openingValues= amazonInfluenceByNo["Open"]
    #closingValues = amazonInfluenceByNo["Close"]
    countNegativeTweet = amazonInfluenceByNo["countNegative"]
    countNeutralTweet = amazonInfluenceByNeu["countNeutral"]
    countPositiveTweet = amazonInfluenceByYes["countPositive"]


    datesNo = amazonInfluenceByNo["dateTime"]
    datesNeu = amazonInfluenceByNeu["dateTime"]
    datesYes = amazonInfluenceByYes["dateTime"]
    # print('***'*100)

    # print(countNegativeTweet.head(20))
    # print('***'*100)
    # print(countPositiveTweet.head(20))
    # print('***'*100)
    # print(datesNo.head(20))
    # print('***'*100)
    # print(datesYes.head(20))
    # print('***'*100)
    # # ax.plot(dates,openingValues,label="open")
    # ax.plot(dates,closingValues,label="close")
    ax.plot(datesYes,countPositiveTweet,label="N° of Positive of Tweets")

    ax.plot(datesNo,countNegativeTweet,label="N° of Negative of Tweets")
    ax.plot(datesNeu,countNeutralTweet,label="N° of Neutral of Tweets")


    ax.legend()

    pathImage = 'static/graficas/sentiments_tweets_'+prefijoEmpresa+'.png'
    ax.figure.savefig(pathImage)    
    pathImage = pathImage.replace('static/', '')

    return pathImage