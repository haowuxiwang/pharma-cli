# Outlier detection R script
# Input: JSON with fields: values, method (grubbs, dixon, iqr, zscore), alpha (default 0.05)
# Output: JSON to stdout

library(jsonlite)

input <- fromJSON(file("stdin"))
values <- as.numeric(input$values)
values <- values[!is.na(values)]
method <- ifelse(is.null(input$method), "grubbs", input$method)
alpha <- ifelse(is.null(input$alpha), 0.05, input$alpha)

n <- length(values)
if (n < 3) stop("Need at least 3 data points for outlier detection")

detect_outliers <- function(values, method) {
  n <- length(values)
  outliers <- c()
  test_stat <- NA
  p_value <- NA
  critical <- NA

  if (method == "grubbs") {
    # Grubbs test (iterative)
    x <- values
    outliers <- c()
    repeat {
      n <- length(x)
      if (n < 3) break
      mean_x <- mean(x)
      sd_x <- sd(x)
      abs_diff <- abs(x - mean_x)
      max_idx <- which.max(abs_diff)
      G <- abs_diff[max_idx] / sd_x

      # Critical value
      t_crit <- qt(1 - alpha / (2 * n), n - 2)
      G_crit <- ((n - 1) / sqrt(n)) * sqrt(t_crit^2 / (n - 2 + t_crit^2))

      if (G > G_crit) {
        outliers <- c(outliers, x[max_idx])
        x <- x[-max_idx]
      } else {
        break
      }
    }
    test_stat <- ifelse(length(outliers) > 0, G, NA)
    critical <- ifelse(length(outliers) > 0, G_crit, NA)

  } else if (method == "dixon") {
    # Dixon Q test
    x_sorted <- sort(values)
    n <- length(x_sorted)
    if (n >= 3 && n <= 30) {
      # Test lower outlier
      Q_low <- (x_sorted[2] - x_sorted[1]) / (x_sorted[n] - x_sorted[1])
      # Test upper outlier
      Q_high <- (x_sorted[n] - x_sorted[n-1]) / (x_sorted[n] - x_sorted[1])

      # Critical values (approximate)
      Q_crit <- if (n == 3) 0.941 else if (n == 4) 0.765 else if (n == 5) 0.642
                else if (n == 6) 0.560 else if (n == 7) 0.507 else if (n == 8) 0.468
                else if (n == 9) 0.437 else if (n == 10) 0.412 else 0.4

      if (Q_low > Q_crit) {
        outliers <- c(outliers, x_sorted[1])
      }
      if (Q_high > Q_crit) {
        outliers <- c(outliers, x_sorted[n])
      }
      test_stat <- max(Q_low, Q_high)
      critical <- Q_crit
    }

  } else if (method == "iqr") {
    # IQR method (Tukey fences)
    Q1 <- quantile(values, 0.25, names = FALSE)
    Q3 <- quantile(values, 0.75, names = FALSE)
    IQR_val <- Q3 - Q1
    lower_fence <- Q1 - 1.5 * IQR_val
    upper_fence <- Q3 + 1.5 * IQR_val
    outliers <- values[values < lower_fence | values > upper_fence]
    test_stat <- IQR_val
    critical <- paste0("[", round(lower_fence, 4), ", ", round(upper_fence, 4), "]")

  } else if (method == "zscore") {
    # Z-score method
    mean_x <- mean(values)
    sd_x <- sd(values)
    z_scores <- (values - mean_x) / sd_x
    z_threshold <- 3
    outliers <- values[abs(z_scores) > z_threshold]
    test_stat <- max(abs(z_scores))
    critical <- z_threshold

  } else {
    stop(paste("Unknown method:", method))
  }

  list(
    outliers = round(outliers, 4),
    n_outliers = length(outliers),
    test_statistic = round(as.numeric(test_stat), 4),
    critical_value = ifelse(is.numeric(critical), round(critical, 4), critical)
  )
}

result_raw <- detect_outliers(values, method)

result <- list(
  method = method,
  alpha = alpha,
  n = n,
  outliers = result_raw$outliers,
  n_outliers = result_raw$n_outliers,
  test_statistic = result_raw$test_statistic,
  critical_value = result_raw$critical_value,
  clean_data = round(values[!values %in% result_raw$outliers], 4),
  interpretation = ifelse(result_raw$n_outliers > 0,
    paste(result_raw$n_outliers, "outlier(s) detected using", method, "test"),
    "No outliers detected"
  )
)

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
