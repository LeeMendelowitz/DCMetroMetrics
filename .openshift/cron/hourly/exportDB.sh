#!/bin/bash
# Dump mongo database as json

collections=('escalator_appstate' 'escalator_statuses' 'escalator_tweet_outbox' 'escalators' 'hotcars' 'hotcars_appstate' 'hotcars_manual_tweets' 'hotcars_tweeters' 'hotcars_tweets' 'symptom_codes' 'webpages')

for name in "${collections[@]}"
do
    mongoexport -host $OPENSHIFT_MONGODB_DB_HOST -d MetroEscalators -u $OPENSHIFT_MONGODB_DB_USERNAME -p $OPENSHIFT_MONGODB_DB_PASSWORD -c $name > $OPENSHIFT_DATA_DIR/mongoexport/$name.json
done
