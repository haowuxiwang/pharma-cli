# Regression analysis R script
# Input: JSON with fields: x (independent variable), y (dependent variable), reg_type (linear, quadratic, polynomial)
# Output: JSON to stdout

library(jsonlite)

input <- fromJSON(file("stdin"))
x <- as.numeric(input$x)
y <- as.numeric(input$y)
reg_type <- ifelse(is.null(input$reg_type), "linear", input$reg_type)
degree <- ifelse(is.null(input$degree), 2, input$degree)

# Remove NAs
valid <- !is.na(x) & !is.na(y)
x <- x[valid]
y <- y[valid]
n <- length(x)

if (n < 2) stop("Need at least 2 data points")

# Fit model
if (reg_type == "linear") {
  model <- lm(y ~ x)
  formula_str <- "y = a + bx"

} else if (reg_type == "quadratic") {
  model <- lm(y ~ poly(x, 2, raw = TRUE))
  formula_str <- "y = a + bx + cx^2"

} else if (reg_type == "polynomial") {
  model <- lm(y ~ poly(x, degree, raw = TRUE))
  formula_str <- paste0("y = a + bx + ... + x^", degree)

} else {
  stop(paste("Unknown regression type:", reg_type))
}

# Model summary
model_summary <- summary(model)

# Coefficients
coefficients <- model_summary$coefficients
coef_list <- list()
for (i in 1:nrow(coefficients)) {
  coef_list[[rownames(coefficients)[i]]] <- list(
    estimate = round(coefficients[i, 1], 6),
    std_error = round(coefficients[i, 2], 4),
    t_value = round(coefficients[i, 3], 4),
    p_value = round(coefficients[i, 4], 4)
  )
}

# Goodness of fit
r_squared <- model_summary$r.squared
adj_r_squared <- model_summary$adj.r.squared
f_stat <- model_summary$fstatistic[1]
f_df1 <- model_summary$fstatistic[2]
f_df2 <- model_summary$fstatistic[3]
f_p <- pf(f_stat, f_df1, f_df2, lower.tail = FALSE)

# Residuals
residuals <- model$residuals
fitted_values <- model$fitted.values

# Residual diagnostics
shapiro_res <- tryCatch(
  shapiro.test(residuals),
  error = function(e) list(p.value = NA)
)

# Confidence and prediction intervals
x_new <- data.frame(x = seq(min(x), max(x), length.out = 50))
if (reg_type != "linear") {
  colnames(x_new) <- "x"
}
ci <- predict(model, x_new, interval = "confidence", level = 0.95)
pi <- predict(model, x_new, interval = "prediction", level = 0.95)

result <- list(
  regression_type = reg_type,
  formula = formula_str,
  n = n,
  coefficients = coef_list,
  r_squared = round(r_squared, 4),
  adj_r_squared = round(adj_r_squared, 4),
  f_statistic = round(f_stat, 4),
  f_df1 = f_df1,
  f_df2 = f_df2,
  f_p_value = round(f_p, 4),
  residual_std_error = round(model_summary$sigma, 4),
  residuals = list(
    mean = round(mean(residuals), 6),
    std = round(sd(residuals), 4),
    min = round(min(residuals), 4),
    max = round(max(residuals), 4),
    shapiro_p = round(shapiro_res$p.value, 4),
    normal = shapiro_res$p.value > 0.05
  ),
  fitted_values = round(fitted_values, 4),
  prediction = list(
    x_values = round(x_new$x, 4),
    fitted = round(ci[, "fit"], 4),
    ci_lower = round(ci[, "lwr"], 4),
    ci_upper = round(ci[, "upr"], 4),
    pi_lower = round(pi[, "lwr"], 4),
    pi_upper = round(pi[, "upr"], 4)
  ),
  interpretation = paste0(
    "R-squared = ", round(r_squared * 100, 1), "% of variance explained. ",
    ifelse(f_p < 0.05, "Model is significant (p < 0.05).", "Model is NOT significant (p >= 0.05)."),
    ifelse(shapiro_res$p.value > 0.05,
      " Residuals are normally distributed.",
      " WARNING: Residuals are NOT normally distributed.")
  )
)

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
