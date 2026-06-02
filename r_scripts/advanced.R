# Advanced Statistical Methods
# Input: JSON with analysis_type and data
# Output: JSON with results

library(jsonlite)

input <- fromJSON(readLines(file("stdin"), warn = FALSE))
analysis_type <- input$analysis_type

result <- tryCatch({
  if (analysis_type == "mixed_effects") {
    # ============================================================
    # Mixed Effects Model (Linear Mixed Model)
    # ============================================================
    data_df <- as.data.frame(input$data)
    response <- input$response
    fixed_effects <- input$fixed_effects
    random_effects <- input$random_effects

    # Build formula
    fixed_formula <- paste(response, "~", paste(fixed_effects, collapse = " + "))
    random_formula <- paste("~", paste(random_effects, collapse = " + "))

    # Fit model using lme4
    if (!requireNamespace("lme4", quietly = TRUE)) {
      stop("lme4 package required. Install: install.packages('lme4')")
    }

    full_formula <- paste(fixed_formula, "+ (1|", paste(random_effects, collapse = "/"), ")")
    model <- lmer(as.formula(full_formula), data = data_df)

    # Model summary
    model_summary <- summary(model)

    # Fixed effects
    fixed_table <- model_summary$coefficients
    fixed_results <- list()
    for (i in 1:nrow(fixed_table)) {
      fixed_results[[rownames(fixed_table)[i]]] <- list(
        estimate = round(fixed_table[i, "Estimate"], 6),
        std_error = round(fixed_table[i, "Std. Error"], 4),
        t_value = round(fixed_table[i, "t value"], 4)
      )
    }

    # Random effects
    ranef_summary <- VarCorr(model)
    random_results <- list()
    for (i in 1:nrow(ranef_summary)) {
      grp <- attr(ranef_summary, "cnms")[[i]]
      random_results[[names(attr(ranef_summary, "cnms"))[i]]] <- list(
        variance = round(as.numeric(ranef_summary[i, "Vcor"]), 6),
        std_dev = round(sqrt(as.numeric(ranef_summary[i, "Vcor"])), 6)
      )
    }

    # Model fit statistics
    aic_val <- AIC(model)
    bic_val <- BIC(model)
    loglik <- logLik(model)

    # Confidence intervals for fixed effects
    ci <- confint(model, parm = "beta_", method = "Wald")

    list(
      analysis_type = "mixed_effects",
      n = nrow(data_df),
      formula = full_formula,
      fixed_effects = fixed_results,
      random_effects = random_results,
      residual_variance = round(sigma(model)^2, 6),
      aic = round(aic_val, 2),
      bic = round(bic_val, 2),
      log_likelihood = round(as.numeric(loglik), 2),
      interpretation = sprintf("Mixed effects model: AIC=%.1f, BIC=%.1f", aic_val, bic_val)
    )

  } else if (analysis_type == "cox_regression") {
    # ============================================================
# Cox Proportional Hazards Regression
    # ============================================================
    if (!requireNamespace("survival", quietly = TRUE)) {
      stop("survival package required. Install: install.packages('survival')")
    }

    data_df <- as.data.frame(input$data)
    time_col <- input$time_column
    status_col <- input$status_column
    covariates <- input$covariates

    # Create survival object
    surv_obj <- Surv(data_df[[time_col]], data_df[[status_col]])

    # Build formula
    formula_str <- paste("surv_obj ~", paste(covariates, collapse = " + "))

    # Fit Cox model
    model <- coxph(as.formula(formula_str), data = data_df)

    # Model summary
    model_summary <- summary(model)

    # Coefficients
    coef_table <- model_summary$coefficients
    coef_results <- list()
    for (i in 1:nrow(coef_table)) {
      coef_results[[rownames(coef_table)[i]]] <- list(
        coefficient = round(coef_table[i, "coef"], 6),
        hazard_ratio = round(exp(coef_table[i, "coef"]), 4),
        std_error = round(coef_table[i, "se(coef)"], 4),
        z_value = round(coef_table[i, "z"], 4),
        p_value = round(coef_table[i, "Pr(>|z|)"], 4)
      )
    }

    # Concordance
    concordance <- model_summary$concordance

    # Likelihood ratio test
    lrt <- model_summary$logtest

    list(
      analysis_type = "cox_regression",
      n = model_summary$n,
      n_events = model_summary$nevent,
      formula = formula_str,
      coefficients = coef_results,
      concordance = list(
        index = round(concordance["C"], 4),
        se = round(concordance["se(C)"], 4)
      ),
      likelihood_ratio_test = list(
        statistic = round(lrt["test"], 4),
        df = lrt["df"],
        p_value = round(lrt["pvalue"], 4)
      ),
      aic = round(AIC(model), 2),
      interpretation = sprintf("Cox regression: %d events, concordance=%.3f, LR test p=%.4f",
                               model_summary$nevent, concordance["C"], lrt["pvalue"])
    )

  } else if (analysis_type == "exact_test") {
    # ============================================================
    # Fisher's Exact Test
    # ============================================================
    observed <- as.matrix(input$observed)

    # Fisher's exact test
    fisher_result <- fisher.test(observed)

    # Chi-square test for comparison
    chisq_result <- chisq.test(observed)

    list(
      analysis_type = "exact_test",
      observed = observed,
      fisher = list(
        p_value = round(fisher_result$p.value, 6),
        odds_ratio = round(fisher_result$estimate, 4),
        ci_lower = round(fisher_result$conf.int[1], 4),
        ci_upper = round(fisher_result$conf.int[2], 4)
      ),
      chi_square = list(
        statistic = round(chisq_result$statistic, 4),
        p_value = round(chisq_result$p.value, 6)
      ),
      interpretation = sprintf("Fisher's exact test: p=%.6f, OR=%.2f (95%% CI: %.2f-%.2f)",
                               fisher_result$p.value, fisher_result$estimate,
                               fisher_result$conf.int[1], fisher_result$conf.int[2])
    )

  } else if (analysis_type == "friedman") {
    # ============================================================
    # Friedman Test (Non-parametric repeated measures)
    # ============================================================
    groups <- input$groups
    data_matrix <- do.call(rbind, lapply(groups, as.numeric))

    friedman_result <- friedman.test(data_matrix)

    list(
      analysis_type = "friedman",
      n_groups = length(groups),
      n_observations = ncol(data_matrix),
      statistic = round(friedman_result$statistic, 4),
      df = friedman_result$parameter,
      p_value = round(friedman_result$p.value, 4),
      significant = friedman_result$p.value < 0.05,
      interpretation = ifelse(friedman_result$p.value < 0.05,
        "Significant difference between groups (p < 0.05)",
        "No significant difference between groups (p >= 0.05)")
    )

  } else if (analysis_type == "mcnemar") {
    # ============================================================
    # McNemar's Test (Paired proportions)
    # ============================================================
    observed <- as.matrix(input$observed)

    mcnemar_result <- mcnemar.test(observed)

    list(
      analysis_type = "mcnemar",
      observed = observed,
      statistic = round(mcnemar_result$statistic, 4),
      df = mcnemar_result$parameter,
      p_value = round(mcnemar_result$p.value, 4),
      significant = mcnemar_result$p.value < 0.05,
      interpretation = ifelse(mcnemar_result$p.value < 0.05,
        "Significant change (p < 0.05)",
        "No significant change (p >= 0.05)")
    )

  } else if (analysis_type == "cochran_q") {
    # ============================================================
    # Cochran's Q Test (Multiple paired proportions)
    # ============================================================
    data_matrix <- as.matrix(input$data)

    # Manual Cochran's Q calculation
    k <- ncol(data_matrix)
    n <- nrow(data_matrix)

    row_sums <- rowSums(data_matrix)
    col_sums <- colSums(data_matrix)
    total <- sum(data_matrix)

    numerator <- k * (k - 1) * sum((col_sums - total/k)^2)
    denominator <- k * total - sum(row_sums^2)

    Q <- numerator / denominator
    df <- k - 1
    p_value <- 1 - pchisq(Q, df)

    list(
      analysis_type = "cochran_q",
      n_subjects = n,
      n_conditions = k,
      statistic = round(Q, 4),
      df = df,
      p_value = round(p_value, 4),
      significant = p_value < 0.05,
      condition_proportions = round(col_sums / n, 4),
      interpretation = ifelse(p_value < 0.05,
        "Significant difference between conditions (p < 0.05)",
        "No significant difference between conditions (p >= 0.05)")
    )

  } else {
    list(
      error = TRUE,
      message = paste("Unknown analysis_type:", analysis_type),
      supported_types = c("mixed_effects", "cox_regression", "exact_test", "friedman", "mcnemar", "cochran_q")
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
