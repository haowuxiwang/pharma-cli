# ANOVA R script
# Input: JSON with fields: anova_type (one_way, two_way), data, response, factor1, factor2 (for two_way)
# data is a list of groups (one_way) or a data frame (two_way)
# Output: JSON to stdout

library(jsonlite)

input <- fromJSON(file("stdin"))
anova_type <- ifelse(is.null(input$anova_type), "one_way", input$anova_type)

if (anova_type == "one_way") {
  groups <- input$groups
  if (is.null(groups)) stop("groups required for one-way ANOVA")

  # Convert matrix to list of vectors (each column is a group)
  if (is.matrix(groups)) {
    group_list <- lapply(1:ncol(groups), function(i) groups[, i])
  } else {
    group_list <- groups
  }

  # Create data frame from groups
  df <- data.frame(
    value = unlist(group_list),
    group = rep(paste0("G", 1:length(group_list)), sapply(group_list, length))
  )
  df$group <- as.factor(df$group)

  # One-way ANOVA
  aov_result <- aov(value ~ group, data = df)
  summary_aov <- summary(aov_result)

  # Extract SS, df, MS, F, p
  anova_table <- as.data.frame(summary_aov[[1]])
  ss_between <- anova_table$`Sum Sq`[1]
  ss_within <- anova_table$`Sum Sq`[2]
  ss_total <- ss_between + ss_within
  df_between <- anova_table$Df[1]
  df_within <- anova_table$Df[2]
  ms_between <- anova_table$`Mean Sq`[1]
  ms_within <- anova_table$`Mean Sq`[2]
  f_stat <- anova_table$`F value`[1]
  p_value <- anova_table$`Pr(>F)`[1]

  # Effect size (eta-squared)
  eta_sq <- ss_between / ss_total

  # Post-hoc Tukey HSD if significant
  post_hoc <- NULL
  if (!is.na(p_value) && p_value < 0.05) {
    tukey <- TukeyHSD(aov_result)
    tukey_df <- as.data.frame(tukey[[1]])
    post_hoc <- list()
    for (i in 1:nrow(tukey_df)) {
      row <- tukey_df[i, ]
      pair_name <- rownames(tukey_df)[i]
      post_hoc[[pair_name]] <- list(
        difference = round(row$diff, 4),
        ci_lower = round(row$`lwr`, 4),
        ci_upper = round(row$`upr`, 4),
        p_adjusted = round(row$`p adj`, 4),
        significant = row$`p adj` < 0.05
      )
    }
  }

  # Group statistics
  group_stats <- list()
  for (g in unique(df$group)) {
    vals <- df$value[df$group == g]
    group_stats[[g]] <- list(
      n = length(vals),
      mean = round(mean(vals), 4),
      sd = round(sd(vals), 4),
      se = round(sd(vals) / sqrt(length(vals)), 4)
    )
  }

  result <- list(
    anova_type = "one_way",
    ss_between = round(ss_between, 4),
    ss_within = round(ss_within, 4),
    ss_total = round(ss_total, 4),
    df_between = df_between,
    df_within = df_within,
    ms_between = round(ms_between, 4),
    ms_within = round(ms_within, 4),
    f_statistic = round(f_stat, 4),
    p_value = round(p_value, 4),
    eta_squared = round(eta_sq, 4),
    significant = !is.na(p_value) && p_value < 0.05,
    group_stats = group_stats,
    post_hoc_tukey = post_hoc,
    interpretation = ifelse(!is.na(p_value) && p_value < 0.05,
      "Significant difference between groups (p < 0.05)",
      "No significant difference between groups (p >= 0.05)"
    )
  )

} else if (anova_type == "two_way") {
  df_data <- input$data
  if (is.null(df_data)) stop("data (data frame) required for two-way ANOVA")

  df <- as.data.frame(df_data)
  response <- input$response
  factor1 <- input$factor1
  factor2 <- input$factor2

  if (is.null(response) || is.null(factor1) || is.null(factor2)) {
    stop("response, factor1, and factor2 required for two-way ANOVA")
  }

  df[[factor1]] <- as.factor(df[[factor1]])
  df[[factor2]] <- as.factor(df[[factor2]])

  # Two-way ANOVA with interaction
  formula_str <- paste(response, "~", factor1, "*", factor2)
  aov_result <- aov(as.formula(formula_str), data = df)
  summary_aov <- summary(aov_result)

  # Extract ANOVA table
  anova_table <- as.data.frame(summary_aov[[1]])
  anova_entries <- list()
  for (i in 1:nrow(anova_table)) {
    row_name <- rownames(anova_table)[i]
    if (row_name != "Residuals") {
      anova_entries[[row_name]] <- list(
        df = anova_table$Df[i],
        ss = round(anova_table$`Sum Sq`[i], 4),
        ms = round(anova_table$`Mean Sq`[i], 4),
        f_stat = round(anova_table$`F value`[i], 4),
        p_value = round(anova_table$`Pr(>F)`[i], 4),
        significant = !is.na(anova_table$`Pr(>F)`[i]) && anova_table$`Pr(>F)`[i] < 0.05
      )
    }
  }

  residual <- list(
    df = anova_table$Df[nrow(anova_table)],
    ss = round(anova_table$`Sum Sq`[nrow(anova_table)], 4),
    ms = round(anova_table$`Mean Sq`[nrow(anova_table)], 4)
  )

  result <- list(
    anova_type = "two_way",
    response = response,
    factor1 = factor1,
    factor2 = factor2,
    anova_table = anova_entries,
    residual = residual,
    interpretation = "Check individual factor and interaction p-values"
  )

} else {
  stop(paste("Unknown ANOVA type:", anova_type))
}

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
