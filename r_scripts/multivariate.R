# Multivariate Analysis
# Input: JSON with analysis_type and data
# Output: JSON with multivariate results

library(jsonlite)

input <- fromJSON(readLines(file("stdin"), warn = FALSE))
analysis_type <- input$analysis_type

result <- tryCatch({
  if (analysis_type == "pca") {
    # ============================================================
    # Principal Component Analysis (PCA)
    # ============================================================
    # Input: data matrix (rows = observations, columns = variables)
    data_matrix <- as.matrix(input$data)
    n_vars <- ncol(data_matrix)
    n_obs <- nrow(data_matrix)

    # Standardize data
    data_scaled <- scale(data_matrix)

    # Perform PCA
    pca_result <- prcomp(data_scaled, center = TRUE, scale. = TRUE)

    # Variance explained
    var_explained <- pca_result$sdev^2
    total_var <- sum(var_explained)
    pct_var <- var_explained / total_var * 100
    cum_pct <- cumsum(pct_var)

    # Number of components to retain (Kaiser criterion: eigenvalue > 1)
    n_components <- sum(var_explained > 1)
    if (n_components < 1) n_components <- 1

    # Loadings (rotation matrix)
    loadings <- pca_result$rotation[, 1:n_components]

    # Scores
    scores <- pca_result$x[, 1:n_components]

    # Build eigenvalue table
    eigenvalues <- data.frame(
      component = paste0("PC", 1:n_vars),
      eigenvalue = round(var_explained, 4),
      pct_variance = round(pct_var, 2),
      cum_pct = round(cum_pct, 2)
    )

    # Build loadings table
    loadings_df <- as.data.frame(round(loadings, 4))
    loadings_df$variable <- rownames(loadings)

    # Build scores table (first 10 observations for preview)
    scores_df <- as.data.frame(round(scores, 4))
    scores_df$observation <- 1:n_obs

    list(
      analysis_type = "pca",
      n_observations = n_obs,
      n_variables = n_vars,
      n_components = n_components,
      eigenvalues = eigenvalues,
      loadings = loadings_df,
      scores_preview = head(scores_df, 10),
      scores_all = scores_df,
      interpretation = sprintf(
        "PCA: %d components retained (Kaiser criterion). PC1 explains %.1f%%, PC2 explains %.1f%% of variance",
        n_components, pct_var[1], pct_var[2]
      )
    )

  } else if (analysis_type == "cluster") {
    # ============================================================
    # Cluster Analysis
    # ============================================================
    data_matrix <- as.matrix(input$data)
    method <- ifelse(!is.null(input$method), input$method, "hierarchical")
    n_clusters <- ifelse(!is.null(input$n_clusters), input$n_clusters, 3)

    # Standardize data
    data_scaled <- scale(data_matrix)

    if (method == "hierarchical") {
      # Hierarchical clustering
      dist_matrix <- dist(data_scaled)
      hc <- hclust(dist_matrix, method = "ward.D2")

      # Cut tree into clusters
      clusters <- cutree(hc, k = n_clusters)

      # Cluster sizes
      cluster_sizes <- table(clusters)

      # Cluster centers
      cluster_centers <- aggregate(data_matrix, by = list(cluster = clusters), FUN = mean)

      # Cophenetic correlation
      cophenetic_corr <- cor(dist_matrix, cophenetic(hc))

      list(
        analysis_type = "cluster",
        method = "hierarchical",
        n_observations = nrow(data_matrix),
        n_variables = ncol(data_matrix),
        n_clusters = n_clusters,
        clusters = clusters,
        cluster_sizes = as.list(cluster_sizes),
        cluster_centers = cluster_centers,
        cophenetic_correlation = round(cophenetic_corr, 4),
        interpretation = sprintf(
          "Hierarchical clustering: %d clusters, cophenetic correlation = %.3f",
          n_clusters, cophenetic_corr
        )
      )

    } else if (method == "kmeans") {
      # K-means clustering
      set.seed(42)  # For reproducibility
      km <- kmeans(data_scaled, centers = n_clusters, nstart = 25)

      list(
        analysis_type = "cluster",
        method = "kmeans",
        n_observations = nrow(data_matrix),
        n_variables = ncol(data_matrix),
        n_clusters = n_clusters,
        clusters = km$cluster,
        cluster_sizes = as.list(km$size),
        cluster_centers = as.data.frame(round(km$centers, 4)),
        within_ss = round(km$withinss, 4),
        total_within_ss = round(km$tot.withinss, 4),
        between_ss = round(km$betweenss, 4),
        total_ss = round(km$totss, 4),
        pct_variance_explained = round(km$betweenss / km$totss * 100, 2),
        interpretation = sprintf(
          "K-means clustering: %d clusters, %.1f%% variance explained",
          n_clusters, km$betweenss / km$totss * 100
        )
      )

    } else {
      stop(paste("Unknown clustering method:", method))
    }

  } else if (analysis_type == "discriminant") {
    # ============================================================
    # Linear Discriminant Analysis (LDA)
    # ============================================================
    data_matrix <- as.matrix(input$data)
    groups <- as.factor(input$groups)

    n_obs <- nrow(data_matrix)
    n_vars <- ncol(data_matrix)
    n_groups <- length(unique(groups))

    if (n_groups < 2) {
      stop("Need at least 2 groups for discriminant analysis")
    }

    # Perform LDA using MASS package
    if (!requireNamespace("MASS", quietly = TRUE)) {
      stop("MASS package required for discriminant analysis. Install: install.packages('MASS')")
    }

    lda_result <- MASS::lda(data_matrix, grouping = groups)

    # Predictions
    predictions <- predict(lda_result, data_matrix)

    # Confusion matrix
    confusion <- table(Predicted = predictions$class, Actual = groups)

    # Classification accuracy
    accuracy <- sum(diag(confusion)) / sum(confusion) * 100

    # Discriminant scores
    scores <- as.data.frame(round(predictions$x, 4))
    scores$group <- as.character(groups)

    # Coefficients
    coefficients <- as.data.frame(round(lda_result$scaling, 4))
    coefficients$variable <- rownames(coefficients)

    # Prior probabilities
    priors <- as.list(round(lda_result$prior, 4))

    # Group means
    group_means <- as.data.frame(round(lda_result$means, 4))
    group_means$group <- rownames(group_means)

    list(
      analysis_type = "discriminant",
      n_observations = n_obs,
      n_variables = n_vars,
      n_groups = n_groups,
      groups = levels(groups),
      prior_probabilities = priors,
      coefficients = coefficients,
      group_means = group_means,
      confusion_matrix = confusion,
      accuracy = round(accuracy, 2),
      scores = scores,
      interpretation = sprintf(
        "LDA: %d groups, classification accuracy = %.1f%%",
        n_groups, accuracy
      )
    )

  } else if (analysis_type == "correlation_matrix") {
    # ============================================================
    # Correlation Matrix
    # ============================================================
    data_matrix <- as.matrix(input$data)
    method <- ifelse(!is.null(input$method), input$method, "pearson")

    # Calculate correlation matrix
    cor_matrix <- cor(data_matrix, method = method)

    # Round for output
    cor_matrix_rounded <- round(cor_matrix, 4)

    # Extract variable names
    var_names <- colnames(data_matrix)
    if (is.null(var_names)) {
      var_names <- paste0("V", 1:ncol(data_matrix))
    }

    # Build correlation table
    cor_table <- data.frame(
      var1 = character(),
      var2 = character(),
      correlation = numeric(),
      stringsAsFactors = FALSE
    )

    for (i in 1:(ncol(cor_matrix) - 1)) {
      for (j in (i + 1):ncol(cor_matrix)) {
        cor_table <- rbind(cor_table, data.frame(
          var1 = var_names[i],
          var2 = var_names[j],
          correlation = round(cor_matrix[i, j], 4),
          stringsAsFactors = FALSE
        ))
      }
    }

    # Significance testing
    n <- nrow(data_matrix)
    t_stats <- cor_matrix * sqrt((n - 2) / (1 - cor_matrix^2))
    p_values <- 2 * pt(-abs(t_stats), df = n - 2)
    p_values_rounded <- round(p_values, 4)

    list(
      analysis_type = "correlation_matrix",
      n_observations = n,
      n_variables = ncol(data_matrix),
      method = method,
      correlation_matrix = cor_matrix_rounded,
      correlation_table = cor_table,
      p_values = p_values_rounded,
      interpretation = sprintf(
        "Correlation matrix (%s): %d variables, %d pairs",
        method, ncol(data_matrix), nrow(cor_table)
      )
    )

  } else {
    list(
      error = TRUE,
      message = paste("Unknown analysis_type:", analysis_type),
      supported_types = c("pca", "cluster", "discriminant", "correlation_matrix")
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
