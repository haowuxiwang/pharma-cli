# Power Analysis and Sample Size Calculation
# Input: JSON with analysis_type and parameters
# Output: JSON with power analysis results

library(jsonlite)

input <- fromJSON(readLines(file("stdin"), warn = FALSE))
analysis_type <- input$analysis_type

result <- tryCatch({
  if (analysis_type == "t_test") {
    # ============================================================
    # t-test Power Analysis
    # ============================================================
    test_type <- input$test_type  # one_sample, two_sample, paired
    effect_size <- input$effect_size  # Cohen's d
    alpha <- ifelse(!is.null(input$alpha), input$alpha, 0.05)
    power <- ifelse(!is.null(input$power), input$power, 0.80)
    n <- input$n  # If provided, calculate power; if NULL, calculate sample size

    if (!is.null(n)) {
      # Calculate power given sample size
      if (test_type == "one_sample") {
        df <- n - 1
        t_crit <- qt(1 - alpha/2, df)
        ncp <- effect_size * sqrt(n)
        power_calc <- 1 - pt(t_crit, df, ncp) + pt(-t_crit, df, ncp)
      } else if (test_type == "two_sample") {
        df <- 2 * n - 2
        t_crit <- qt(1 - alpha/2, df)
        ncp <- effect_size * sqrt(n/2)
        power_calc <- 1 - pt(t_crit, df, ncp) + pt(-t_crit, df, ncp)
      } else if (test_type == "paired") {
        df <- n - 1
        t_crit <- qt(1 - alpha/2, df)
        ncp <- effect_size * sqrt(n)
        power_calc <- 1 - pt(t_crit, df, ncp) + pt(-t_crit, df, ncp)
      }

      list(
        analysis_type = "power",
        test_type = test_type,
        effect_size = effect_size,
        alpha = alpha,
        n = n,
        power = round(power_calc, 4),
        interpretation = sprintf("Power = %.2f%% for %s test with n=%d, d=%.2f, alpha=%.3f",
                                 power_calc * 100, test_type, n, effect_size, alpha)
      )
    } else {
      # Calculate sample size given power
      # Binary search for sample size
      n_min <- 2
      n_max <- 10000

      while (n_min < n_max) {
        n_mid <- floor((n_min + n_max) / 2)

        if (test_type == "one_sample") {
          df <- n_mid - 1
          t_crit <- qt(1 - alpha/2, df)
          ncp <- effect_size * sqrt(n_mid)
          power_calc <- 1 - pt(t_crit, df, ncp) + pt(-t_crit, df, ncp)
        } else if (test_type == "two_sample") {
          df <- 2 * n_mid - 2
          t_crit <- qt(1 - alpha/2, df)
          ncp <- effect_size * sqrt(n_mid/2)
          power_calc <- 1 - pt(t_crit, df, ncp) + pt(-t_crit, df, ncp)
        } else if (test_type == "paired") {
          df <- n_mid - 1
          t_crit <- qt(1 - alpha/2, df)
          ncp <- effect_size * sqrt(n_mid)
          power_calc <- 1 - pt(t_crit, df, ncp) + pt(-t_crit, df, ncp)
        }

        if (power_calc >= power) {
          n_max <- n_mid
        } else {
          n_min <- n_mid + 1
        }
      }

      list(
        analysis_type = "sample_size",
        test_type = test_type,
        effect_size = effect_size,
        alpha = alpha,
        power = power,
        n = n_min,
        interpretation = sprintf("Required n = %d per group for %s test with d=%.2f, alpha=%.3f, power=%.2f",
                                 n_min, test_type, effect_size, alpha, power)
      )
    }

  } else if (analysis_type == "anova") {
    # ============================================================
    # ANOVA Power Analysis
    # ============================================================
    n_groups <- input$n_groups
    effect_size <- input$effect_size  # Cohen's f
    alpha <- ifelse(!is.null(input$alpha), input$alpha, 0.05)
    power <- ifelse(!is.null(input$power), input$power, 0.80)
    n <- input$n  # per group

    if (!is.null(n)) {
      # Calculate power
      df1 <- n_groups - 1
      df2 <- n_groups * (n - 1)
      ncp <- effect_size^2 * n * n_groups
      f_crit <- qf(1 - alpha, df1, df2)
      power_calc <- 1 - pf(f_crit, df1, df2, ncp)

      list(
        analysis_type = "power",
        test_type = "anova",
        n_groups = n_groups,
        effect_size = effect_size,
        alpha = alpha,
        n_per_group = n,
        total_n = n * n_groups,
        power = round(power_calc, 4),
        interpretation = sprintf("Power = %.2f%% for ANOVA with %d groups, n=%d per group, f=%.2f",
                                 power_calc * 100, n_groups, n, effect_size)
      )
    } else {
      # Calculate sample size per group
      n_min <- 2
      n_max <- 10000

      while (n_min < n_max) {
        n_mid <- floor((n_min + n_max) / 2)
        df1 <- n_groups - 1
        df2 <- n_groups * (n_mid - 1)
        ncp <- effect_size^2 * n_mid * n_groups
        f_crit <- qf(1 - alpha, df1, df2)
        power_calc <- 1 - pf(f_crit, df1, df2, ncp)

        if (power_calc >= power) {
          n_max <- n_mid
        } else {
          n_min <- n_mid + 1
        }
      }

      list(
        analysis_type = "sample_size",
        test_type = "anova",
        n_groups = n_groups,
        effect_size = effect_size,
        alpha = alpha,
        power = power,
        n_per_group = n_min,
        total_n = n_min * n_groups,
        interpretation = sprintf("Required n = %d per group (%d total) for ANOVA with %d groups, f=%.2f",
                                 n_min, n_min * n_groups, n_groups, effect_size)
      )
    }

  } else if (analysis_type == "proportion") {
    # ============================================================
    # Proportion Power Analysis
    # ============================================================
    p0 <- input$p0  # Null proportion
    p1 <- input$p1  # Alternative proportion
    alpha <- ifelse(!is.null(input$alpha), input$alpha, 0.05)
    power <- ifelse(!is.null(input$power), input$power, 0.80)

    # Calculate sample size using normal approximation
    z_alpha <- qnorm(1 - alpha/2)
    z_beta <- qnorm(power)

    # Pooled proportion
    p_bar <- (p0 + p1) / 2

    # Sample size formula
    n <- ((z_alpha * sqrt(p0 * (1 - p0)) + z_beta * sqrt(p1 * (1 - p1))) / (p1 - p0))^2
    n <- ceiling(n)

    list(
      analysis_type = "sample_size",
      test_type = "proportion",
      p0 = p0,
      p1 = p1,
      alpha = alpha,
      power = power,
      n = n,
      effect_size = round(abs(p1 - p0) / sqrt(p0 * (1 - p0)), 4),
      interpretation = sprintf("Required n = %d to detect proportion change from %.2f to %.2f",
                               n, p0, p1)
    )

  } else if (analysis_type == "effect_size") {
    # ============================================================
    # Effect Size Calculations
    # ============================================================
    metric <- input$metric  # cohens_d, cohens_f, eta_squared

    if (metric == "cohens_d") {
      m1 <- input$m1
      m2 <- input$m2
      sd1 <- input$sd1
      sd2 <- input$sd2
      n1 <- input$n1
      n2 <- input$n2

      # Pooled SD
      sd_pooled <- sqrt(((n1 - 1) * sd1^2 + (n2 - 1) * sd2^2) / (n1 + n2 - 2))
      d <- (m1 - m2) / sd_pooled

      # Interpretation
      d_abs <- abs(d)
      if (d_abs < 0.2) {
        interp <- "negligible"
      } else if (d_abs < 0.5) {
        interp <- "small"
      } else if (d_abs < 0.8) {
        interp <- "medium"
      } else {
        interp <- "large"
      }

      list(
        analysis_type = "effect_size",
        metric = "cohens_d",
        value = round(d, 4),
        magnitude = interp,
        interpretation = sprintf("Cohen's d = %.3f (%s effect)", d, interp)
      )
    } else if (metric == "eta_squared") {
      ss_effect <- input$ss_effect
      ss_total <- input$ss_total

      eta_sq <- ss_effect / ss_total

      if (eta_sq < 0.01) {
        interp <- "negligible"
      } else if (eta_sq < 0.06) {
        interp <- "small"
      } else if (eta_sq < 0.14) {
        interp <- "medium"
      } else {
        interp <- "large"
      }

      list(
        analysis_type = "effect_size",
        metric = "eta_squared",
        value = round(eta_sq, 4),
        magnitude = interp,
        interpretation = sprintf("Eta-squared = %.3f (%s effect)", eta_sq, interp)
      )
    } else {
      list(error = TRUE, message = paste("Unknown effect size metric:", metric))
    }

  } else {
    list(
      error = TRUE,
      message = paste("Unknown analysis_type:", analysis_type),
      supported_types = c("t_test", "anova", "proportion", "effect_size")
    )
  }
}, error = function(e) {
  list(error = TRUE, message = conditionMessage(e), analysis_type = analysis_type)
})

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
