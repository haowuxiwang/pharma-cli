# Non-parametric tests R script
# Input: JSON with test_type and data
# Output: JSON to stdout

library(jsonlite)

input <- fromJSON(file("stdin"))
test_type <- "mann_whitney"
if (!is.null(input$test_type)) test_type <- input$test_type

result <- tryCatch({
  if (test_type == "mann_whitney") {
    # ============================================================
    # Mann-Whitney U test (Wilcoxon rank-sum test)
    # ============================================================
    if (is.null(input$x) || is.null(input$y)) stop("x and y required")
    x <- as.numeric(input$x)
    y <- as.numeric(input$y)
    result_test <- wilcox.test(x, y, exact = FALSE)

    list(
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
    # ============================================================
    # Kruskal-Wallis test
    # ============================================================
    if (is.null(input$groups)) stop("groups required")
    groups <- input$groups
    data_list <- list()
    group_names <- c()
    for (i in 1:length(groups)) {
      data_list[[i]] <- as.numeric(groups[[i]])
      group_names <- c(group_names, paste0("Group_", i))
    }
    names(data_list) <- group_names
    df <- data.frame(value = unlist(data_list), group = rep(group_names, sapply(data_list, length)))
    result_test <- kruskal.test(value ~ group, data = df)

    list(
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
    # ============================================================
    # Wilcoxon signed-rank test (paired)
    # ============================================================
    if (is.null(input$x) || is.null(input$y)) stop("x and y required")
    x <- as.numeric(input$x)
    y <- as.numeric(input$y)
    if (length(x) != length(y)) stop("x and y must have same length")
    result_test <- wilcox.test(x, y, paired = TRUE, exact = FALSE)

    list(
      test_type = "wilcoxon_signed_rank",
      n_pairs = length(x),
      statistic = round(as.numeric(result_test$statistic), 4),
      p_value = round(result_test$p.value, 4),
      significant = result_test$p.value < 0.05,
      interpretation = ifelse(result_test$p.value < 0.05,
        "Significant difference between pairs (p < 0.05)",
        "No significant difference between pairs (p >= 0.05)")
    )

  } else if (test_type == "chi_square") {
    # ============================================================
    # Chi-Square Test
    # ============================================================
    chi_type <- "goodness_of_fit"
    if (!is.null(input$chi_type)) chi_type <- input$chi_type

    if (chi_type == "goodness_of_fit") {
      # Chi-square goodness of fit test
      observed <- as.numeric(input$observed)
      expected <- input$expected

      if (is.null(expected)) {
        # Equal expected frequencies
        expected <- rep(sum(observed) / length(observed), length(observed))
      } else {
        expected <- as.numeric(expected)
      }

      result_test <- chisq.test(observed, p = expected / sum(expected))

      list(
        test_type = "chi_square",
        chi_type = "goodness_of_fit",
        n_categories = length(observed),
        observed = observed,
        expected = round(expected, 4),
        statistic = round(result_test$statistic, 4),
        df = result_test$parameter,
        p_value = round(result_test$p.value, 4),
        significant = result_test$p.value < 0.05,
        interpretation = ifelse(result_test$p.value < 0.05,
          "Significant deviation from expected distribution (p < 0.05)",
          "No significant deviation from expected distribution (p >= 0.05)")
      )

    } else if (chi_type == "independence") {
      # Chi-square test of independence
      observed <- as.matrix(input$observed)

      result_test <- chisq.test(observed)

      # Cramér's V
      n <- sum(observed)
      k <- min(nrow(observed), ncol(observed))
      v <- sqrt(result_test$statistic / (n * (k - 1)))

      list(
        test_type = "chi_square",
        chi_type = "independence",
        n_rows = nrow(observed),
        n_cols = ncol(observed),
        observed = observed,
        expected = round(result_test$expected, 4),
        statistic = round(result_test$statistic, 4),
        df = result_test$parameter,
        p_value = round(result_test$p.value, 4),
        cramers_v = round(v, 4),
        significant = result_test$p.value < 0.05,
        interpretation = sprintf("Chi-square = %.2f, df = %d, p = %.4f, Cramer's V = %.3f (%s)",
                                 result_test$statistic, result_test$parameter, result_test$p.value, v,
                                 ifelse(result_test$p.value < 0.05, "significant association", "no significant association"))
      )
    } else {
      stop(paste("Unknown chi_square type:", chi_type))
    }

  } else if (test_type == "friedman") {
    # ============================================================
    # Friedman Test
    # ============================================================
    if (is.null(input$groups)) stop("groups required")
    groups <- input$groups

    # Convert to matrix
    data_matrix <- do.call(rbind, lapply(groups, as.numeric))
    result_test <- friedman.test(data_matrix)

    list(
      test_type = "friedman",
      n_groups = length(groups),
      n_observations = ncol(data_matrix),
      statistic = round(result_test$statistic, 4),
      df = result_test$parameter,
      p_value = round(result_test$p.value, 4),
      significant = result_test$p.value < 0.05,
      interpretation = ifelse(result_test$p.value < 0.05,
        "Significant difference between groups (p < 0.05)",
        "No significant difference between groups (p >= 0.05)")
    )

  } else {
    list(error = TRUE, message = paste("Unknown test type:", test_type),
         supported_types = c("mann_whitney", "kruskal_wallis", "wilcoxon", "chi_square", "friedman"))
  }
}, error = function(e) {
  list(error = TRUE, message = conditionMessage(e), test_type = test_type)
})

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
