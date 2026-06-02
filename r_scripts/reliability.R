# Reliability Analysis
# Input: JSON with analysis_type and data
# Output: JSON with reliability results

library(jsonlite)

input <- fromJSON(readLines(file("stdin"), warn = FALSE))
analysis_type <- input$analysis_type

result <- tryCatch({
  if (analysis_type == "weibull") {
    # ============================================================
    # Weibull Analysis
    # ============================================================
    times <- as.numeric(input$times)
    status <- as.numeric(input$status)  # 1 = failure, 0 = censored

    n <- length(times)
    n_failures <- sum(status == 1)
    n_censored <- sum(status == 0)

    # Fit Weibull distribution using MLE
    # Log-likelihood for Weibull
    weibull_loglik <- function(params) {
      beta <- params[1]  # shape
      eta <- params[2]   # scale

      if (beta <= 0 || eta <= 0) return(1e10)

      ll <- 0
      for (i in 1:n) {
        if (status[i] == 1) {
          # Failure
          ll <- ll + log(beta/eta) + (beta-1)*log(times[i]/eta) - (times[i]/eta)^beta
        } else {
          # Censored
          ll <- ll - (times[i]/eta)^beta
        }
      }
      return(-ll)
    }

    # Initial estimates
    # Use median rank regression for initial estimates
    failures <- times[status == 1]
    if (length(failures) < 2) {
      stop("Need at least 2 failures for Weibull analysis")
    }

    # Simple initial estimates
    beta_init <- 1.0
    eta_init <- median(failures)

    # Optimize
    opt <- optim(c(beta_init, eta_init), weibull_loglik, method="L-BFGS-B",
                 lower=c(0.01, 0.01), upper=c(100, max(times)*10))

    beta <- opt$par[1]  # shape parameter
    eta <- opt$par[2]   # scale parameter (characteristic life)

    # Calculate reliability at specific time
    if (!is.null(input$time)) {
      t <- input$time
      reliability <- exp(-(t/eta)^beta)
      failure_prob <- 1 - reliability
    }

    # Calculate B-life (time for X% failure)
    b_lives <- list()
    for (pct in c(1, 5, 10, 50)) {
      t_b <- eta * (-log(1 - pct/100))^(1/beta)
      b_lives[[paste0("B", pct)]] <- round(t_b, 4)
    }

    # MTTF (Mean Time To Failure)
    mttf <- eta * gamma(1 + 1/beta)

    # Confidence intervals (Fisher matrix approximation)
    # Simplified CI calculation
    se_beta <- beta / sqrt(n_failures)
    se_eta <- eta / sqrt(n_failures)

    beta_ci_lower <- beta * exp(-1.96 * sqrt(log(1 + (se_beta/beta)^2)))
    beta_ci_upper <- beta * exp(1.96 * sqrt(log(1 + (se_beta/beta)^2)))
    eta_ci_lower <- eta * exp(-1.96 * sqrt(log(1 + (se_eta/eta)^2)))
    eta_ci_upper <- eta * exp(1.96 * sqrt(log(1 + (se_eta/eta)^2)))

    # Determine failure pattern
    if (beta < 1) {
      failure_pattern <- "Decreasing failure rate (infant mortality)"
    } else if (beta == 1) {
      failure_pattern <- "Constant failure rate (random failures)"
    } else {
      failure_pattern <- "Increasing failure rate (wear-out)"
    }

    list(
      analysis_type = "weibull",
      n = n,
      n_failures = n_failures,
      n_censored = n_censored,
      parameters = list(
        shape = round(beta, 4),
        scale = round(eta, 4),
        shape_ci_lower = round(beta_ci_lower, 4),
        shape_ci_upper = round(beta_ci_upper, 4),
        scale_ci_lower = round(eta_ci_lower, 4),
        scale_ci_upper = round(eta_ci_upper, 4)
      ),
      b_lives = b_lives,
      mttf = round(mttf, 4),
      failure_pattern = failure_pattern,
      reliability_at_time = if (!is.null(input$time)) round(reliability, 6) else NA,
      failure_prob_at_time = if (!is.null(input$time)) round(failure_prob, 6) else NA,
      interpretation = sprintf(
        "Weibull shape = %.2f (%s), scale = %.2f. B5 life = %.2f, B10 life = %.2f, MTTF = %.2f",
        beta, failure_pattern, eta, b_lives$B5, b_lives$B10, mttf
      )
    )

  } else if (analysis_type == "kaplan_meier") {
    # ============================================================
    # Kaplan-Meier Survival Analysis
    # ============================================================
    times <- as.numeric(input$times)
    status <- as.numeric(input$status)  # 1 = death/failure, 0 = censored

    # Sort by time
    ord <- order(times)
    times <- times[ord]
    status <- status[ord]

    n <- length(times)
    unique_times <- sort(unique(times[status == 1]))

    # Calculate KM estimate
    km_data <- data.frame(
      time = numeric(),
      n_at_risk = numeric(),
      n_events = numeric(),
      survival = numeric(),
      std_error = numeric()
    )

    surv <- 1.0
    var_sum <- 0

    for (t in unique_times) {
      n_at_risk <- sum(times >= t)
      n_events <- sum(times == t & status == 1)
      n_censored <- sum(times == t & status == 0)

      if (n_at_risk > 0) {
        surv <- surv * (1 - n_events / n_at_risk)
        var_sum <- var_sum + n_events / (n_at_risk * (n_at_risk - n_events))
      }

      se <- surv * sqrt(var_sum)

      km_data <- rbind(km_data, data.frame(
        time = t,
        n_at_risk = n_at_risk,
        n_events = n_events,
        survival = round(surv, 6),
        std_error = round(se, 6)
      ))
    }

    # Median survival time
    median_surv <- NA
    for (i in 1:nrow(km_data)) {
      if (km_data$survival[i] <= 0.5) {
        median_surv <- km_data$time[i]
        break
      }
    }

    # Survival at specific time points
    survival_at <- list()
    if (!is.null(input$time_points)) {
      for (tp in input$time_points) {
        idx <- max(which(km_data$time <= tp))
        if (length(idx) > 0) {
          survival_at[[as.character(tp)]] <- km_data$survival[idx]
        } else {
          survival_at[[as.character(tp)]] <- 1.0
        }
      }
    }

    list(
      analysis_type = "kaplan_meier",
      n = n,
      n_events = sum(status == 1),
      n_censored = sum(status == 0),
      median_survival = median_surv,
      survival_table = km_data,
      survival_at = survival_at,
      interpretation = sprintf(
        "Kaplan-Meier: %d events, %d censored. Median survival = %s",
        sum(status == 1), sum(status == 0),
        ifelse(is.na(median_surv), "not reached", as.character(round(median_surv, 2)))
      )
    )

  } else if (analysis_type == "distribution") {
    # ============================================================
    # Distribution Fitting
    # ============================================================
    times <- as.numeric(input$times)
    status <- as.numeric(input$status)

    n <- length(times)
    failures <- times[status == 1]

    if (length(failures) < 3) {
      stop("Need at least 3 failures for distribution fitting")
    }

    # Fit multiple distributions
    fits <- list()

    # Weibull
    tryCatch({
      opt_w <- optim(c(1, median(failures)), function(p) {
        beta <- p[1]; eta <- p[2]
        if (beta <= 0 || eta <= 0) return(1e10)
        -sum(dweibull(failures, beta, eta, log=TRUE))
      }, method="L-BFGS-B", lower=c(0.01, 0.01))
      aic_w <- 2 * opt_w$value + 2 * 2
      fits$weibull <- list(shape=round(opt_w$par[1], 4), scale=round(opt_w$par[2], 4), aic=round(aic_w, 2))
    }, error = function(e) {})

    # Lognormal
    tryCatch({
      log_f <- log(failures)
      mu <- mean(log_f)
      sigma <- sd(log_f)
      aic_ln <- -2 * sum(dlnorm(failures, mu, sigma, log=TRUE)) + 2 * 2
      fits$lognormal <- list(mu=round(mu, 4), sigma=round(sigma, 4), aic=round(aic_ln, 2))
    }, error = function(e) {})

    # Exponential
    tryCatch({
      rate <- 1 / mean(failures)
      aic_exp <- -2 * sum(dexp(failures, rate, log=TRUE)) + 1
      fits$exponential <- list(rate=round(rate, 6), aic=round(aic_exp, 2))
    }, error = function(e) {})

    # Find best distribution
    aics <- sapply(fits, function(f) f$aic)
    best <- names(which.min(aics))

    list(
      analysis_type = "distribution",
      n = n,
      n_failures = length(failures),
      fits = fits,
      best_distribution = best,
      best_aic = fits[[best]]$aic,
      interpretation = sprintf("Best fit: %s (AIC = %.2f)", best, fits[[best]]$aic)
    )

  } else if (analysis_type == "stability") {
    # ============================================================
    # Stability Study (Shelf Life Estimation)
    # ============================================================
    # Common in pharma: stability testing at different time points
    times <- as.numeric(input$times)
    values <- as.numeric(input$values)
    usl <- input$usl
    lsl <- input$lsl
    confidence <- ifelse(!is.null(input$confidence), input$confidence, 0.95)

    n <- length(times)

    # Linear regression: value ~ time
    model <- lm(values ~ times)
    intercept <- coef(model)[1]
    slope <- coef(model)[2]
    r_squared <- summary(model)$r.squared

    # Calculate shelf life (time when limit is reached)
    if (!is.null(lsl)) {
      # Lower limit: shelf life = (lsl - intercept) / slope
      shelf_life_lower <- (lsl - intercept) / slope
    } else {
      shelf_life_lower <- NA
    }

    if (!is.null(usl)) {
      # Upper limit: shelf life = (usl - intercept) / slope
      shelf_life_upper <- (usl - intercept) / slope
    } else {
      shelf_life_upper <- NA
    }

    # Use the shorter shelf life
    shelf_life <- min(shelf_life_lower, shelf_life_upper, na.rm = TRUE)

    # 95% CI for shelf life (simplified)
    se_slope <- summary(model)$coefficients[2, 2]
    t_crit <- qt(1 - (1-confidence)/2, n - 2)

    # Prediction at each time point
    pred <- predict(model, newdata=data.frame(times=times), interval="prediction", level=confidence)

    list(
      analysis_type = "stability",
      n = n,
      time_range = list(min=min(times), max=max(times)),
      regression = list(
        intercept = round(intercept, 4),
        slope = round(slope, 6),
        r_squared = round(r_squared, 4),
        p_value = round(summary(model)$coefficients[2, 4], 4)
      ),
      limits = list(usl = usl, lsl = lsl),
      shelf_life = round(shelf_life, 2),
      shelf_life_lower_limit = round(shelf_life_lower, 2),
      shelf_life_upper_limit = round(shelf_life_upper, 2),
      confidence = confidence,
      interpretation = sprintf(
        "Stability: slope = %.6f per unit time. Estimated shelf life = %.1f time units (at %.0f%% confidence)",
        slope, shelf_life, confidence * 100
      )
    )

  } else {
    list(
      error = TRUE,
      message = paste("Unknown analysis_type:", analysis_type),
      supported_types = c("weibull", "kaplan_meier", "distribution", "stability")
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
