# Multiple comparison tests R script
# Input: JSON with fields: test_type, groups, alpha (optional)
# Output: JSON to stdout

library(jsonlite)

input <- fromJSON(file("stdin"), simplifyVector = FALSE, simplifyDataFrame = FALSE)
test_type <- ifelse(is.null(input$test_type), "tukey", input$test_type)
alpha <- ifelse(is.null(input$alpha), 0.05, input$alpha)

if (test_type == "tukey") {
  # Tukey HSD (Honest Significant Difference) test
  if (is.null(input$groups)) {
    stop("groups required for Tukey HSD test")
  }
  groups <- input$groups

  # Convert to list of numeric vectors
  data_list <- list()
  group_names <- c()
  for (i in 1:length(groups)) {
    data_list[[i]] <- as.numeric(groups[[i]])
    group_names <- c(group_names, paste0("Group_", i))
  }
  names(data_list) <- group_names

  # Create data frame
  df <- data.frame(
    value = unlist(data_list),
    group = rep(group_names, sapply(data_list, length))
  )

  # Perform ANOVA first
  anova_result <- aov(value ~ factor(group), data = df)

  # Tukey HSD test
  tukey_result <- TukeyHSD(anova_result)

  # Extract pairwise comparisons
  comparisons <- tukey_result$`factor(group)`
  pairwise_results <- list()

  for (i in 1:nrow(comparisons)) {
    row_name <- rownames(comparisons)[i]
    parts <- strsplit(row_name, "-")[[1]]
    pairwise_results[[row_name]] <- list(
      group1 = parts[1],
      group2 = parts[2],
      difference = round(comparisons[i, "diff"], 4),
      ci_lower = round(comparisons[i, "lwr"], 4),
      ci_upper = round(comparisons[i, "upr"], 4),
      p_value = round(comparisons[i, "p adj"], 4),
      significant = comparisons[i, "p adj"] < alpha
    )
  }

  output <- list(
    test_type = "tukey",
    n_groups = length(groups),
    group_sizes = sapply(data_list, length),
    alpha = alpha,
    pairwise_comparisons = pairwise_results,
    interpretation = paste("Tukey HSD test completed with", length(pairwise_results), "pairwise comparisons")
  )

} else if (test_type == "bonferroni") {
  # Bonferroni correction for multiple comparisons
  if (is.null(input$groups)) {
    stop("groups required for Bonferroni test")
  }
  groups <- input$groups

  # Convert to list of numeric vectors
  data_list <- list()
  group_names <- c()
  for (i in 1:length(groups)) {
    data_list[[i]] <- as.numeric(groups[[i]])
    group_names <- c(group_names, paste0("Group_", i))
  }
  names(data_list) <- group_names

  # Create data frame
  df <- data.frame(
    value = unlist(data_list),
    group = rep(group_names, sapply(data_list, length))
  )

  # Perform pairwise t-tests with Bonferroni correction
  n_groups <- length(groups)
  n_comparisons <- n_groups * (n_groups - 1) / 2
  adjusted_alpha <- alpha / n_comparisons

  pairwise_results <- list()
  comparison_count <- 0

  for (i in 1:(n_groups - 1)) {
    for (j in (i + 1):n_groups) {
      comparison_count <- comparison_count + 1
      group1_name <- group_names[i]
      group2_name <- group_names[j]

      t_test <- t.test(data_list[[i]], data_list[[j]])
      p_adjusted <- min(1, t_test$p.value * n_comparisons)

      comparison_name <- paste0(group1_name, "-", group2_name)
      pairwise_results[[comparison_name]] <- list(
        group1 = group1_name,
        group2 = group2_name,
        t_statistic = round(t_test$statistic, 4),
        p_value = round(t_test$p.value, 4),
        p_adjusted = round(p_adjusted, 4),
        significant = p_adjusted < alpha
      )
    }
  }

  output <- list(
    test_type = "bonferroni",
    n_groups = n_groups,
    group_sizes = sapply(data_list, length),
    alpha = alpha,
    n_comparisons = n_comparisons,
    adjusted_alpha = round(adjusted_alpha, 4),
    pairwise_comparisons = pairwise_results,
    interpretation = paste("Bonferroni correction applied with", n_comparisons, "comparisons")
  )

} else if (test_type == "scheffe") {
  # Scheffe's test for multiple comparisons
  if (is.null(input$groups)) {
    stop("groups required for Scheffe's test")
  }
  groups <- input$groups

  # Convert to list of numeric vectors
  data_list <- list()
  group_names <- c()
  for (i in 1:length(groups)) {
    data_list[[i]] <- as.numeric(groups[[i]])
    group_names <- c(group_names, paste0("Group_", i))
  }
  names(data_list) <- group_names

  # Create data frame
  df <- data.frame(
    value = unlist(data_list),
    group = rep(group_names, sapply(data_list, length))
  )

  # Perform ANOVA
  anova_result <- aov(value ~ factor(group), data = df)
  anova_summary <- summary(anova_result)

  # Extract ANOVA components
  mse <- anova_summary[[1]]$`Mean Sq`[2]
  df_error <- anova_summary[[1]]$Df[2]
  n_groups <- length(groups)

  # Scheffe critical value
  f_crit <- qf(1 - alpha, n_groups - 1, df_error)
  scheffe_crit <- sqrt((n_groups - 1) * f_crit)

  pairwise_results <- list()

  for (i in 1:(n_groups - 1)) {
    for (j in (i + 1):n_groups) {
      group1_name <- group_names[i]
      group2_name <- group_names[j]

      mean_diff <- mean(data_list[[i]]) - mean(data_list[[j]])
      n1 <- length(data_list[[i]])
      n2 <- length(data_list[[j]])
      se_diff <- sqrt(mse * (1/n1 + 1/n2))

      scheffe_stat <- abs(mean_diff) / se_diff
      significant <- scheffe_stat > scheffe_crit

      comparison_name <- paste0(group1_name, "-", group2_name)
      pairwise_results[[comparison_name]] <- list(
        group1 = group1_name,
        group2 = group2_name,
        mean_difference = round(mean_diff, 4),
        scheffe_statistic = round(scheffe_stat, 4),
        critical_value = round(scheffe_crit, 4),
        significant = significant
      )
    }
  }

  output <- list(
    test_type = "scheffe",
    n_groups = n_groups,
    group_sizes = sapply(data_list, length),
    alpha = alpha,
    mse = round(mse, 4),
    df_error = df_error,
    f_critical = round(f_crit, 4),
    scheffe_critical = round(scheffe_crit, 4),
    pairwise_comparisons = pairwise_results,
    interpretation = paste("Scheffe's test completed with", length(pairwise_results), "pairwise comparisons")
  )

} else {
  stop(paste("Unknown test type:", test_type))
}

cat(toJSON(output, auto_unbox = TRUE, pretty = TRUE))
