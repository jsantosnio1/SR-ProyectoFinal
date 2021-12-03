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
    analyzer = SentimentIntensityAnalyzer()
    sentences = tweets["body"]
    sentenceSample = sentences[:10]
    sentenceSampleDf=pd.DataFrame(sentenceSample)
    # sentenceSampleDf
    def negativityCheck(sentence):
        if(analyzer.polarity_scores(sentence)["neg"]>0.7):
            return 1
        else:
            return 0

    sentenceSampleDf["negative"]=pd.DataFrame(sentenceSample.apply(negativityCheck).tolist())

    # sentenceSampleDf
    # sentenceSample.head()
    # tweets.shape
    tweets["negative_sentiment"] = sentenceSampleDf["negative"]=pd.DataFrame(sentences.apply(negativityCheck).tolist())
    #tweets.head(5)

    def positiveCheck(sentence):
        if(analyzer.polarity_scores(sentence)["pos"]>0.7):
            return 1
        else:
            return 0

    sentenceSampleDf["positive"]=pd.DataFrame(sentenceSample.apply(positiveCheck).tolist())
    #sentenceSampleDf
    #sentenceSample.head()
    #tweets.shape
    tweets["positive_sentiment"] = sentenceSampleDf["positive"]=pd.DataFrame(sentences.apply(positiveCheck).tolist())
       #tweets.head(5)
    negativeTweeets = tweets.loc[tweets["negative_sentiment"]==1]
    # negativeTweeets.head(5)
    positiveTweeets = tweets.loc[tweets["positive_sentiment"]==1]
    tweets.ticker_symbol.unique()

    # """AMAZON"""
    # amazonDf = pd.read_csv("/content/drive/MyDrive/UNIVERSIDAD/8vo/Sistemas de Recomendación con BigData/Tweets about top companies/AMZN.csv")
    # amazonDf.head(5)
    amazonDf = tweets
    """Negative Tweets Amazon """
    negativeTweetsAmazon = negativeTweeets#.loc[negativeTweeets['ticker_symbol'] =="AMZN"]
    # negativeTopUsersTweetsAmazon = negativeTweeets.loc[negativeTweeets['retweet_num'] > 10]
    """Positive Tweets Amazon"""
    positiveTweetsAmazon = positiveTweeets#.loc[positiveTweeets['ticker_symbol'] =="AMZN"]
    # positiveTopUsersTweetsAmazon = positiveTweeets.loc[positiveTweeets['retweet_num'] > 10]
    # """Positive and Negative Top Users Amazon"""
    # negativeTopUsersTweetsAmazon.head(5)
    # positiveTopUsersTweetsAmazon.head(5)
    """Negative And Positive Tweets of Amazon"""
    # negativeTweetsAmazon.head(5)
    # positiveTweetsAmazon.head(5)
    negativeTweetsAmazon['post_date'] = pd.to_datetime(negativeTweetsAmazon['post_date'],unit='s').dt.strftime('%d-%m-%Y')
    positiveTweetsAmazon['post_date'] = pd.to_datetime(positiveTweetsAmazon['post_date'],unit='s').dt.strftime('%d-%m-%Y')
    # amazonNegativeInfluence= pd.merge(negativeTweetsAmazon,amazonDf,on="Date",how="inner")
    # amazonPositiveInfluence= pd.merge(positiveTweetsAmazon,amazonDf,on="Date",how="inner")
    # amazonNegativeInfluence.head(5)

    # amazonPositiveInfluence.head(5)

    negativeTweetsOnAmazonDateCount= negativeTweetsAmazon["post_date"].value_counts()
    positiveTweetsOnAmazonDateCount= positiveTweetsAmazon["post_date"].value_counts()

    negativeTweetsOnAmazonDateCount = pd.DataFrame(negativeTweetsOnAmazonDateCount)
    negativeTweetsOnAmazonDateCount.reset_index(inplace=True)

    positiveTweetsOnAmazonDateCount = pd.DataFrame(positiveTweetsOnAmazonDateCount)
    positiveTweetsOnAmazonDateCount.reset_index(inplace=True)

    # positiveTweetsOnAmazonDateCount.head(5)

    # negativeTweetsOnAmazonDateCount.head(5)

    negativeTweetsOnAmazonDateCount["countNegative"] = negativeTweetsOnAmazonDateCount["post_date"]
    negativeTweetsOnAmazonDateCount.drop("post_date",axis=1,inplace=True)
    negativeTweetsOnAmazonDateCount["post_date"] = negativeTweetsOnAmazonDateCount["index"]

    positiveTweetsOnAmazonDateCount["countPositive"] = positiveTweetsOnAmazonDateCount["post_date"]
    positiveTweetsOnAmazonDateCount.drop("post_date",axis=1,inplace=True)
    positiveTweetsOnAmazonDateCount["post_date"] = positiveTweetsOnAmazonDateCount["index"]

    amazonInfluenceByNo= pd.merge(negativeTweetsOnAmazonDateCount,amazonDf,on="post_date",how="inner")

    amazonInfluenceByYes= pd.merge(positiveTweetsOnAmazonDateCount,amazonDf,on="post_date",how="inner")

    # amazonInfluenceByNo.head(5)

    # amazonInfluenceByYes.head(5)


    fig, ax = plt.subplots(figsize=(15,15))

    amazonInfluenceByNo["post_date"] = pd.to_datetime(amazonInfluenceByNo["post_date"])
    amazonInfluenceByNo = amazonInfluenceByNo.sort_values(by="post_date")

    amazonInfluenceByYes["post_date"] = pd.to_datetime(amazonInfluenceByYes["post_date"])
    amazonInfluenceByYes = amazonInfluenceByYes.sort_values(by="post_date")  


    #openingValues= amazonInfluenceByNo["Open"]
    #closingValues = amazonInfluenceByNo["Close"]
    countNegativeTweet = amazonInfluenceByNo["countNegative"]
    countPositiveTweet = amazonInfluenceByYes["countPositive"]

    datesNo = amazonInfluenceByNo["post_date"]
    datesYes = amazonInfluenceByYes["post_date"]
    # ax.plot(dates,openingValues,label="open")
    # ax.plot(dates,closingValues,label="close")
    ax.plot(datesNo,countNegativeTweet,label="N° of Negative of Tweets")
    ax.plot(datesYes,countPositiveTweet,label="N° of Positive of Tweets")

    ax.legend()

    pathImage = 'prediction/graficas/_sentiments_tweets_'+prefijoEmpresa+'_'+datetime.now+'.png'
    ax.savefig(pathImage)   
    img = ax.imread(pathImage)

    return img