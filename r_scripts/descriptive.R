# Descriptive statistics R script
# Input: JSON from stdin with field "values" (numeric vector)
# Output: JSON to stdout

library(jsonlite)

input <- fromJSON(file("stdin"))
values <- as.numeric(input$values)
values <- values[!is.na(values)]

if (length(values) < 1) {
  stop("No valid data points")
}

n <- length(values)
mean_val <- mean(values)
median_val <- median(values)
std_val <- sd(values)
rsd <- (std_val / mean_val * 100) * (mean_val != 0)
min_val <- min(values)
max_val <- max(values)
range_val <- max_val - min_val
q1 <- quantile(values, 0.25, names = FALSE)
q3 <- quantile(values, 0.75, names = FALSE)
iqr_val <- IQR(values)

# 95% CI
if (n > 1) {
  se <- std_val / sqrt(n)
  t_crit <- qt(0.975, df = n - 1)
  ci_lower <- mean_val - t_crit * se
  ci_upper <- mean_val + t_crit * se
} else {
  ci_lower <- mean_val
  ci_upper <- mean_val
}

# Skewness and kurtosis
if (n > 2) {
  skewness <- mean((values - mean_val)^3) / std_val^3
  kurtosis <- mean((values - mean_val)^4) / std_val^4 - 3
} else {
  skewness <- 0
  kurtosis <- 0
}

result <- list(
  n = n,
  mean = round(mean_val, 4),
  median = round(median_val, 4),
  std = round(std_val, 4),
  rsd_percent = round(rsd, 2),
  min = round(min_val, 4),
  max = round(max_val, 4),
  range = round(range_val, 4),
  q1 = round(q1, 4),
  q3 = round(q3, 4),
  iqr = round(iqr_val, 4),
  ci_95_lower = round(ci_lower, 4),
  ci_95_upper = round(ci_upper, 4),
  skewness = round(skewness, 4),
  kurtosis = round(kurtosis, 4)
)

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
