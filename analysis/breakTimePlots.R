library(ggplot2)
library(gplots)
library(dichromat)
library(scales)
# Read Data
breakData = read.csv("breaks.csv")
timeformat="%Y-%m-%dT%H:%M:%S"
breakTimes <- lapply(breakData[2], function(ts){as.POSIXct(strptime(ts,timeformat,tz="GMT"))})[[1]]
breakData['time'] = breakTimes
breakData['date'] = as.Date(breakTimes, tz="America/New_York")
breakData['hour'] = sapply(breakTimes, function(t){strftime(t,"%H",tz="America/New_York")})
breakData['weekday'] = sapply(breakTimes, function(t){strftime(t, "%A",tz="America/New_York")})

isWeekend = (breakData['weekday'] == 'Saturday') | (breakData['weekday'] == 'Sunday')
dayLabel = rep('Weekday', nrow(breakData))
dayLabel[isWeekend] = 'Weekend'
breakData['dayType'] = dayLabel


breakData$weekday <- factor(breakData$weekday,
                       levels = c("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"))
# Get the Day and Hour from a POSIXct object. Convert to local time.
getDayHour = function(t)
{
  day = as.numeric(strftime(t, "%w",tz="America/New_York")) # 0 is Sunday
  hour = as.numeric(strftime(t, "%H",tz="America/New_York"))
return(c(day,hour))
}

dayHourBin <- sapply(1:length(breakTimes),function(i){getDayHour(breakTimes[i])})

t <- table(dayHourBin[1,],dayHourBin[2,])
breakMat = as.matrix(t)
rownames(breakMat) = c("Sun", "Mon", "Tues", "Wed", "Thurs", "Fri", "Sat")
colnames(breakMat) = as.numeric(0:23)
breakMat = breakMat[c(2,3,4,5,6,7,1),]
breakMatNorm = as.matrix(breakMat)/rowSums(breakMat)

heatmap.2(breakMat, main=c("Break Counts\nby Time of Day"), dendrogram=c("none"),
          col=colorschemes$BluetoOrange.12, Colv=F, Rowv=F, trace="none", sepwidth=c(1,1))
cellLabels = as.matrix(sprintf("%.1f", 100*breakMatNorm))
dim(cellLabels) = dim(breakMatNorm)

heatmap.2(breakMatNorm, main=c("Break Frequency\nby Time of Day"), dendrogram=c("none"),
          col=colorschemes$BluetoOrange.12, Colv=F, Rowv=F, trace="none", colsep=1:ncol(breakMatNorm),
          rowsep=1:nrow(breakMatNorm), sepwidth=c(0.1,0.1), cellnote=cellLabels, notecol="black")

# Plot the count of breaks base on the hour
p <- qplot(hour, data=breakData, facets = weekday ~ .) + xlab("Hour") + ylab("Break Count") + ggtitle("Break Counts vs. Time of Day")
p

breakDataWeekdays <- breakData[breakData['dayType'] == 'Weekday',]
breakDataWeekends <- breakData[breakData['dayType'] == 'Weekend',]

p2 <- ggplot(breakDataWeekdays,aes(x=hour)) + stat_bin(aes(n=nrow(breakDataWeekdays), y=..count../n))+ scale_y_continuous(labels=percent_format())+ ylab("Percentage of Breaks") + ggtitle('Breaks by time of day, Weekdays')+ xlab('Hour')
weekdayHist <- hist(as.numeric(breakDataWeekdays[['hour']]), breaks=24)
sprintf('Percentage of breaks at 5 AM weekdays: %f', 100.0*weekdayHist$density[5])

p3 <- ggplot(breakDataWeekends,aes(x=hour)) + stat_bin(aes(n=nrow(breakDataWeekends), y=..count../n))+ scale_y_continuous(labels=percent_format())+ ylab("Percentage of Breaks") + ggtitle('Breaks by time of day, Weekends') + xlab('Hour')
plotTheme <- theme(axis.title.x = element_text(face="bold", colour="black", size=20), 
                 axis.text.x  = element_text(angle=90, vjust=0.5, size=16, colour="black"), 
                 axis.title.y = element_text(face="bold", colour="black", size=20), 
                 axis.text.y  = element_text(size=14, colour="black"),
                 title = element_text(size=18, colour="black"))
p2 <- p2 + plotTheme
p3 <- p3 + plotTheme
p2
p3
weekendHist <- hist(as.numeric(breakDataWeekends[['hour']]), breaks=24)
sprintf('Percentage of breaks at 7 AM weekends: %f', 100.0*weekendHist$density[7])
