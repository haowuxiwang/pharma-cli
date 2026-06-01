# Process capability analysis R script
# Input: JSON from stdin with fields: values, usl, lsl, target (optional)
# Output: JSON to stdout

library(jsonlite)
library(base64enc)

input <- fromJSON(file("stdin"))
values <- as.numeric(input$values)
values <- values[!is.na(values)]

usl <- input$usl
lsl <- input$lsl
target <- input$target

if (length(values) < 2) {
  stop("Need at least 2 data points")
}
if (is.null(usl) && is.null(lsl)) {
  stop("At least one specification limit (USL or LSL) is required")
}

n <- length(values)
mean_val <- mean(values)
std_within <- sd(values)  # Within-subgroup std (short-term)
std_overall <- sd(values)  # Overall std (long-term)

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

  result$cp <- round(cp, 4)
  result$cpk <- round(cpk, 4)
  result$cpu <- round(cpu, 4)
  result$cpl <- round(cpl, 4)
  result$pp <- round(pp, 4)
  result$ppk <- round(ppk, 4)
  result$ppu <- round(ppu, 4)
  result$ppl <- round(ppl, 4)
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

# Histogram data
hist_obj <- hist(values, plot = FALSE, breaks = "Sturges")
result$histogram <- list(
  x = round((hist_obj$breaks[-1] + head(hist_obj$breaks, -1)) / 2, 4),
  counts = as.integer(hist_obj$counts)
)

# Generate plot if requested
if (!is.null(input$generate_plot) && input$generate_plot == TRUE) {
  tryCatch({
    # Create temp file for PNG
    tmp_file <- tempfile(fileext = ".png")
    on.exit(unlink(tmp_file))

    # Generate plot
    png(tmp_file, width = 800, height = 600, res = 100)
    par(mar = c(5, 4, 4, 2) + 0.1)

    # Histogram with specification limits
    hist(values, breaks = "Sturges", col = "lightblue", border = "white",
         main = paste("Process Capability Analysis\nCpk =", round(result$cpk, 2),
                      "- Rating:", result$rating),
         xlab = "Value", ylab = "Frequency", probability = TRUE)

    # Add normal curve
    x_range <- seq(min(values) - 3 * sd(values), max(values) + 3 * sd(values), length.out = 100)
    normal_curve_y <- dnorm(x_range, mean(values), sd(values))
    lines(x_range, normal_curve_y, col = "blue", lwd = 2)

    # Add specification limits
    if (!is.null(usl)) {
      abline(v = usl, col = "red", lwd = 2, lty = 2)
      text(usl, par("usr")[4] * 0.9, paste("USL =", usl), pos = 4, col = "red")
    }
    if (!is.null(lsl)) {
      abline(v = lsl, col = "red", lwd = 2, lty = 2)
      text(lsl, par("usr")[4] * 0.9, paste("LSL =", lsl), pos = 2, col = "red")
    }

    # Add target line
    abline(v = target, col = "green", lwd = 2, lty = 3)
    text(target, par("usr")[4] * 0.8, paste("Target =", target), pos = 4, col = "green")

    # Add mean line
    abline(v = mean(values), col = "purple", lwd = 2)
    text(mean(values), par("usr")[4] * 0.7, paste("Mean =", round(mean(values), 2)), pos = 4, col = "purple")

    # Add legend
    legend("topright",
           legend = c("Normal Curve", "USL/LSL", "Target", "Mean"),
           col = c("blue", "red", "green", "purple"),
           lwd = c(2, 2, 2, 2),
           lty = c(1, 2, 3, 1))

    dev.off()

    # Read and encode to base64
    raw_bytes <- readBin(tmp_file, "raw", file.info(tmp_file)$size)
    result$plot <- base64enc::base64encode(raw_bytes)
  }, error = function(e) {
    result$plot_error <- as.character(e)
  })
}

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
