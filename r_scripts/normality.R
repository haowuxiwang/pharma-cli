# Normality test R script
# Input: JSON from stdin with field "values" (numeric vector)
# Output: JSON to stdout

library(jsonlite)
library(nortest)
library(base64enc)

input <- fromJSON(file("stdin"))
values <- as.numeric(input$values)
values <- values[!is.na(values)]

if (length(values) < 3) {
  stop("Need at least 3 data points for normality test")
}

n <- length(values)

# Shapiro-Wilk test (best for n < 5000)
if (n <= 5000) {
  sw <- shapiro.test(values)
  sw_stat <- sw$statistic
  sw_p <- sw$p.value
} else {
  # For large samples, use Anderson-Darling
  ad <- ad.test(values)
  sw_stat <- ad$statistic
  sw_p <- ad$p.value
}

# Anderson-Darling test (requires n > 7)
if (n > 7) {
  ad <- ad.test(values)
  ad_stat <- ad$statistic
  ad_p <- ad$p.value
} else {
  ad_stat <- NA
  ad_p <- NA
}

# Lilliefors (Kolmogorov-Smirnov) test (requires n >= 5)
if (n >= 5) {
  lillie <- lillie.test(values)
  lillie_stat <- lillie$statistic
  lillie_p <- lillie$p.value
} else {
  lillie_stat <- NA
  lillie_p <- NA
}

is_normal <- sw_p > 0.05

# Histogram data
hist_obj <- hist(values, plot = FALSE, breaks = "Sturges")
hist_x <- (hist_obj$breaks[-1] + head(hist_obj$breaks, -1)) / 2
hist_counts <- hist_obj$counts

# Normal curve
x_range <- seq(min(values) - 3 * sd(values), max(values) + 3 * sd(values), length.out = 100)
normal_curve_y <- dnorm(x_range, mean(values), sd(values))

# Q-Q plot data
theoretical_q <- qnorm(ppoints(n))
sorted_data <- sort(values)
sorted_standardized <- (sorted_data - mean(values)) / sd(values)

result <- list(
  shapiro_wilk = list(
    statistic = round(as.numeric(sw_stat), 4),
    p_value = round(as.numeric(sw_p), 4),
    is_normal = is_normal
  ),
  anderson_darling = list(
    statistic = ifelse(is.na(ad_stat), NA, round(as.numeric(ad_stat), 4)),
    p_value = ifelse(is.na(ad_p), NA, round(as.numeric(ad_p), 4))
  ),
  lilliefors = list(
    statistic = ifelse(is.na(lillie_stat), NA, round(as.numeric(lillie_stat), 4)),
    p_value = ifelse(is.na(lillie_p), NA, round(as.numeric(lillie_p), 4))
  ),
  is_normal = is_normal,
  interpretation = ifelse(is_normal,
    "Data follows a normal distribution (p > 0.05)",
    "Data does NOT follow a normal distribution (p <= 0.05)"
  ),
  histogram = list(
    x = round(hist_x, 4),
    counts = as.integer(hist_counts)
  ),
  normal_curve = list(
    x = round(x_range, 4),
    y = round(normal_curve_y, 6)
  ),
  qq_plot = list(
    theoretical = round(theoretical_q, 4),
    sample = round(sorted_standardized, 4)
  )
)

# Generate plot if requested
if (!is.null(input$generate_plot) && input$generate_plot == TRUE) {
  tryCatch({
    # Create temp file for PNG
    tmp_file <- tempfile(fileext = ".png")
    on.exit(unlink(tmp_file))

    # Generate plot with two panels
    png(tmp_file, width = 1000, height = 500, res = 100)
    par(mfrow = c(1, 2), mar = c(5, 4, 4, 2) + 0.1)

    # Panel 1: Histogram with normal curve
    hist(values, breaks = "Sturges", col = "lightblue", border = "white",
         main = "Histogram with Normal Curve",
         xlab = "Value", ylab = "Frequency", probability = TRUE)
    lines(x_range, normal_curve_y, col = "red", lwd = 2)
    legend("topright", legend = c("Normal Curve"), col = "red", lwd = 2)

    # Panel 2: Q-Q plot
    qqnorm(values, main = "Q-Q Plot", pch = 19, col = "blue")
    qqline(values, col = "red", lwd = 2)

    dev.off()

    # Read and encode to base64
    raw_bytes <- readBin(tmp_file, "raw", file.info(tmp_file)$size)
    result$plot <- base64enc::base64encode(raw_bytes)
  }, error = function(e) {
    result$plot_error <- as.character(e)
  })
}

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
