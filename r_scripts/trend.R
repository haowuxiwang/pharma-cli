# Trend analysis R script
# Input: JSON with fields: values, time (optional timestamps), test_type (cusum, ewma, runs)
# Output: JSON to stdout

library(jsonlite)

input <- fromJSON(file("stdin"))
values <- as.numeric(input$values)
values <- values[!is.na(values)]
test_type <- ifelse(is.null(input$test_type), "cusum", input$test_type)

n <- length(values)
if (n < 2) stop("Need at least 2 data points")

# CUSUM analysis
if (test_type == "cusum") {
  target <- ifelse(is.null(input$target), mean(values), input$target)
  k <- ifelse(is.null(input$k), 0.5 * sd(values), input$k)
  h <- ifelse(is.null(input$h), 5 * sd(values), input$h)

  cusum_pos <- numeric(n)
  cusum_neg <- numeric(n)
  alarm <- rep(FALSE, n)

  for (i in 2:n) {
    cusum_pos[i] <- max(0, cusum_pos[i-1] + (values[i] - target) - k)
    cusum_neg[i] <- max(0, cusum_neg[i-1] - (values[i] - target) - k)
    if (cusum_pos[i] > h || cusum_neg[i] > h) {
      alarm[i] <- TRUE
    }
  }

  result <- list(
    test_type = "cusum",
    target = round(target, 4),
    k = round(k, 4),
    h = round(h, 4),
    cusum_pos = round(cusum_pos, 4),
    cusum_neg = round(cusum_neg, 4),
    alarm_points = which(alarm),
    n_alarms = sum(alarm),
    interpretation = ifelse(sum(alarm) > 0,
      paste(sum(alarm), "alarm(s) detected - process may have shifted"),
      "No alarms detected - process appears stable"
    )
  )

} else if (test_type == "ewma") {
  # EWMA chart
  lambda <- ifelse(is.null(input$lambda), 0.2, input$lambda)
  target <- ifelse(is.null(input$target), mean(values), input$target)
  sigma <- sd(values)

  ewma <- numeric(n)
  ewma[1] <- values[1]
  for (i in 2:n) {
    ewma[i] <- lambda * values[i] + (1 - lambda) * ewma[i-1]
  }

  L <- 3
  ucl <- target + L * sigma * sqrt(lambda / (2 - lambda))
  lcl <- target - L * sigma * sqrt(lambda / (2 - lambda))

  in_control <- ewma >= lcl & ewma <= ucl

  result <- list(
    test_type = "ewma",
    lambda = lambda,
    target = round(target, 4),
    ewma_values = round(ewma, 4),
    ucl = round(ucl, 4),
    lcl = round(lcl, 4),
    in_control = in_control,
    out_of_control_points = which(!in_control),
    interpretation = ifelse(all(in_control),
      "Process is in statistical control",
      paste(sum(!in_control), "out-of-control point(s) detected")
    )
  )

} else if (test_type == "runs") {
  # Runs test for randomness
  median_val <- median(values)
  above <- as.integer(values > median_val)

  # Count runs
  runs <- 1
  for (i in 2:n) {
    if (above[i] != above[i-1]) runs <- runs + 1
  }

  n_above <- sum(above)
  n_below <- n - n_above

  # Expected runs and variance
  if (n_above > 0 && n_below > 0) {
    expected_runs <- (2 * n_above * n_below) / n + 1
    var_runs <- (2 * n_above * n_below * (2 * n_above * n_below - n)) / (n^2 * (n - 1))
    se_runs <- sqrt(var_runs)
    z_runs <- (runs - expected_runs) / se_runs
    p_value <- 2 * pnorm(-abs(z_runs))
  } else {
    expected_runs <- runs
    z_runs <- 0
    p_value <- 1
  }

  result <- list(
    test_type = "runs",
    n = n,
    median = round(median_val, 4),
    n_above_median = n_above,
    n_below_median = n_below,
    observed_runs = runs,
    expected_runs = round(expected_runs, 2),
    z_statistic = round(z_runs, 4),
    p_value = round(p_value, 4),
    random = p_value > 0.05,
    interpretation = ifelse(p_value > 0.05,
      "Data appears to be random (p > 0.05)",
      "Data shows non-random pattern (p <= 0.05) - possible trend or shift"
    )
  )

} else {
  stop(paste("Unknown test type:", test_type))
}

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
