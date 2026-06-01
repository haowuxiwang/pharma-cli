# Correlation analysis R script
# Input: JSON with fields: x, y (or matrix for multiple), method (pearson, spearman, kendall)
# Output: JSON to stdout

library(jsonlite)

input <- fromJSON(file("stdin"))
method <- ifelse(is.null(input$method), "pearson", input$method)

if (!is.null(input$matrix)) {
  # Multiple variables correlation matrix
  data_matrix <- as.data.frame(input$matrix)
  n_vars <- ncol(data_matrix)

  cor_matrix <- cor(data_matrix, method = method, use = "complete.obs")

  # Get p-values
  cor_p <- matrix(NA, n_vars, n_vars)
  for (i in 1:n_vars) {
    for (j in 1:n_vars) {
      if (i != j) {
        test <- cor.test(data_matrix[[i]], data_matrix[[j]], method = method)
        cor_p[i, j] <- test$p.value
      } else {
        cor_p[i, j] <- 0
      }
    }
  }

  colnames(cor_matrix) <- colnames(data_matrix)
  rownames(cor_matrix) <- colnames(data_matrix)
  colnames(cor_p) <- colnames(data_matrix)
  rownames(cor_p) <- colnames(data_matrix)

  result <- list(
    method = method,
    n_variables = n_vars,
    correlation_matrix = round(cor_matrix, 4),
    p_value_matrix = round(cor_p, 4),
    interpretation = paste(method, "correlation matrix computed")
  )

} else {
  # Simple two-variable correlation
  x <- as.numeric(input$x)
  y <- as.numeric(input$y)

  valid <- !is.na(x) & !is.na(y)
  x <- x[valid]
  y <- y[valid]
  n <- length(x)

  if (n < 3) stop("Need at least 3 data points")

  cor_result <- cor.test(x, y, method = method)

  r <- cor_result$estimate
  p_value <- cor_result$p.value
  ci <- cor_result$conf.int

  # Interpretation
  r_abs <- abs(r)
  if (r_abs >= 0.9) {
    strength <- "very strong"
  } else if (r_abs >= 0.7) {
    strength <- "strong"
  } else if (r_abs >= 0.5) {
    strength <- "moderate"
  } else if (r_abs >= 0.3) {
    strength <- "weak"
  } else {
    strength <- "very weak"
  }

  direction <- ifelse(r > 0, "positive", "negative")

  result <- list(
    method = method,
    n = n,
    correlation = round(as.numeric(r), 4),
    p_value = round(as.numeric(p_value), 4),
    ci_95_lower = round(as.numeric(ci[1]), 4),
    ci_95_upper = round(as.numeric(ci[2]), 4),
    r_squared = round(as.numeric(r^2), 4),
    significant = p_value < 0.05,
    interpretation = paste0(
      strength, " ", direction, " correlation (r = ", round(r, 4), ", ",
      ifelse(p_value < 0.05, "p < 0.05", paste("p =", round(p_value, 4))), ")"
    )
  )
}

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
