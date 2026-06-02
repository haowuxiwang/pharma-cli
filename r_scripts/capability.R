# Process capability analysis R script
# Input: JSON from stdin with fields: values, usl, lsl, target (optional), capability_type (optional)
# Output: JSON to stdout

library(jsonlite)
library(base64enc)

input <- fromJSON(file("stdin"))
values <- as.numeric(input$values)
values <- values[!is.na(values) & is.finite(values)]

usl <- input$usl
lsl <- input$lsl
target <- input$target
capability_type <- ifelse(!is.null(input$capability_type), input$capability_type, "normal")

if (length(values) < 2) {
  stop("Need at least 2 data points")
}
if (is.null(usl) && is.null(lsl)) {
  stop("At least one specification limit (USL or LSL) is required")
}

n <- length(values)
mean_val <- mean(values)
std_overall <- sd(values)  # Overall std (long-term)

# Calculate within-subgroup std using moving range method (for I-MR data)
if (n >= 2) {
  moving_ranges <- abs(diff(values))
  mr_bar <- mean(moving_ranges)
  d2 <- 1.128  # d2 for subgroup size 2 (moving range)
  std_within <- mr_bar / d2
} else {
  std_within <- std_overall
}

# Use midpoint of specs as target if not specified
if (is.null(target)) {
  if (!is.null(usl) && !is.null(lsl)) {
    target <- (usl + lsl) / 2
  } else {
    target <- mean_val
  }
}

result <- list(
  mean = round(mean_val, 4),
  std_within = round(std_within, 4),
  std_overall = round(std_overall, 4),
  usl = usl,
  lsl = lsl,
  target = target,
  n = n
)

# Calculate capability indices
if (!is.null(usl) && !is.null(lsl)) {
  # Two-sided spec
  cp <- (usl - lsl) / (6 * std_within)
  pp <- (usl - lsl) / (6 * std_overall)
  cpu <- (usl - mean_val) / (3 * std_within)
  cpl <- (mean_val - lsl) / (3 * std_within)
  cpk <- min(cpu, cpl)
  ppu <- (usl - mean_val) / (3 * std_overall)
  ppl <- (mean_val - lsl) / (3 * std_overall)
  ppk <- min(ppu, ppl)

  # Cpm (Taguchi capability index)
  tau_sq <- sum((values - target)^2) / n
  cpm <- (usl - lsl) / (6 * sqrt(tau_sq))

  result$cp <- round(cp, 4)
  result$cpk <- round(cpk, 4)
  result$cpu <- round(cpu, 4)
  result$cpl <- round(cpl, 4)
  result$pp <- round(pp, 4)
  result$ppk <- round(ppk, 4)
  result$ppu <- round(ppu, 4)
  result$ppl <- round(ppl, 4)
  result$cpm <- round(cpm, 4)
} else if (!is.null(usl)) {
  # One-sided (upper)
  cpu <- (usl - mean_val) / (3 * std_within)
  ppu <- (usl - mean_val) / (3 * std_overall)
  result$cp <- round(cpu, 4)
  result$cpk <- round(cpu, 4)
  result$cpu <- round(cpu, 4)
  result$cpl <- NA
  result$pp <- round(ppu, 4)
  result$ppk <- round(ppu, 4)
  result$ppu <- round(ppu, 4)
  result$ppl <- NA
  result$cpm <- NA
} else {
  # One-sided (lower)
  cpl <- (mean_val - lsl) / (3 * std_within)
  ppl <- (mean_val - lsl) / (3 * std_overall)
  result$cp <- round(cpl, 4)
  result$cpk <- round(cpl, 4)
  result$cpu <- NA
  result$cpl <- round(cpl, 4)
  result$pp <- round(ppl, 4)
  result$ppk <- round(ppl, 4)
  result$ppu <- NA
  result$ppl <- round(ppl, 4)
  result$cpm <- NA
}

# Confidence intervals for Cp and Cpk (95%)
alpha <- 0.05
if (n > 2) {
  # Cp CI
  cp_val <- ifelse(is.null(result$cp), NA, result$cp)
  if (!is.na(cp_val)) {
    chi_lower <- qchisq(alpha/2, n - 1)
    chi_upper <- qchisq(1 - alpha/2, n - 1)
    cp_lower <- cp_val * sqrt((n - 1) / chi_upper)
    cp_upper <- cp_val * sqrt((n - 1) / chi_lower)
    result$cp_ci_lower <- round(cp_lower, 4)
    result$cp_ci_upper <- round(cp_upper, 4)
  }

  # Cpk CI (approximate)
  cpk_val <- ifelse(is.null(result$cpk), NA, result$cpk)
  if (!is.na(cpk_val)) {
    se_cpk <- sqrt(1/n + cpk_val^2 / (2 * (n - 1)))
    cpk_lower <- cpk_val - qnorm(1 - alpha/2) * se_cpk
    cpk_upper <- cpk_val + qnorm(1 - alpha/2) * se_cpk
    result$cpk_ci_lower <- round(cpk_lower, 4)
    result$cpk_ci_upper <- round(cpk_upper, 4)
  }
}

# Non-normal capability (Box-Cox transformation)
if (capability_type == "boxcox" && n >= 5) {
  # Find optimal lambda
  if (any(values <= 0)) {
    offset <- abs(min(values)) + 1
    shifted <- values + offset
  } else {
    offset <- 0
    shifted <- values
  }

  lambdas <- seq(-2, 2, by = 0.1)
  log_likelihood <- sapply(lambdas, function(lam) {
    if (abs(lam) < 0.001) {
      transformed <- log(shifted)
    } else {
      transformed <- (shifted^lam - 1) / lam
    }
    n_t <- length(transformed)
    -n_t/2 * log(var(transformed)) + (lam - 1) * sum(log(shifted))
  })

  optimal_lambda <- lambdas[which.max(log_likelihood)]

  if (abs(optimal_lambda) < 0.001) {
    transformed <- log(shifted)
  } else {
    transformed <- (shifted^optimal_lambda - 1) / optimal_lambda
  }

  # Calculate capability on transformed data
  mean_t <- mean(transformed)
  sd_t <- sd(transformed)

  # Transform spec limits
  if (!is.null(usl)) {
    if (offset > 0) usl_t <- (usl + offset)^optimal_lambda else usl_t <- usl^optimal_lambda
  }
  if (!is.null(lsl)) {
    if (offset > 0) lsl_t <- (lsl + offset)^optimal_lambda else lsl_t <- lsl^optimal_lambda
  }

  if (!is.null(usl) && !is.null(lsl)) {
    cp_bc <- (usl_t - lsl_t) / (6 * sd_t)
    cpu_bc <- (usl_t - mean_t) / (3 * sd_t)
    cpl_bc <- (mean_t - lsl_t) / (3 * sd_t)
    cpk_bc <- min(cpu_bc, cpl_bc)

    result$boxcox <- list(
      lambda = round(optimal_lambda, 2),
      offset = offset,
      cp = round(cp_bc, 4),
      cpk = round(cpk_bc, 4),
      cpu = round(cpu_bc, 4),
      cpl = round(cpl_bc, 4),
      mean_transformed = round(mean_t, 4),
      sd_transformed = round(sd_t, 4)
    )
  }
}

# Capability rating
cpk_val <- ifelse(is.null(result$cpk), 0, result$cpk)
if (cpk_val >= 1.67) {
  result$rating <- "Excellent"
  result$rating_desc <- "Process is highly capable"
} else if (cpk_val >= 1.33) {
  result$rating <- "Good"
  result$rating_desc <- "Process is capable (pharma minimum)"
} else if (cpk_val >= 1.0) {
  result$rating <- "Marginal"
  result$rating_desc <- "Process is marginally capable, improvement recommended"
} else {
  result$rating <- "Poor"
  result$rating_desc <- "Process is NOT capable, corrective action required"
}

# Performance metrics
if (!is.null(usl) && !is.null(lsl)) {
  # PPM (Parts Per Million) - expected defect rate
  z_upper <- (usl - mean_val) / std_overall
  z_lower <- (mean_val - lsl) / std_overall
  ppm_upper <- pnorm(-z_upper) * 1e6
  ppm_lower <- pnorm(-z_lower) * 1e6
  ppm_total <- ppm_upper + ppm_lower

  result$performance <- list(
    z_upper = round(z_upper, 4),
    z_lower = round(z_lower, 4),
    ppm_upper = round(ppm_upper, 2),
    ppm_lower = round(ppm_lower, 2),
    ppm_total = round(ppm_total, 2),
    yield_pct = round(100 - ppm_total / 10000, 4)
  )
}

# Histogram data
hist_obj <- hist(values, plot = FALSE, breaks = "Sturges")
result$histogram <- list(
  x = round((hist_obj$breaks[-1] + head(hist_obj$breaks, -1)) / 2, 4),
  counts = as.integer(hist_obj$counts)
)

# Generate plot if requested
if (!is.null(input$generate_plot) && input$generate_plot == TRUE) {
  tryCatch({
    tmp_file <- tempfile(fileext = ".png")
    on.exit(unlink(tmp_file))

    png(tmp_file, width = 800, height = 600, res = 100)
    par(mar = c(5, 4, 4, 2) + 0.1)

    hist(values, breaks = "Sturges", col = "lightblue", border = "white",
         main = paste("Process Capability Analysis\nCpk =", round(result$cpk, 2),
                      "- Rating:", result$rating),
         xlab = "Value", ylab = "Frequency", probability = TRUE)

    x_range <- seq(min(values) - 3 * sd(values), max(values) + 3 * sd(values), length.out = 100)
    normal_curve_y <- dnorm(x_range, mean(values), sd(values))
    lines(x_range, normal_curve_y, col = "blue", lwd = 2)

    if (!is.null(usl)) {
      abline(v = usl, col = "red", lwd = 2, lty = 2)
      text(usl, par("usr")[4] * 0.9, paste("USL =", usl), pos = 4, col = "red")
    }
    if (!is.null(lsl)) {
      abline(v = lsl, col = "red", lwd = 2, lty = 2)
      text(lsl, par("usr")[4] * 0.9, paste("LSL =", lsl), pos = 2, col = "red")
    }

    abline(v = target, col = "green", lwd = 2, lty = 3)
    text(target, par("usr")[4] * 0.8, paste("Target =", target), pos = 4, col = "green")

    abline(v = mean(values), col = "purple", lwd = 2)
    text(mean(values), par("usr")[4] * 0.7, paste("Mean =", round(mean(values), 2)), pos = 4, col = "purple")

    legend("topright",
           legend = c("Normal Curve", "USL/LSL", "Target", "Mean"),
           col = c("blue", "red", "green", "purple"),
           lwd = c(2, 2, 2, 2),
           lty = c(1, 2, 3, 1))

    dev.off()

    raw_bytes <- readBin(tmp_file, "raw", file.info(tmp_file)$size)
    result$plot <- base64enc::base64encode(raw_bytes)
  }, error = function(e) {
    result$plot_error <- as.character(e)
  })
}

# Interpretation
interp_parts <- c()
if (!is.null(result$cp)) {
  interp_parts <- c(interp_parts, sprintf("Cp = %.2f", result$cp))
}
if (!is.null(result$cpk)) {
  interp_parts <- c(interp_parts, sprintf("Cpk = %.2f", result$cpk))
}
if (!is.null(result$cpm)) {
  interp_parts <- c(interp_parts, sprintf("Cpm = %.2f", result$cpm))
}
interp_parts <- c(interp_parts, result$rating_desc)

if (!is.null(result$performance)) {
  interp_parts <- c(interp_parts, sprintf("Expected yield = %.2f%%", result$performance$yield_pct))
}

result$interpretation <- paste(interp_parts, collapse = ". ")

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
