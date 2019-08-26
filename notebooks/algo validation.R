# YUEGE ALgorithm VAlidation

## INITIAL ANALYSIS ##
# Set working directory to location of this file - duh!
library(rstudioapi) 
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

# 1 - Similarity hypothesis of data

# Read in CSV file
#data = read.csv("kabab_house.csv", head = TRUE, sep = ",") # header has column names; CSV 
data = read.csv("dubliner.csv", head = TRUE, sep = ",") # header has column names; CSV 


# Quick look at data that was read in
dim(data)    # rows, cols
head(data)   # header and first few rows
data[1:5,]   # Specific focus [rows, columns] (indexing in R is 1-based)

# Make data columns (x'x and y's) available
attach(data)                # To reference column names directly 

# Does similarity of a user pair's ratings on one restaurnat correlate with ratings on another?  
# Scatter Plot of the user pair's two rating matches 
plot(match1, match2, xlab="Rest1 Rating Sim", ylab="Rest2 Rating Sim", main="Correlation of User Pair Rating Similarity")

# Jittered scatterplot
install.packages("plotrix")
library(plotrix)
plot(cluster.overplot(match1, match2), xlab="Restaurant 1 Rating Similarity", ylab="Restaurant 2 Rating Similarity", main="User Pair Rating Similarity - Dubliner")

# Correlation of variables
cor(match1, match2)

# 2 - ANOVA validation of Algorithm

# Read in CSV file
data = read.csv("kabab_house_anova.csv", head = TRUE, sep = ",") # header has column names; CSV 

attach(data)                # To reference column names directly 

# visulize the similarity by lmu vs. non-lmu 
boxplot(match1~lmu, xlab="Non-LMU vs. LMU User Pairs", ylab="Rating Similarity", main="Rating Similarity between LMU and Non-LMU")


# apply ANOVA
anova_mod = aov(match1~lmu)

# Additional Analysis
## Diagnostic plots
plot(anova_mod)


## More extensive output
summary(anova_mod)
model.tables(anova_mod,type = "means")

## Pairwise comparison
TukeyHSD(anova_mod, conf.level = .95)
