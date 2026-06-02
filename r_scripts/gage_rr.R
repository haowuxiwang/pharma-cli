# Gage R&R / MSA Analysis
# Input: JSON with analysis_type and data
# Output: JSON with MSA results

library(jsonlite)

# Read input from stdin
input <- fromJSON(readLines(file("stdin"), warn = FALSE))

analysis_type <- input$analysis_type

result <- tryCatch({
  if (analysis_type == "crossed") {
    # ============================================================
    # Crossed Gage R&R (ANOVA Method)
    # ============================================================
    measurements <- input$measurements
    parts <- input$parts
    operators <- input$operators
    tolerance <- input$tolerance

    n <- length(measurements)
    part_levels <- unique(parts)
    op_levels <- unique(operators)
    k <- length(part_levels)
    m <- length(op_levels)
    r <- n / (k * m)

    df <- data.frame(
      measurement = as.numeric(measurements),
      part = factor(parts, levels = part_levels),
      operator = factor(operators, levels = op_levels)
    )

    # Check if we have replication (r > 1) for interaction
    if (r > 1) {
      # Full model with interaction
      model <- aov(measurement ~ part * operator, data = df)
      anova_table <- anova(model)

      ms_part <- anova_table["part", "Mean Sq"]
      ms_oper <- anova_table["operator", "Mean Sq"]
      ms_interact <- anova_table["part:operator", "Mean Sq"]
      ms_error <- anova_table["Residuals", "Mean Sq"]
      df_part <- anova_table["part", "Df"]
      df_oper <- anova_table["operator", "Df"]
      df_interact <- anova_table["part:operator", "Df"]
      df_error <- anova_table["Residuals", "Df"]

      # Variance components
      sigma2_error <- ms_error
      sigma2_interaction <- (ms_interact - ms_error) / r
      sigma2_operator <- (ms_oper - ms_interact) / (k * r)
      sigma2_part <- (ms_part - ms_interact) / (m * r)

      has_interaction <- TRUE
      p_interaction <- anova_table["part:operator", "Pr(>F)"]
    } else {
      # No replication: use model without interaction
      model <- aov(measurement ~ part + operator, data = df)
      anova_table <- anova(model)

      ms_part <- anova_table["part", "Mean Sq"]
      ms_oper <- anova_table["operator", "Mean Sq"]
      ms_error <- anova_table["Residuals", "Mean Sq"]
      df_part <- anova_table["part", "Df"]
      df_oper <- anova_table["operator", "Df"]
      df_error <- anova_table["Residuals", "Df"]

      ms_interact <- NA
      df_interact <- 0
      sigma2_interaction <- 0

      # Variance components (no interaction)
      sigma2_error <- ms_error
      sigma2_operator <- (ms_oper - ms_error) / (k)
      sigma2_part <- (ms_part - ms_error) / (m)

      has_interaction <- FALSE
      p_interaction <- NA
    }

    # Handle negative variance components
    if (is.na(sigma2_interaction) || sigma2_interaction < 0) sigma2_interaction <- 0
    if (is.na(sigma2_operator) || sigma2_operator < 0) sigma2_operator <- 0
    if (is.na(sigma2_part) || sigma2_part < 0) sigma2_part <- 0

    sigma2_grr <- sigma2_error + sigma2_interaction + sigma2_operator
    sigma2_total <- sigma2_part + sigma2_grr

    sd_repeatability <- sqrt(sigma2_error)
    sd_reproducibility <- sqrt(sigma2_operator + sigma2_interaction)
    sd_grr <- sqrt(sigma2_grr)
    sd_part <- sqrt(sigma2_part)
    sd_total <- sqrt(sigma2_total)

    pct_contrib_repeatability <- (sigma2_error / sigma2_total) * 100
    pct_contrib_reproducibility <- ((sigma2_operator + sigma2_interaction) / sigma2_total) * 100
    pct_contrib_grr <- (sigma2_grr / sigma2_total) * 100
    pct_contrib_part <- (sigma2_part / sigma2_total) * 100

    sv_repeatability <- 6 * sd_repeatability
    sv_reproducibility <- 6 * sd_reproducibility
    sv_grr <- 6 * sd_grr
    sv_part <- 6 * sd_part
    sv_total <- 6 * sd_total

    pct_sv_repeatability <- (sd_repeatability / sd_total) * 100
    pct_sv_reproducibility <- (sd_reproducibility / sd_total) * 100
    pct_sv_grr <- (sd_grr / sd_total) * 100
    pct_sv_part <- (sd_part / sd_total) * 100

    if (!is.null(tolerance) && !is.na(tolerance) && tolerance > 0) {
      pct_tolerance_repeatability <- (sv_repeatability / tolerance) * 100
      pct_tolerance_reproducibility <- (sv_reproducibility / tolerance) * 100
      pct_tolerance_grr <- (sv_grr / tolerance) * 100
      pct_tolerance_part <- (sv_part / tolerance) * 100
    } else {
      pct_tolerance_repeatability <- NA
      pct_tolerance_reproducibility <- NA
      pct_tolerance_grr <- NA
      pct_tolerance_part <- NA
    }

    ndc <- floor(1.41 * (sd_part / sd_grr))

    if (pct_sv_grr < 10) {
      rating <- "Excellent"
      rating_desc <- "Measurement system is acceptable"
    } else if (pct_sv_grr < 30) {
      rating <- "Acceptable"
      rating_desc <- "Measurement system may be acceptable depending on application"
    } else {
      rating <- "Unacceptable"
      rating_desc <- "Measurement system needs improvement"
    }

    # Build ANOVA table output
    if (has_interaction) {
      anova_sources <- c("Part", "Operator", "Part:Operator", "Residuals", "Total")
      anova_df <- c(df_part, df_oper, df_interact, df_error, df_part + df_oper + df_interact + df_error)
      anova_ss <- c(anova_table["part", "Sum Sq"], anova_table["operator", "Sum Sq"],
                    anova_table["part:operator", "Sum Sq"], anova_table["Residuals", "Sum Sq"],
                    sum(anova_table[, "Sum Sq"]))
      anova_ms <- c(ms_part, ms_oper, ms_interact, ms_error, NA)
      anova_f <- c(anova_table["part", "F value"], anova_table["operator", "F value"],
                   anova_table["part:operator", "F value"], NA, NA)
      anova_p <- c(anova_table["part", "Pr(>F)"], anova_table["operator", "Pr(>F)"],
                   anova_table["part:operator", "Pr(>F)"], NA, NA)
    } else {
      anova_sources <- c("Part", "Operator", "Residuals", "Total")
      anova_df <- c(df_part, df_oper, df_error, df_part + df_oper + df_error)
      anova_ss <- c(anova_table["part", "Sum Sq"], anova_table["operator", "Sum Sq"],
                    anova_table["Residuals", "Sum Sq"], sum(anova_table[, "Sum Sq"]))
      anova_ms <- c(ms_part, ms_oper, ms_error, NA)
      anova_f <- c(anova_table["part", "F value"], anova_table["operator", "F value"], NA, NA)
      anova_p <- c(anova_table["part", "Pr(>F)"], anova_table["operator", "Pr(>F)"], NA, NA)
    }

    interaction_sig <- !is.null(p_interaction) && length(p_interaction) > 0 && !is.na(p_interaction) && p_interaction < 0.05

    list(
      analysis_type = "crossed_gage_rr",
      n = n,
      n_parts = k,
      n_operators = m,
      n_replicates = as.integer(r),
      has_interaction = has_interaction,
      anova_table = list(
        source = anova_sources,
        df = anova_df,
        sum_sq = anova_ss,
        mean_sq = anova_ms,
        f_value = anova_f,
        p_value = anova_p
      ),
      variance_components = list(
        repeatability = list(variance = sigma2_error, sd = sd_repeatability, sv = sv_repeatability),
        reproducibility = list(variance = sigma2_operator + sigma2_interaction, sd = sd_reproducibility, sv = sv_reproducibility,
                               operator = list(variance = sigma2_operator, sd = sqrt(sigma2_operator)),
                               interaction = list(variance = sigma2_interaction, sd = sqrt(sigma2_interaction))),
        grr = list(variance = sigma2_grr, sd = sd_grr, sv = sv_grr),
        part_to_part = list(variance = sigma2_part, sd = sd_part, sv = sv_part),
        total = list(variance = sigma2_total, sd = sd_total, sv = sv_total)
      ),
      contribution = list(repeatability = round(pct_contrib_repeatability, 2), reproducibility = round(pct_contrib_reproducibility, 2),
                          grr = round(pct_contrib_grr, 2), part_to_part = round(pct_contrib_part, 2)),
      study_variation = list(repeatability = round(pct_sv_repeatability, 2), reproducibility = round(pct_sv_reproducibility, 2),
                             grr = round(pct_sv_grr, 2), part_to_part = round(pct_sv_part, 2)),
      tolerance = list(repeatability = pct_tolerance_repeatability, reproducibility = pct_tolerance_reproducibility,
                       grr = pct_tolerance_grr, part_to_part = pct_tolerance_part),
      ndc = ndc,
      rating = rating,
      rating_desc = rating_desc,
      interaction_significant = interaction_sig,
      interpretation = sprintf("Gage R&R = %.1f%% of study variation. %s (ndc = %d)", pct_sv_grr, rating_desc, ndc)
    )

  } else if (analysis_type == "nested") {
    # ============================================================
    # Nested Gage R&R
    # ============================================================
    measurements <- as.numeric(input$measurements)
    parts <- input$parts
    operators <- input$operators
    tolerance <- input$tolerance

    df <- data.frame(
      measurement = measurements,
      part = factor(parts),
      operator = factor(operators)
    )

    model <- aov(measurement ~ operator / part, data = df)
    anova_table <- anova(model)

    ms_operator <- anova_table["operator", "Mean Sq"]
    ms_part_in_op <- anova_table["operator:part", "Mean Sq"]
    ms_error <- anova_table["Residuals", "Mean Sq"]

    r <- max(table(df$operator))

    sigma2_error <- ms_error
    sigma2_part_in_op <- (ms_part_in_op - ms_error) / r
    sigma2_operator <- (ms_operator - ms_part_in_op) / (length(unique(df$part)) / length(unique(df$operator)))

    if (is.na(sigma2_part_in_op) || sigma2_part_in_op < 0) sigma2_part_in_op <- 0
    if (is.na(sigma2_operator) || sigma2_operator < 0) sigma2_operator <- 0

    sigma2_grr <- sigma2_error + sigma2_operator
    sigma2_part <- sigma2_part_in_op
    sigma2_total <- sigma2_part + sigma2_grr

    sd_repeatability <- sqrt(sigma2_error)
    sd_reproducibility <- sqrt(sigma2_operator)
    sd_grr <- sqrt(sigma2_grr)
    sd_part <- sqrt(sigma2_part)
    sd_total <- sqrt(sigma2_total)

    pct_contrib_grr <- (sigma2_grr / sigma2_total) * 100
    pct_contrib_part <- (sigma2_part / sigma2_total) * 100
    pct_sv_grr <- (sd_grr / sd_total) * 100
    ndc <- floor(1.41 * (sd_part / sd_grr))

    if (pct_sv_grr < 10) {
      rating <- "Excellent"
      rating_desc <- "Measurement system is acceptable"
    } else if (pct_sv_grr < 30) {
      rating <- "Acceptable"
      rating_desc <- "Measurement system may be acceptable depending on application"
    } else {
      rating <- "Unacceptable"
      rating_desc <- "Measurement system needs improvement"
    }

    list(
      analysis_type = "nested_gage_rr",
      n = length(measurements),
      n_parts = length(unique(parts)),
      n_operators = length(unique(operators)),
      variance_components = list(
        repeatability = list(variance = sigma2_error, sd = sd_repeatability),
        operator = list(variance = sigma2_operator, sd = sd_reproducibility),
        part_in_operator = list(variance = sigma2_part_in_op, sd = sqrt(sigma2_part_in_op)),
        grr = list(variance = sigma2_grr, sd = sd_grr),
        total = list(variance = sigma2_total, sd = sd_total)
      ),
      contribution = list(grr = round(pct_contrib_grr, 2), part_to_part = round(pct_contrib_part, 2)),
      study_variation = list(grr = round(pct_sv_grr, 2)),
      ndc = ndc,
      rating = rating,
      rating_desc = rating_desc,
      interpretation = sprintf("Gage R&R = %.1f%% of study variation. %s (ndc = %d)", pct_sv_grr, rating_desc, ndc)
    )

  } else if (analysis_type == "attribute") {
    # ============================================================
    # Attribute Agreement Analysis
    # ============================================================
    reference <- input$reference
    ratings <- input$ratings

    n_samples <- length(ratings)
    n_operators <- length(ratings[[1]])
    n_replicates <- length(ratings[[1]][[1]])

    operator_agreement <- numeric(n_operators)
    operator_kappa <- numeric(n_operators)

    for (op in 1:n_operators) {
      matches <- 0
      total <- 0
      for (s in 1:n_samples) {
        ref <- reference[s]
        for (r_idx in 1:n_replicates) {
          if (!is.na(ratings[[s]][[op]][r_idx])) {
            total <- total + 1
            if (ratings[[s]][[op]][r_idx] == ref) {
              matches <- matches + 1
            }
          }
        }
      }
      operator_agreement[op] <- (matches / total) * 100
      p_o <- matches / total
      p_e <- 0.5
      operator_kappa[op] <- (p_o - p_e) / (1 - p_e)
    }

    all_matches <- 0
    all_total <- 0
    for (s in 1:n_samples) {
      ref <- reference[s]
      for (op in 1:n_operators) {
        for (r_idx in 1:n_replicates) {
          if (!is.na(ratings[[s]][[op]][r_idx])) {
            all_total <- all_total + 1
            if (ratings[[s]][[op]][r_idx] == ref) {
              all_matches <- all_matches + 1
            }
          }
        }
      }
    }

    overall_agreement <- (all_matches / all_total) * 100
    overall_kappa <- (overall_agreement / 100 - 0.5) / (1 - 0.5)

    list(
      analysis_type = "attribute_agreement",
      n_samples = n_samples,
      n_operators = n_operators,
      n_replicates = n_replicates,
      overall = list(agreement_pct = round(overall_agreement, 2), kappa = round(overall_kappa, 3)),
      operators = lapply(1:n_operators, function(op) {
        list(name = paste0("Operator_", op), agreement_pct = round(operator_agreement[op], 2), kappa = round(operator_kappa[op], 3))
      }),
      interpretation = sprintf("Overall agreement = %.1f%%, Kappa = %.3f", overall_agreement, overall_kappa)
    )

  } else if (analysis_type == "bias") {
    # ============================================================
    # Bias Study
    # ============================================================
    measurements <- as.numeric(input$measurements)
    reference_value <- input$reference_value

    n <- length(measurements)
    mean_meas <- mean(measurements)
    sd_meas <- sd(measurements)
    bias <- mean_meas - reference_value
    bias_pct <- (bias / reference_value) * 100

    t_stat <- bias / (sd_meas / sqrt(n))
    p_value <- 2 * pt(-abs(t_stat), df = n - 1)

    list(
      analysis_type = "bias",
      n = n,
      reference_value = reference_value,
      mean = round(mean_meas, 4),
      sd = round(sd_meas, 4),
      bias = round(bias, 4),
      bias_pct = round(bias_pct, 2),
      t_statistic = round(t_stat, 4),
      p_value = round(p_value, 4),
      significant = p_value < 0.05,
      interpretation = ifelse(p_value < 0.05,
        sprintf("Significant bias detected (bias = %.4f, p = %.4f)", bias, p_value),
        sprintf("No significant bias detected (bias = %.4f, p = %.4f)", bias, p_value))
    )

  } else if (analysis_type == "linearity") {
    # ============================================================
    # Linearity Study
    # ============================================================
    reference_values <- as.numeric(input$reference_values)
    measurements <- as.numeric(input$measurements)

    model <- lm(measurements ~ reference_values)
    intercept <- coef(model)[1]
    slope <- coef(model)[2]
    bias <- measurements - reference_values
    linearity <- abs(slope - 1) * diff(range(reference_values))

    list(
      analysis_type = "linearity",
      n = length(measurements),
      intercept = round(intercept, 4),
      slope = round(slope, 4),
      r_squared = round(summary(model)$r.squared, 4),
      linearity = round(linearity, 4),
      bias_mean = round(mean(bias), 4),
      bias_sd = round(sd(bias), 4),
      reference_values = reference_values,
      biases = round(bias, 4),
      interpretation = sprintf("Slope = %.4f (ideal = 1.0), Intercept = %.4f (ideal = 0.0), Linearity = %.4f",
                               slope, intercept, linearity)
    )

  } else if (analysis_type == "stability") {
    # ============================================================
    # Stability Study
    # ============================================================
    measurements <- as.numeric(input$measurements)
    time_points <- input$time_points
    reference_value <- input$reference_value
    tolerance <- input$tolerance

    n <- length(measurements)
    mean_meas <- mean(measurements)
    sd_meas <- sd(measurements)

    ucl <- mean_meas + 3 * sd_meas
    lcl <- mean_meas - 3 * sd_meas
    ooc <- which(measurements > ucl | measurements < lcl)

    slope <- NA
    p_trend <- NA
    if (!is.null(time_points) && length(time_points) > 1) {
      time_numeric <- 1:n
      model <- lm(measurements ~ time_numeric)
      slope <- coef(model)[2]
      p_trend <- summary(model)$coefficients[2, 4]
    }

    if (!is.null(tolerance) && !is.na(tolerance) && tolerance > 0) {
      pct_tolerance <- (6 * sd_meas / tolerance) * 100
    } else {
      pct_tolerance <- NA
    }

    list(
      analysis_type = "stability",
      n = n,
      mean = round(mean_meas, 4),
      sd = round(sd_meas, 4),
      ucl = round(ucl, 4),
      lcl = round(lcl, 4),
      out_of_control = ooc,
      n_out_of_control = length(ooc),
      trend_slope = slope,
      trend_p_value = p_trend,
      trend_significant = !is.na(p_trend) && p_trend < 0.05,
      pct_tolerance = pct_tolerance,
      measurements = measurements,
      interpretation = ifelse(length(ooc) == 0,
        "Measurement system appears stable - no out-of-control points",
        sprintf("Measurement system may be unstable - %d out-of-control point(s) detected", length(ooc)))
    )

  } else {
    list(
      error = TRUE,
      message = paste("Unknown analysis_type:", analysis_type),
      supported_types = c("crossed", "nested", "attribute", "bias", "linearity", "stability")
    )
  }
}, error = function(e) {
  list(
    error = TRUE,
    message = conditionMessage(e),
    analysis_type = analysis_type
  )
})

# Output JSON
toJSON(result, auto_unbox = TRUE, pretty = TRUE)
