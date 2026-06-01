# Homogeneity of variance tests R script
# Input: JSON with fields: test_type, groups
# Output: JSON to stdout

library(jsonlite)

input <- fromJSON(file("stdin"), simplifyVector = FALSE, simplifyDataFrame = FALSE)
test_type <- ifelse(is.null(input$test_type), "levene", input$test_type)

if (test_type == "levene") {
  # Levene's test for homogeneity of variance
  if (is.null(input$groups)) {
    stop("groups required for Levene's test")
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

  # Levene's test (using car package if available, otherwise manual implementation)
  tryCatch({
    library(car)
    result_test <- leveneTest(value ~ factor(group), data = df)
    f_stat <- result_test$`F value`[1]
    p_value <- result_test$`Pr(>F)`[1]
  }, error = function(e) {
    # Manual implementation of Levene's test
    # Calculate group medians
    group_medians <- tapply(df$value, df$group, median)

    # Calculate absolute deviations from group medians
    abs_dev <- abs(df$value - group_medians[df$group])

    # Perform ANOVA on absolute deviations
    anova_result <- aov(abs_dev ~ factor(df$group))
    anova_summary <- summary(anova_result)

    f_stat <<- anova_summary[[1]]$`F value`[1]
    p_value <<- anova_summary[[1]]$`Pr(>F)`[1]
  })

  output <- list(
    test_type = "levene",
    n_groups = length(groups),
    group_sizes = sapply(data_list, length),
    f_statistic = round(as.numeric(f_stat), 4),
    p_value = round(as.numeric(p_value), 4),
    significant = as.numeric(p_value) < 0.05,
    interpretation = ifelse(as.numeric(p_value) < 0.05,
      "Variances are significantly different (p < 0.05)",
      "No significant difference in variances (p >= 0.05)")
  )

} else if (test_type == "bartlett") {
  # Bartlett's test for homogeneity of variance
  if (is.null(input$groups)) {
    stop("groups required for Bartlett's test")
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

  # Bartlett's test
  result_test <- bartlett.test(value ~ group, data = df)

  output <- list(
    test_type = "bartlett",
    n_groups = length(groups),
    group_sizes = sapply(data_list, length),
    statistic = round(as.numeric(result_test$statistic), 4),
    p_value = round(result_test$p.value, 4),
    significant = result_test$p.value < 0.05,
    interpretation = ifelse(result_test$p.value < 0.05,
      "Variances are significantly different (p < 0.05)",
      "No significant difference in variances (p >= 0.05)")
  )

} else {
  stop(paste("Unknown test type:", test_type))
}

cat(toJSON(output, auto_unbox = TRUE, pretty = TRUE))
