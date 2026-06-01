# Non-parametric tests R script
# Input: JSON with fields: test_type, x, y (for mann_whitney, wilcoxon), groups (for kruskal_wallis)
# Output: JSON to stdout

library(jsonlite)

input <- fromJSON(file("stdin"))
test_type <- ifelse(is.null(input$test_type), "mann_whitney", input$test_type)

if (test_type == "mann_whitney") {
  # Mann-Whitney U test (Wilcoxon rank-sum test)
  if (is.null(input$x) || is.null(input$y)) {
    stop("x and y required for Mann-Whitney test")
  }
  x <- as.numeric(input$x)
  y <- as.numeric(input$y)

  result_test <- wilcox.test(x, y, exact = FALSE)

  output <- list(
    test_type = "mann_whitney",
    n_x = length(x),
    n_y = length(y),
    statistic = round(as.numeric(result_test$statistic), 4),
    p_value = round(result_test$p.value, 4),
    significant = result_test$p.value < 0.05,
    interpretation = ifelse(result_test$p.value < 0.05,
      "Significant difference between groups (p < 0.05)",
      "No significant difference between groups (p >= 0.05)")
  )

} else if (test_type == "kruskal_wallis") {
  # Kruskal-Wallis test
  if (is.null(input$groups)) {
    stop("groups required for Kruskal-Wallis test")
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

  # Create data frame for kruskal.test
  df <- data.frame(
    value = unlist(data_list),
    group = rep(group_names, sapply(data_list, length))
  )

  result_test <- kruskal.test(value ~ group, data = df)

  output <- list(
    test_type = "kruskal_wallis",
    n_groups = length(groups),
    group_sizes = sapply(data_list, length),
    statistic = round(as.numeric(result_test$statistic), 4),
    df = result_test$parameter,
    p_value = round(result_test$p.value, 4),
    significant = result_test$p.value < 0.05,
    interpretation = ifelse(result_test$p.value < 0.05,
      "Significant difference between groups (p < 0.05)",
      "No significant difference between groups (p >= 0.05)")
  )

} else if (test_type == "wilcoxon") {
  # Wilcoxon signed-rank test (paired)
  if (is.null(input$x) || is.null(input$y)) {
    stop("x and y required for Wilcoxon signed-rank test")
  }
  x <- as.numeric(input$x)
  y <- as.numeric(input$y)

  if (length(x) != length(y)) {
    stop("x and y must have same length for paired test")
  }

  result_test <- wilcox.test(x, y, paired = TRUE, exact = FALSE)

  output <- list(
    test_type = "wilcoxon_signed_rank",
    n_pairs = length(x),
    statistic = round(as.numeric(result_test$statistic), 4),
    p_value = round(result_test$p.value, 4),
    significant = result_test$p.value < 0.05,
    interpretation = ifelse(result_test$p.value < 0.05,
      "Significant difference between pairs (p < 0.05)",
      "No significant difference between pairs (p >= 0.05)")
  )

} else {
  stop(paste("Unknown test type:", test_type))
}

cat(toJSON(output, auto_unbox = TRUE, pretty = TRUE))
