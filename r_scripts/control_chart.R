# Control chart R script
# Input: JSON with fields: values, chart_type (xbar, r, imr, p, np, c, u), subgroups (optional)
# Output: JSON to stdout

library(jsonlite)
library(base64enc)

# Helper function to generate base64-encoded PNG plot
generate_plot_base64 <- function(plot_func, width = 800, height = 600) {
  # Create temp file for PNG
  tmp_file <- tempfile(fileext = ".png")
  on.exit(unlink(tmp_file))

  # Generate plot
  png(tmp_file, width = width, height = height, res = 100)
  plot_func()
  dev.off()

  # Read and encode to base64
  raw_bytes <- readBin(tmp_file, "raw", file.info(tmp_file)$size)
  return(base64enc::base64encode(raw_bytes))
}

input <- fromJSON(file("stdin"))
values <- as.numeric(input$values)
chart_type <- ifelse(is.null(input$chart_type), "imr", input$chart_type)
subgroup_size <- ifelse(is.null(input$subgroup_size), 5, input$subgroup_size)

values <- values[!is.na(values)]
n <- length(values)

if (n < 2) stop("Need at least 2 data points")

create_chart <- function(x, center, ucl, lcl, title) {
  list(
    points = round(x, 4),
    center = round(center, 4),
    ucl = round(ucl, 4),
    lcl = round(lcl, 4),
    in_control = (x >= lcl & x <= ucl),
    out_of_control_points = which(x < lcl | x > ucl),
    title = title
  )
}

detect_rules <- function(x, center, ucl, lcl, sigma) {
  n <- length(x)
  violations <- list()

  # Rule 1: Point beyond 3-sigma
  rule1 <- which(x > ucl | x < lcl)
  if (length(rule1) > 0) {
    violations$rule1 <- list(description = "Point beyond 3-sigma", indices = rule1)
  }

  # Rule 2: 2 of 3 consecutive points beyond 2-sigma
  rule2 <- c()
  if (n >= 3) {
    upper_2s <- center + 2 * sigma
    lower_2s <- center - 2 * sigma
    for (i in 2:(n - 1)) {
      window <- x[(i - 1):(i + 1)]
      if (sum(window > upper_2s | window < lower_2s) >= 2) {
        rule2 <- c(rule2, i)
      }
    }
  }
  if (length(rule2) > 0) {
    violations$rule2 <- list(description = "2 of 3 points beyond 2-sigma", indices = rule2)
  }

  # Rule 3: 4 of 5 consecutive points beyond 1-sigma
  rule3 <- c()
  if (n >= 5) {
    upper_1s <- center + sigma
    lower_1s <- center - sigma
    for (i in 3:(n - 2)) {
      window <- x[(i - 2):(i + 2)]
      if (sum(window > upper_1s | window < lower_1s) >= 4) {
        rule3 <- c(rule3, i)
      }
    }
  }
  if (length(rule3) > 0) {
    violations$rule3 <- list(description = "4 of 5 points beyond 1-sigma", indices = rule3)
  }

  # Rule 4: 8 consecutive points on same side of center
  rule4 <- c()
  if (n >= 8) {
    above <- x > center
    for (i in 8:n) {
      window <- above[(i - 7):i]
      if (all(window) || all(!window)) {
        rule4 <- c(rule4, i)
      }
    }
  }
  if (length(rule4) > 0) {
    violations$rule4 <- list(description = "8 points on same side of center", indices = rule4)
  }

  # Rule 5: 6 consecutive points steadily increasing or decreasing
  rule5 <- c()
  if (n >= 6) {
    for (i in 6:n) {
      window <- x[(i - 5):i]
      if (all(diff(window) > 0) || all(diff(window) < 0)) {
        rule5 <- c(rule5, i)
      }
    }
  }
  if (length(rule5) > 0) {
    violations$rule5 <- list(description = "6 points steadily increasing or decreasing", indices = rule5)
  }

  violations
}

if (chart_type == "xbar") {
  # X-bar chart with subgroups
  n_groups <- floor(n / subgroup_size)
  if (n_groups < 2) stop("Not enough data for subgroups")
  groups <- matrix(values[1:(n_groups * subgroup_size)], nrow = subgroup_size)
  group_means <- colMeans(groups)
  group_ranges <- apply(groups, 2, function(x) max(x) - min(x))
  center <- mean(group_means)
  r_bar <- mean(group_ranges)
  d2 <- c(1.128, 1.693, 2.059, 2.326, 2.534, 2.704, 2.847, 2.970)
  d2_val <- d2[min(subgroup_size, length(d2))]
  sigma <- r_bar / d2_val
  ucl <- center + 3 * sigma / sqrt(subgroup_size)
  lcl <- center - 3 * sigma / sqrt(subgroup_size)
  chart <- create_chart(group_means, center, ucl, lcl, "X-bar Chart")
  chart$violations <- detect_rules(group_means, center, ucl, lcl, sigma / sqrt(subgroup_size))
  result <- list(chart_type = "xbar", subgroup_size = subgroup_size, n_groups = n_groups, chart = chart)

} else if (chart_type == "r") {
  # R chart
  n_groups <- floor(n / subgroup_size)
  if (n_groups < 2) stop("Not enough data for subgroups")
  groups <- matrix(values[1:(n_groups * subgroup_size)], nrow = subgroup_size)
  group_ranges <- apply(groups, 2, function(x) max(x) - min(x))
  center <- mean(group_ranges)
  D3 <- c(0, 0, 0, 0, 0, 0.076, 0.136, 0.184, 0.223)
  D4 <- c(3.267, 2.574, 2.282, 2.114, 2.004, 1.924, 1.864, 1.816, 1.777)
  idx <- min(subgroup_size, length(D4))
  ucl <- center * D4[idx]
  lcl <- center * D3[idx]
  chart <- create_chart(group_ranges, center, ucl, lcl, "R Chart")
  chart$violations <- detect_rules(group_ranges, center, ucl, lcl, center * 0.5)
  result <- list(chart_type = "r", subgroup_size = subgroup_size, n_groups = n_groups, chart = chart)

} else if (chart_type == "imr") {
  # Individual-Moving Range chart
  moving_ranges <- abs(diff(values))
  mr_bar <- mean(moving_ranges)
  center <- mean(values)
  sigma <- mr_bar / 1.128
  ucl <- center + 3 * sigma
  lcl <- center - 3 * sigma
  chart <- create_chart(values, center, ucl, lcl, "I Chart")
  chart$violations <- detect_rules(values, center, ucl, lcl, sigma)

  mr_ucl <- 3.267 * mr_bar
  mr_chart <- create_chart(c(NA, moving_ranges), mr_bar, mr_ucl, 0, "MR Chart")

  result <- list(chart_type = "imr", chart = chart, mr_chart = mr_chart)

} else if (chart_type == "p") {
  # p chart (proportion defective)
  n_sample <- ifelse(is.null(input$sample_size), subgroup_size, input$sample_size)
  p_bar <- mean(values / n_sample)
  sigma <- sqrt(p_bar * (1 - p_bar) / n_sample)
  center <- p_bar
  ucl <- p_bar + 3 * sigma
  lcl <- max(0, p_bar - 3 * sigma)
  proportions <- values / n_sample
  chart <- create_chart(proportions, center, ucl, lcl, "p Chart")
  chart$violations <- detect_rules(proportions, center, ucl, lcl, sigma)
  result <- list(chart_type = "p", sample_size = n_sample, chart = chart)

} else if (chart_type == "np") {
  # np chart (number defective)
  n_sample <- ifelse(is.null(input$sample_size), subgroup_size, input$sample_size)
  p_bar <- mean(values / n_sample)
  center <- n_sample * p_bar
  ucl <- center + 3 * sqrt(n_sample * p_bar * (1 - p_bar))
  lcl <- max(0, center - 3 * sqrt(n_sample * p_bar * (1 - p_bar)))
  chart <- create_chart(values, center, ucl, lcl, "np Chart")
  chart$violations <- detect_rules(values, center, ucl, lcl, sqrt(n_sample * p_bar * (1 - p_bar)))
  result <- list(chart_type = "np", sample_size = n_sample, chart = chart)

} else if (chart_type == "c") {
  # c chart (count of defects)
  center <- mean(values)
  sigma <- sqrt(center)
  ucl <- center + 3 * sigma
  lcl <- max(0, center - 3 * sigma)
  chart <- create_chart(values, center, ucl, lcl, "c Chart")
  chart$violations <- detect_rules(values, center, ucl, lcl, sigma)
  result <- list(chart_type = "c", chart = chart)

} else if (chart_type == "u") {
  # u chart (defects per unit)
  n_sample <- ifelse(is.null(input$sample_size), subgroup_size, input$sample_size)
  u_values <- values / n_sample
  center <- mean(u_values)
  sigma <- sqrt(center / n_sample)
  ucl <- center + 3 * sigma
  lcl <- max(0, center - 3 * sigma)
  chart <- create_chart(u_values, center, ucl, lcl, "u Chart")
  chart$violations <- detect_rules(u_values, center, ucl, lcl, sigma)
  result <- list(chart_type = "u", sample_size = n_sample, chart = chart)

} else if (chart_type == "ewma") {
  # EWMA (Exponentially Weighted Moving Average) chart
  lambda <- ifelse(is.null(input$lambda), 0.2, input$lambda)
  target <- ifelse(is.null(input$target), mean(values), input$target)

  # Calculate EWMA values
  ewma_values <- numeric(n)
  ewma_values[1] <- lambda * values[1] + (1 - lambda) * target
  for (i in 2:n) {
    ewma_values[i] <- lambda * values[i] + (1 - lambda) * ewma_values[i-1]
  }

  # Calculate control limits
  sigma <- sd(values)
  center <- target
  ucl <- target + 3 * sigma * sqrt(lambda / (2 - lambda) * (1 - (1 - lambda)^(2 * (1:n))))
  lcl <- target - 3 * sigma * sqrt(lambda / (2 - lambda) * (1 - (1 - lambda)^(2 * (1:n))))

  chart <- create_chart(ewma_values, center, ucl[1], lcl[1], "EWMA Chart")
  chart$ucl <- round(ucl, 4)
  chart$lcl <- round(lcl, 4)
  chart$lambda <- lambda
  chart$target <- target
  chart$violations <- detect_rules(ewma_values, center, ucl[1], lcl[1], sigma)
  result <- list(chart_type = "ewma", chart = chart)

} else if (chart_type == "cusum") {
  # CUSUM (Cumulative Sum) chart
  target <- ifelse(is.null(input$target), mean(values), input$target)
  k <- ifelse(is.null(input$k), 0.5, input$k)  # Reference value (typically 0.5 * sigma)
  h <- ifelse(is.null(input$h), 5, input$h)  # Decision interval (typically 5 * sigma)

  sigma <- sd(values)
  k_val <- k * sigma
  h_val <- h * sigma

  # Calculate CUSUM values
  cusum_pos <- numeric(n)
  cusum_neg <- numeric(n)
  cusum_pos[1] <- max(0, values[1] - target - k_val)
  cusum_neg[1] <- max(0, target - values[1] - k_val)

  for (i in 2:n) {
    cusum_pos[i] <- max(0, cusum_pos[i-1] + values[i] - target - k_val)
    cusum_neg[i] <- max(0, cusum_neg[i-1] + target - values[i] - k_val)
  }

  # Find alarm points
  alarm_points <- which(cusum_pos > h_val | cusum_neg > h_val)

  chart <- list(
    points = round(values, 4),
    center = round(target, 4),
    ucl = round(h_val, 4),
    lcl = round(-h_val, 4),
    cusum_pos = round(cusum_pos, 4),
    cusum_neg = round(cusum_neg, 4),
    k = k,
    h = h,
    alarm_points = alarm_points,
    n_alarms = length(alarm_points),
    title = "CUSUM Chart"
  )

  result <- list(
    chart_type = "cusum",
    chart = chart,
    summary = list(
      stable = length(alarm_points) == 0,
      message = ifelse(length(alarm_points) == 0,
        "No alarms detected - process appears stable",
        paste(length(alarm_points), "alarm(s) detected - process may be out of control")
      )
    )
  )

} else {
  stop(paste("Unknown chart type:", chart_type))
}

# Summary
result$summary <- list(
  stable = length(chart$out_of_control_points) == 0,
  message = ifelse(length(chart$out_of_control_points) == 0,
    "Process is in statistical control",
    paste("Process has", length(chart$out_of_control_points), "out-of-control point(s)")
  )
)

# Generate plot if requested
if (!is.null(input$generate_plot) && input$generate_plot == TRUE) {
  tryCatch({
    library(base64enc)

    plot_func <- function() {
      par(mfrow = c(1, 1), mar = c(5, 4, 4, 2) + 0.1)

      if (chart_type == "imr") {
        # I-MR chart: plot I chart
        plot(chart$points, type = "b", pch = 19, col = "blue",
             main = "Individual (I) Chart",
             xlab = "Observation", ylab = "Value",
             ylim = c(min(chart$lcl, min(chart$points)) * 0.95,
                      max(chart$ucl, max(chart$points)) * 1.05))
        abline(h = chart$center, col = "green", lwd = 2)
        abline(h = chart$ucl, col = "red", lwd = 2, lty = 2)
        abline(h = chart$lcl, col = "red", lwd = 2, lty = 2)

        # Highlight out-of-control points
        if (length(chart$out_of_control_points) > 0) {
          points(chart$out_of_control_points,
                 chart$points[chart$out_of_control_points],
                 col = "red", pch = 19, cex = 1.5)
        }

      } else {
        # Generic control chart
        plot(chart$points, type = "b", pch = 19, col = "blue",
             main = chart$title,
             xlab = "Subgroup", ylab = "Value",
             ylim = c(min(chart$lcl, min(chart$points, na.rm = TRUE)) * 0.95,
                      max(chart$ucl, max(chart$points, na.rm = TRUE)) * 1.05))
        abline(h = chart$center, col = "green", lwd = 2)
        abline(h = chart$ucl, col = "red", lwd = 2, lty = 2)
        abline(h = chart$lcl, col = "red", lwd = 2, lty = 2)

        # Highlight out-of-control points
        if (length(chart$out_of_control_points) > 0) {
          points(chart$out_of_control_points,
                 chart$points[chart$out_of_control_points],
                 col = "red", pch = 19, cex = 1.5)
        }
      }

      # Add legend
      legend("topright",
             legend = c("Data", "Center Line", "UCL/LCL", "Out of Control"),
             col = c("blue", "green", "red", "red"),
             pch = c(19, NA, NA, 19),
             lty = c(NA, 1, 2, NA),
             lwd = c(NA, 2, 2, NA))
    }

    result$plot <- generate_plot_base64(plot_func)
  }, error = function(e) {
    # If plot generation fails, just skip it
    result$plot_error <- as.character(e)
  })
}

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
