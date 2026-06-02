# Data Transformation Command
# Input: JSON with values and transformation method
# Output: JSON with transformed values

library(jsonlite)

# Read input from stdin
input <- fromJSON(readLines(file("stdin"), warn = FALSE))

values <- as.numeric(input$values)
method <- input$method  # log, sqrt, boxcox, johnson, rank, standardize, recip

result <- tryCatch({
  # Remove NA/NaN/Inf for transformation
  valid_idx <- !is.na(values) & is.finite(values)
  valid_values <- values[valid_idx]

  if (method == "log") {
    # Log transformation
    if (any(valid_values <= 0)) {
      # Add constant to make all values positive
      offset <- abs(min(valid_values)) + 1
      transformed <- log(valid_values + offset)
      method_desc <- sprintf("log(x + %.4f) applied (offset added for non-positive values)", offset)
    } else {
      transformed <- log(valid_values)
      offset <- 0
      method_desc <- "log(x) applied"
    }

  } else if (method == "sqrt") {
    # Square root transformation
    if (any(valid_values < 0)) {
      offset <- abs(min(valid_values))
      transformed <- sqrt(valid_values + offset)
      method_desc <- sprintf("sqrt(x + %.4f) applied (offset added for negative values)", offset)
    } else {
      transformed <- sqrt(valid_values)
      offset <- 0
      method_desc <- "sqrt(x) applied"
    }

  } else if (method == "boxcox") {
    # Box-Cox transformation
    # Find optimal lambda
    if (any(valid_values <= 0)) {
      offset <- abs(min(valid_values)) + 1
      shifted <- valid_values + offset
    } else {
      offset <- 0
      shifted <- valid_values
    }

    # Try different lambda values
    lambdas <- seq(-2, 2, by = 0.1)
    log_likelihood <- sapply(lambdas, function(lam) {
      if (abs(lam) < 0.001) {
        transformed <- log(shifted)
      } else {
        transformed <- (shifted^lam - 1) / lam
      }
      n <- length(transformed)
      -n/2 * log(var(transformed)) + (lam - 1) * sum(log(shifted))
    })

    optimal_lambda <- lambdas[which.max(log_likelihood)]

    if (abs(optimal_lambda) < 0.001) {
      transformed <- log(shifted)
    } else {
      transformed <- (shifted^optimal_lambda - 1) / optimal_lambda
    }

    method_desc <- sprintf("Box-Cox applied with lambda = %.2f", optimal_lambda)

  } else if (method == "johnson") {
    # Johnson transformation (simplified)
    # Use log as approximation
    if (any(valid_values <= 0)) {
      offset <- abs(min(valid_values)) + 1
      transformed <- log(valid_values + offset)
    } else {
      transformed <- log(valid_values)
      offset <- 0
    }
    method_desc <- "Johnson transformation (log approximation) applied"

  } else if (method == "rank") {
    # Rank transformation
    transformed <- rank(valid_values)
    offset <- 0
    method_desc <- "Rank transformation applied"

  } else if (method == "standardize") {
    # Standardize (z-score)
    mean_val <- mean(valid_values)
    sd_val <- sd(valid_values)
    transformed <- (valid_values - mean_val) / sd_val
    offset <- 0
    method_desc <- sprintf("Standardized (z-score) applied: mean = %.4f, sd = %.4f", mean_val, sd_val)

  } else if (method == "recip") {
    # Reciprocal transformation
    if (any(valid_values == 0)) {
      offset <- 0.001
      transformed <- 1 / (valid_values + offset)
      method_desc <- "1/(x + 0.001) applied (offset for zero values)"
    } else {
      transformed <- 1 / valid_values
      offset <- 0
      method_desc <- "1/x applied"
    }

  } else {
    stop(paste("Unknown transformation method:", method))
  }

  # Calculate statistics before and after
  list(
    method = method,
    method_desc = method_desc,
    n = length(valid_values),
    before = list(
      mean = round(mean(valid_values), 4),
      sd = round(sd(valid_values), 4),
      min = min(valid_values),
      max = max(valid_values),
      skewness = round(mean((valid_values - mean(valid_values))^3) / sd(valid_values)^3, 4),
      kurtosis = round(mean((valid_values - mean(valid_values))^4) / sd(valid_values)^4 - 3, 4)
    ),
    after = list(
      mean = round(mean(transformed), 4),
      sd = round(sd(transformed), 4),
      min = min(transformed),
      max = max(transformed),
      skewness = round(mean((transformed - mean(transformed))^3) / sd(transformed)^3, 4),
      kurtosis = round(mean((transformed - mean(transformed))^4) / sd(transformed)^4 - 3, 4)
    ),
    offset = offset,
    values = transformed,
    interpretation = sprintf("%s. Skewness: %.3f -> %.3f, Kurtosis: %.3f -> %.3f",
                             method_desc,
                             mean((valid_values - mean(valid_values))^3) / sd(valid_values)^3,
                             mean((transformed - mean(transformed))^3) / sd(transformed)^3,
                             mean((valid_values - mean(valid_values))^4) / sd(valid_values)^4 - 3,
                             mean((transformed - mean(transformed))^4) / sd(transformed)^4 - 3)
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
