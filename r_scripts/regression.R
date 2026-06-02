# Regression analysis R script
# Input: JSON with fields: x, y, reg_type, degree, etc.
# Output: JSON to stdout

library(jsonlite)

input <- fromJSON(file("stdin"))
reg_type <- "linear"
if (!is.null(input$reg_type)) reg_type <- input$reg_type

result <- tryCatch({
  if (reg_type %in% c("linear", "quadratic", "polynomial")) {
    # ============================================================
    # Linear/Polynomial Regression
    # ============================================================
    x <- as.numeric(input$x)
    y <- as.numeric(input$y)
    degree <- 2
    if (!is.null(input$degree)) degree <- as.integer(input$degree)

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
    } else {
      model <- lm(y ~ poly(x, degree, raw = TRUE))
      formula_str <- paste0("y = a + bx + ... + x^", degree)
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
    shapiro_res <- tryCatch(shapiro.test(residuals), error = function(e) list(p.value = NA))

    # Confidence and prediction intervals
    x_new <- data.frame(x = seq(min(x), max(x), length.out = 50))
    ci <- predict(model, x_new, interval = "confidence", level = 0.95)
    pi <- predict(model, x_new, interval = "prediction", level = 0.95)

    list(
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
      residuals = list(mean = round(mean(residuals), 6), std = round(sd(residuals), 4),
                       min = round(min(residuals), 4), max = round(max(residuals), 4),
                       shapiro_p = round(shapiro_res$p.value, 4), normal = shapiro_res$p.value > 0.05),
      fitted_values = round(fitted_values, 4),
      prediction = list(x_values = round(x_new$x, 4), fitted = round(ci[, "fit"], 4),
                        ci_lower = round(ci[, "lwr"], 4), ci_upper = round(ci[, "upr"], 4),
                        pi_lower = round(pi[, "lwr"], 4), pi_upper = round(pi[, "upr"], 4)),
      interpretation = paste0("R-squared = ", round(r_squared * 100, 1), "% of variance explained. ",
                              ifelse(f_p < 0.05, "Model is significant (p < 0.05).", "Model is NOT significant (p >= 0.05)."),
                              ifelse(shapiro_res$p.value > 0.05, " Residuals are normally distributed.", " WARNING: Residuals are NOT normally distributed."))
    )

  } else if (reg_type == "multiple") {
    # ============================================================
    # Multiple Regression
    # ============================================================
    # Input: data frame with multiple columns
    data_df <- as.data.frame(input$data)
    y_col <- input$y_column
    x_cols <- input$x_columns

    if (is.null(y_col) || is.null(x_cols)) {
      stop("Multiple regression requires y_column and x_columns")
    }

    y <- data_df[[y_col]]
    x_data <- data_df[, x_cols, drop = FALSE]
    n <- length(y)

    # Build formula
    formula_str <- paste(y_col, "~", paste(x_cols, collapse = " + "))
    model <- lm(as.formula(formula_str), data = data_df)

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

    # VIF (Variance Inflation Factor)
    vif_values <- list()
    if (length(x_cols) > 1) {
      tryCatch({
        if (requireNamespace("car", quietly = TRUE)) {
          vif <- car::vif(model)
          for (i in 1:length(vif)) {
            vif_values[[x_cols[i]]] <- round(vif[i], 4)
          }
        }
      }, error = function(e) {})
    }

    # Cook's distance
    cooks_d <- cooks.distance(model)
    influential <- which(cooks_d > 4 / n)

    # Residuals
    residuals <- model$residuals
    shapiro_res <- tryCatch(shapiro.test(residuals), error = function(e) list(p.value = NA))

    list(
      regression_type = "multiple",
      formula = formula_str,
      n = n,
      n_predictors = length(x_cols),
      coefficients = coef_list,
      r_squared = round(model_summary$r.squared, 4),
      adj_r_squared = round(model_summary$adj.r.squared, 4),
      f_statistic = round(model_summary$fstatistic[1], 4),
      f_p_value = round(pf(model_summary$fstatistic[1], model_summary$fstatistic[2], model_summary$fstatistic[3], lower.tail = FALSE), 4),
      vif = vif_values,
      cooks_distance = list(
        max = round(max(cooks_d), 6),
        influential_observations = as.list(influential),
        n_influential = length(influential)
      ),
      residuals = list(shapiro_p = round(shapiro_res$p.value, 4), normal = shapiro_res$p.value > 0.05),
      interpretation = sprintf("Multiple R-squared = %.1f%%, %d predictors, %d influential observations",
                               model_summary$r.squared * 100, length(x_cols), length(influential))
    )

  } else if (reg_type == "logistic") {
    # ============================================================
    # Logistic Regression
    # ============================================================
    x <- as.numeric(input$x)
    y <- as.numeric(input$y)  # Binary 0/1

    # Remove NAs
    valid <- !is.na(x) & !is.na(y)
    x <- x[valid]
    y <- y[valid]
    n <- length(x)

    if (n < 10) stop("Need at least 10 data points for logistic regression")

    # Fit logistic regression
    model <- glm(y ~ x, family = binomial(link = "logit"))
    model_summary <- summary(model)

    # Coefficients
    coefficients <- model_summary$coefficients
    coef_list <- list()
    for (i in 1:nrow(coefficients)) {
      coef_list[[rownames(coefficients)[i]]] <- list(
        estimate = round(coefficients[i, 1], 6),
        std_error = round(coefficients[i, 2], 4),
        z_value = round(coefficients[i, 3], 4),
        p_value = round(coefficients[i, 4], 4),
        odds_ratio = round(exp(coefficients[i, 1]), 4)
      )
    }

    # Predicted probabilities
    predicted_prob <- predict(model, type = "response")
    predicted_class <- ifelse(predicted_prob > 0.5, 1, 0)

    # Confusion matrix
    confusion <- table(Predicted = predicted_class, Actual = y)
    accuracy <- sum(diag(confusion)) / sum(confusion) * 100

    # AIC/BIC
    aic <- model$aic
    bic <- BIC(model)

    list(
      regression_type = "logistic",
      formula = "logit(y) = a + bx",
      n = n,
      n_positive = sum(y == 1),
      n_negative = sum(y == 0),
      coefficients = coef_list,
      aic = round(aic, 2),
      bic = round(bic, 2),
      confusion_matrix = confusion,
      accuracy = round(accuracy, 2),
      predicted_probabilities = round(predicted_prob, 4),
      interpretation = sprintf("Logistic regression: accuracy = %.1f%%, AIC = %.1f", accuracy, aic)
    )

  } else if (reg_type == "stepwise") {
    # ============================================================
    # Stepwise Regression
    # ============================================================
    data_df <- as.data.frame(input$data)
    y_col <- input$y_column
    x_cols <- input$x_columns
    direction <- "both"
    if (!is.null(input$direction)) direction <- input$direction

    if (is.null(y_col) || is.null(x_cols)) {
      stop("Stepwise regression requires y_column and x_columns")
    }

    # Full model
    formula_full <- paste(y_col, "~", paste(x_cols, collapse = " + "))
    model_full <- lm(as.formula(formula_full), data = data_df)

    # Null model
    formula_null <- paste(y_col, "~ 1")
    model_null <- lm(as.formula(formula_null), data = data_df)

    # Stepwise selection
    if (direction == "both") {
      model_step <- step(model_null, scope = list(lower = model_null, upper = model_full), direction = "both", trace = 0)
    } else if (direction == "forward") {
      model_step <- step(model_null, scope = list(lower = model_null, upper = model_full), direction = "forward", trace = 0)
    } else if (direction == "backward") {
      model_step <- step(model_full, direction = "backward", trace = 0)
    }

    # Model summary
    model_summary <- summary(model_step)

    # Selected variables
    selected_vars <- names(coef(model_step))[-1]  # Exclude intercept

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

    list(
      regression_type = "stepwise",
      direction = direction,
      n = nrow(data_df),
      selected_variables = selected_vars,
      n_selected = length(selected_vars),
      coefficients = coef_list,
      r_squared = round(model_summary$r.squared, 4),
      adj_r_squared = round(model_summary$adj.r.squared, 4),
      aic = round(AIC(model_step), 2),
      bic = round(BIC(model_step), 2),
      interpretation = sprintf("Stepwise (%s): %d variables selected, R-squared = %.1f%%",
                               direction, length(selected_vars), model_summary$r.squared * 100)
    )

  } else {
    list(error = TRUE, message = paste("Unknown regression type:", reg_type))
  }
}, error = function(e) {
  list(error = TRUE, message = conditionMessage(e), reg_type = reg_type)
})

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
