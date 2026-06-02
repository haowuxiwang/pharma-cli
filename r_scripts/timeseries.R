# Time Series Analysis
# Input: JSON with analysis_type and data
# Output: JSON with time series results

library(jsonlite)

# Read input from stdin
con <- file("stdin", "r")
input_lines <- readLines(con, warn = FALSE)
close(con)
input <- fromJSON(paste(input_lines, collapse = "\n"))
analysis_type <- input$analysis_type

result <- tryCatch({
  if (analysis_type == "exp_smoothing") {
    # ============================================================
    # Exponential Smoothing (Holt-Winters)
    # ============================================================
    values <- as.numeric(input$values)
    frequency <- 1
    if (!is.null(input$frequency)) frequency <- as.integer(input$frequency)
    method <- "auto"
    if (!is.null(input$method)) method <- input$method

    n <- length(values)

    # Create time series object
    ts_data <- ts(values, frequency = frequency)

    # Fit exponential smoothing model
    if (frequency > 1) {
      fit <- HoltWinters(ts_data)
      model_type <- "holt_winters_seasonal"
    } else {
      if (n >= 6) {
        fit <- HoltWinters(ts_data)
        model_type <- "holt_winters"
      } else {
        fit <- HoltWinters(ts_data, beta = FALSE, gamma = FALSE)
        model_type <- "simple_exponential"
      }
    }

    # Fitted values
    fitted_values <- as.numeric(fitted(fit)[, 1])

    # Parameters
    alpha <- fit$alpha
    beta <- NA
    if (!is.null(fit$beta)) beta <- fit$beta
    gamma <- NA
    if (!is.null(fit$gamma)) gamma <- fit$gamma

    # Forecast
    n_forecast <- 10
    if (!is.null(input$n_forecast)) n_forecast <- as.integer(input$n_forecast)
    forecast_result <- predict(fit, n.ahead = n_forecast)
    forecast_values <- as.numeric(forecast_result)

    # Residuals
    residuals <- values - fitted_values
    rmse <- sqrt(mean(residuals^2, na.rm = TRUE))
    mae <- mean(abs(residuals), na.rm = TRUE)

    list(
      analysis_type = "exp_smoothing",
      model_type = model_type,
      n = n,
      parameters = list(alpha = round(alpha, 4), beta = round(beta, 4), gamma = round(gamma, 4)),
      fitted_values = round(fitted_values, 4),
      residuals = round(residuals, 4),
      forecast = round(forecast_values, 4),
      n_forecast = n_forecast,
      metrics = list(rmse = round(rmse, 4), mae = round(mae, 4)),
      interpretation = sprintf(
        "Exponential smoothing (%s): alpha=%.3f, RMSE=%.4f, MAE=%.4f",
        model_type, alpha, rmse, mae
      )
    )

  } else if (analysis_type == "arima") {
    # ============================================================
    # ARIMA Model
    # ============================================================
    values <- as.numeric(input$values)
    n <- length(values)

    # Use specified order or default to ARIMA(1,0,0)
    order <- c(1L, 0L, 0L)
    if (!is.null(input$order)) {
      order <- as.integer(input$order)
      if (length(order) != 3) order <- c(1L, 0L, 0L)
    }

    # Fit ARIMA model
    fit <- arima(values, order = order)

    # Fitted values
    fitted_values <- as.numeric(fitted(fit))

    # Residuals
    residuals <- as.numeric(fit$residuals)

    # Forecast
    n_forecast <- 10L
    if (!is.null(input$n_forecast)) {
      n_forecast <- as.integer(round(as.numeric(input$n_forecast)))
    }
    forecast_result <- predict(fit, n.ahead = n_forecast)
    forecast_values <- as.numeric(forecast_result$pred)
    forecast_se <- as.numeric(forecast_result$se)

    # Confidence intervals
    ci_lower <- forecast_values - 1.96 * forecast_se
    ci_upper <- forecast_values + 1.96 * forecast_se

    list(
      analysis_type = "arima",
      order = order,
      n = n,
      coefficients = as.list(round(fit$coef, 4)),
      aic = round(fit$aic, 2),
      bic = round(fit$bic, 2),
      fitted_values = round(fitted_values, 4),
      residuals = round(residuals, 4),
      forecast = round(forecast_values, 4),
      forecast_se = round(forecast_se, 4),
      ci_lower = round(ci_lower, 4),
      ci_upper = round(ci_upper, 4),
      n_forecast = as.integer(n_forecast),
      interpretation = sprintf(
        "ARIMA(%d,%d,%d): AIC=%.2f",
        order[1], order[2], order[3], fit$aic
      )
    )

  } else if (analysis_type == "decomposition") {
    # ============================================================
    # Seasonal Decomposition
    # ============================================================
    values <- as.numeric(input$values)
    frequency <- 12
    if (!is.null(input$frequency)) frequency <- as.integer(input$frequency)
    type <- "additive"
    if (!is.null(input$type)) type <- input$type

    n <- length(values)

    if (n < 2 * frequency) {
      stop("Need at least 2 full seasonal cycles for decomposition")
    }

    # Create time series object
    ts_data <- ts(values, frequency = frequency)

    # Decompose
    if (type == "additive") {
      decomp <- decompose(ts_data, type = "additive")
    } else {
      decomp <- decompose(ts_data, type = "multiplicative")
    }

    # Extract components
    trend <- as.numeric(decomp$trend)
    seasonal <- as.numeric(decomp$seasonal)
    random <- as.numeric(decomp$random)

    # Remove NAs for summary statistics
    trend_clean <- trend[!is.na(trend)]
    seasonal_clean <- seasonal[!is.na(seasonal)]
    random_clean <- random[!is.na(random)]

    # Strength of components
    var_seasonal <- var(seasonal_clean)
    var_random <- var(random_clean)
    seasonal_strength <- 1 - var_random / (var_seasonal + var_random)

    list(
      analysis_type = "decomposition",
      type = type,
      n = n,
      frequency = frequency,
      trend = round(trend, 4),
      seasonal = round(seasonal, 4),
      random = round(random, 4),
      summary = list(
        trend_range = round(range(trend_clean, na.rm = TRUE), 4),
        seasonal_range = round(range(seasonal_clean, na.rm = TRUE), 4),
        random_sd = round(sd(random_clean, na.rm = TRUE), 4),
        seasonal_strength = round(seasonal_strength, 4)
      ),
      interpretation = sprintf(
        "%s decomposition: seasonal strength = %.3f, random SD = %.4f",
        type, seasonal_strength, sd(random_clean, na.rm = TRUE)
      )
    )

  } else if (analysis_type == "acf") {
    # ============================================================
    # ACF / PACF Analysis
    # ============================================================
    values <- as.numeric(input$values)
    n <- length(values)
    max_lag <- min(20, n / 4)
    if (!is.null(input$max_lag)) max_lag <- as.integer(input$max_lag)

    # Calculate ACF
    acf_result <- acf(values, lag.max = max_lag, plot = FALSE, type = "correlation")
    acf_values <- as.numeric(acf_result$acf)

    # Calculate PACF
    pacf_result <- pacf(values, lag.max = max_lag, plot = FALSE)
    pacf_values <- as.numeric(pacf_result$acf)

    # Significance threshold (95% CI)
    threshold <- 1.96 / sqrt(n)

    # Significant lags (excluding lag 0 for ACF)
    sig_acf <- which(abs(acf_values[-1]) > threshold)
    sig_pacf <- which(abs(pacf_values) > threshold)

    # Simple heuristic for order suggestion
    if (length(sig_pacf) > 0 && max(sig_pacf) <= 2) {
      suggested_order <- sprintf("AR(%d)", max(sig_pacf))
    } else if (length(sig_acf) > 0 && max(sig_acf) <= 2) {
      suggested_order <- sprintf("MA(%d)", max(sig_acf))
    } else {
      suggested_order <- "Check ACF/PACF patterns"
    }

    list(
      analysis_type = "acf",
      n = n,
      max_lag = max_lag,
      acf = round(acf_values, 4),
      pacf = round(pacf_values, 4),
      threshold = round(threshold, 4),
      significant_acf_lags = sig_acf,
      significant_pacf_lags = sig_pacf,
      suggested_order = suggested_order,
      interpretation = sprintf(
        "ACF/PACF: %d significant ACF lags, %d significant PACF lags. Suggested: %s",
        length(sig_acf), length(sig_pacf), suggested_order
      )
    )

  } else {
    list(
      error = TRUE,
      message = paste("Unknown analysis_type:", analysis_type),
      supported_types = c("exp_smoothing", "arima", "decomposition", "acf")
    )
  }
}, error = function(e) {
  list(
    error = TRUE,
    message = conditionMessage(e),
    analysis_type = analysis_type
  )
})

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
