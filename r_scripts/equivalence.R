# Equivalence test R script
# Input: JSON with fields: test_type, x, y (for tost), mu (for one_sample_tost), delta
# Output: JSON to stdout

library(jsonlite)

input <- fromJSON(file("stdin"))
test_type <- ifelse(is.null(input$test_type), "tost", input$test_type)

if (test_type == "tost") {
  # Two One-Sided Tests (TOST) for equivalence
  if (is.null(input$x) || is.null(input$y)) {
    stop("x and y required for two-sample TOST")
  }
  if (is.null(input$delta)) {
    stop("delta (equivalence margin) required for TOST")
  }

  x <- as.numeric(input$x)
  y <- as.numeric(input$y)
  delta <- as.numeric(input$delta)

  n_x <- length(x)
  n_y <- length(y)
  mean_x <- mean(x)
  mean_y <- mean(y)
  sd_x <- sd(x)
  sd_y <- sd(y)

  # Pooled standard deviation
  sp <- sqrt(((n_x - 1) * sd_x^2 + (n_y - 1) * sd_y^2) / (n_x + n_y - 2))

  # Standard error
  se <- sp * sqrt(1/n_x + 1/n_y)

  # Mean difference
  diff <- mean_x - mean_y

  # TOST procedure
  t1 <- (diff + delta) / se
  t2 <- (diff - delta) / se

  df <- n_x + n_y - 2
  p1 <- pt(t1, df, lower.tail = FALSE)
  p2 <- pt(t2, df, lower.tail = TRUE)

  p_value <- max(p1, p2)

  # 90% confidence interval for the difference
  t_crit <- qt(0.05, df, lower.tail = FALSE)
  ci_lower <- diff - t_crit * se
  ci_upper <- diff + t_crit * se

  output <- list(
    test_type = "tost",
    n_x = n_x,
    n_y = n_y,
    mean_x = round(mean_x, 4),
    mean_y = round(mean_y, 4),
    mean_difference = round(diff, 4),
    delta = delta,
    t_statistic_1 = round(t1, 4),
    t_statistic_2 = round(t2, 4),
    p_value_1 = round(p1, 4),
    p_value_2 = round(p2, 4),
    p_value = round(p_value, 4),
    ci_90_lower = round(ci_lower, 4),
    ci_90_upper = round(ci_upper, 4),
    equivalent = p_value < 0.05,
    interpretation = ifelse(p_value < 0.05,
      paste0("Groups are equivalent within the specified margin (delta = ", delta, ", p < 0.05)"),
      paste0("Groups are NOT equivalent within the specified margin (delta = ", delta, ", p >= 0.05)"))
  )

} else if (test_type == "one_sample_tost") {
  # One-sample TOST
  if (is.null(input$x)) {
    stop("x required for one-sample TOST")
  }
  if (is.null(input$mu)) {
    stop("mu (hypothesized mean) required for one-sample TOST")
  }
  if (is.null(input$delta)) {
    stop("delta (equivalence margin) required for TOST")
  }

  x <- as.numeric(input$x)
  mu <- as.numeric(input$mu)
  delta <- as.numeric(input$delta)

  n <- length(x)
  mean_x <- mean(x)
  sd_x <- sd(x)

  # Standard error
  se <- sd_x / sqrt(n)

  # Difference from hypothesized mean
  diff <- mean_x - mu

  # TOST procedure
  t1 <- (diff + delta) / se
  t2 <- (diff - delta) / se

  df <- n - 1
  p1 <- pt(t1, df, lower.tail = FALSE)
  p2 <- pt(t2, df, lower.tail = TRUE)

  p_value <- max(p1, p2)

  # 90% confidence interval for the difference
  t_crit <- qt(0.05, df, lower.tail = FALSE)
  ci_lower <- diff - t_crit * se
  ci_upper <- diff + t_crit * se

  output <- list(
    test_type = "one_sample_tost",
    n = n,
    sample_mean = round(mean_x, 4),
    mu = mu,
    mean_difference = round(diff, 4),
    delta = delta,
    t_statistic_1 = round(t1, 4),
    t_statistic_2 = round(t2, 4),
    p_value_1 = round(p1, 4),
    p_value_2 = round(p2, 4),
    p_value = round(p_value, 4),
    ci_90_lower = round(ci_lower, 4),
    ci_90_upper = round(ci_upper, 4),
    equivalent = p_value < 0.05,
    interpretation = ifelse(p_value < 0.05,
      paste0("Sample mean is equivalent to the specified value (mu = ", mu, ", delta = ", delta, ", p < 0.05)"),
      paste0("Sample mean is NOT equivalent to the specified value (mu = ", mu, ", delta = ", delta, ", p >= 0.05)"))
  )

} else {
  stop(paste("Unknown test type:", test_type))
}

cat(toJSON(output, auto_unbox = TRUE, pretty = TRUE))
