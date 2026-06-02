# Data Cleaning Command
# Input: JSON with values and cleaning options
# Output: JSON with cleaned data and cleaning report

library(jsonlite)

# Read input from stdin
input <- fromJSON(readLines(file("stdin"), warn = FALSE))

values <- as.numeric(input$values)
method <- input$method  # drop, impute_mean, impute_median, winsorize, clip
n_original <- length(values)

result <- tryCatch({
  if (method == "drop") {
    # Drop NA/NaN/Inf values
    clean <- values[!is.na(values) & is.finite(values)]
    n_removed <- n_original - length(clean)
    method_desc <- "Dropped missing and infinite values"

  } else if (method == "impute_mean") {
    # Impute missing values with mean
    valid <- values[!is.na(values) & is.finite(values)]
    mean_val <- mean(valid)
    clean <- ifelse(is.na(values) | !is.finite(values), mean_val, values)
    n_removed <- sum(is.na(values) | !is.finite(values))
    method_desc <- sprintf("Imputed %d missing values with mean = %.4f", n_removed, mean_val)

  } else if (method == "impute_median") {
    # Impute missing values with median
    valid <- values[!is.na(values) & is.finite(values)]
    median_val <- median(valid)
    clean <- ifelse(is.na(values) | !is.finite(values), median_val, values)
    n_removed <- sum(is.na(values) | !is.finite(values))
    method_desc <- sprintf("Imputed %d missing values with median = %.4f", n_removed, median_val)

  } else if (method == "winsorize") {
    # Winsorize outliers (cap at percentiles)
    lower_pct <- ifelse(!is.null(input$lower_pct), input$lower_pct, 0.05)
    upper_pct <- ifelse(!is.null(input$upper_pct), input$upper_pct, 0.95)

    valid <- values[!is.na(values) & is.finite(values)]
    lower_bound <- quantile(valid, lower_pct)
    upper_bound <- quantile(valid, upper_pct)

    clean <- values
    clean[clean < lower_bound] <- lower_bound
    clean[clean > upper_bound] <- upper_bound
    n_removed <- sum(values < lower_bound | values > upper_bound, na.rm = TRUE)
    method_desc <- sprintf("Winsorized at %.1f%% and %.1f%% (%.4f to %.4f)",
                           lower_pct * 100, upper_pct * 100, lower_bound, upper_bound)

  } else if (method == "clip") {
    # Clip values to specified range
    lower <- ifelse(!is.null(input$lower), input$lower, -Inf)
    upper <- ifelse(!is.null(input$upper), input$upper, Inf)

    clean <- values
    clean[clean < lower] <- lower
    clean[clean > upper] <- upper
    n_removed <- sum(values < lower | values > upper, na.rm = TRUE)
    method_desc <- sprintf("Clipped to range [%.4f, %.4f]", lower, upper)

  } else {
    stop(paste("Unknown cleaning method:", method))
  }

  # Calculate statistics before and after
  valid_before <- values[!is.na(values) & is.finite(values)]
  valid_after <- clean[!is.na(clean) & is.finite(clean)]

  list(
    method = method,
    method_desc = method_desc,
    n_original = n_original,
    n_clean = length(valid_after),
    n_removed = n_removed,
    before = list(
      mean = round(mean(valid_before), 4),
      sd = round(sd(valid_before), 4),
      min = min(valid_before),
      max = max(valid_before),
      n_na = sum(is.na(values)),
      n_inf = sum(!is.na(values) & !is.finite(values))
    ),
    after = list(
      mean = round(mean(valid_after), 4),
      sd = round(sd(valid_after), 4),
      min = min(valid_after),
      max = max(valid_after)
    ),
    values = clean,
    interpretation = sprintf("Cleaned %d values using %s. %d values affected.",
                             n_original, method, n_removed)
  )
}, error = function(e) {
  list(
    error = TRUE,
    message = conditionMessage(e),
    method = method
  )
})

# Output JSON
toJSON(result, auto_unbox = TRUE, pretty = TRUE)
