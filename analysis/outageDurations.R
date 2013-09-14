library(ggplot2)
library(scales)
library(plyr)

# Read Data
data <- read.csv("outageStartToDuration.csv")

# Remove long outages (more than 24 hours)

T = 24*60*60.00

outages <- data[data['duration']<T,]

# Get sunday data
sunday = outages[outages['day']==6,]
saturday = outages[outages['day']==5,]
monday = outages[outages['day']==0,]
weekday = outages[outages['day']<4,]
weekend = outages[outages['day']>4,]

p1 <- qplot(dayseconds, duration, data=sunday, main="Sunday")
p2 <- qplot(dayseconds, duration, data=saturday, main="Saturday")
p3 <- qplot(dayseconds, duration, data=monday, main="Monday")
p4 <- qplot(dayseconds, duration, data=weekday, main="Weekday (not Friday)", colour = I(alpha("black", 1/2)), geom="boxplot", group=round_any(hour, 1))
p5 <- qplot(dayseconds, duration, data=weekend, main="Saturday and Sunday", colour = I(alpha("black", 1/2)), geom="boxplot", group=round_any(hour, 1))
