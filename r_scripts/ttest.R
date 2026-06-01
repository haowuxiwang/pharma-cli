# t-test R script
# Input: JSON with fields: test_type (one_sample, two_sample, paired), values, values2, mu (for one-sample)
# Output: JSON to stdout

library(jsonlite)

input <- fromJSON(file("stdin"))
test_type <- ifelse(is.null(input$test_type), "two_sample", input$test_type)
values <- as.numeric(input$values)
values <- values[!is.na(values)]

if (test_type == "one_sample") {
  if (is.null(input$mu)) stop("mu (hypothesized mean) required for one-sample t-test")
  mu <- input$mu
  n <- length(values)
  mean_val <- mean(values)
  sd_val <- sd(values)
  se <- sd_val / sqrt(n)
  t_stat <- (mean_val - mu) / se
  df <- n - 1
  p_value <- 2 * pt(-abs(t_stat), df)
  ci_lower <- mean_val - qt(0.975, df) * se
  ci_upper <- mean_val + qt(0.975, df) * se

  result <- list(
    test_type = "one_sample",
    n = n,
    mean = round(mean_val, 4),
    sd = round(sd_val, 4),
    se = round(se, 4),
    hypothesized_mean = mu,
    t_statistic = round(t_stat, 4),
    df = df,
    p_value = round(p_value, 4),
    ci_95_lower = round(ci_lower, 4),
    ci_95_upper = round(ci_upper, 4),
    significant = p_value < 0.05,
    interpretation = ifelse(p_value < 0.05,
      paste("Significant difference from", mu, "(p < 0.05)"),
      paste("No significant difference from", mu, "(p >= 0.05)")
    )
  )

} else if (test_type == "two_sample") {
  values2 <- as.numeric(input$values2)
  values2 <- values2[!is.na(values2)]
  if (length(values2) < 2) stop("Need at least 2 data points in second group")

  # Check for equal variance assumption (F-test)
  var_test <- var.test(values, values2)
  equal_var <- var_test$p.value > 0.05

  t_result <- t.test(values, values2, var.equal = equal_var)

  n1 <- length(values)
  n2 <- length(values2)
  mean1 <- mean(values)
  mean2 <- mean(values2)
  sd1 <- sd(values)
  sd2 <- sd(values2)
  mean_diff <- mean1 - mean2

  result <- list(
    test_type = "two_sample",
    group1 = list(n = n1, mean = round(mean1, 4), sd = round(sd1, 4)),
    group2 = list(n = n2, mean = round(mean2, 4), sd = round(sd2, 4)),
    mean_difference = round(mean_diff, 4),
    t_statistic = round(as.numeric(t_result$statistic), 4),
    df = round(as.numeric(t_result$parameter), 4),
    p_value = round(as.numeric(t_result$p.value), 4),
    ci_95_lower = round(as.numeric(t_result$conf.int[1]), 4),
    ci_95_upper = round(as.numeric(t_result$conf.int[2]), 4),
    equal_variance = equal_var,
    f_test_p_value = round(as.numeric(var_test$p.value), 4),
    significant = t_result$p.value < 0.05,
    interpretation = ifelse(t_result$p.value < 0.05,
      "Significant difference between groups (p < 0.05)",
      "No significant difference between groups (p >= 0.05)"
    )
  )

} else if (test_type == "paired") {
  values2 <- as.numeric(input$values2)
  values2 <- values2[!is.na(values2)]
  if (length(values) != length(values2)) stop("Paired test requires equal sample sizes")

  t_result <- t.test(values, values2, paired = TRUE)
  diff_values <- values - values2
  n <- length(diff_values)
  mean_diff <- mean(diff_values)
  sd_diff <- sd(diff_values)

  result <- list(
    test_type = "paired",
    n_pairs = n,
    mean_before = round(mean(values), 4),
    mean_after = round(mean(values2), 4),
    mean_difference = round(mean_diff, 4),
    sd_difference = round(sd_diff, 4),
    t_statistic = round(as.numeric(t_result$statistic), 4),
    df = as.numeric(t_result$parameter),
    p_value = round(as.numeric(t_result$p.value), 4),
    ci_95_lower = round(as.numeric(t_result$conf.int[1]), 4),
    ci_95_upper = round(as.numeric(t_result$conf.int[2]), 4),
    significant = t_result$p.value < 0.05,
    interpretation = ifelse(t_result$p.value < 0.05,
      "Significant difference between paired samples (p < 0.05)",
      "No significant difference between paired samples (p >= 0.05)"
    )
  )

} else {
  stop(paste("Unknown test type:", test_type))
}

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
