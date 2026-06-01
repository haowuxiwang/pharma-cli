# Design of Experiments R script
# Input: JSON with fields: doe_type (full_factorial, fractional_factorial, response_surface),
#        factors (list of factor definitions), responses (list of response values)
# Output: JSON to stdout

library(jsonlite)

input <- fromJSON(file("stdin"), simplifyVector = FALSE, simplifyDataFrame = FALSE)
doe_type <- ifelse(is.null(input$doe_type), "full_factorial", input$doe_type)

if (doe_type == "full_factorial") {
  factors <- input$factors
  if (is.null(factors)) stop("factors required for full factorial design")

  n_factors <- length(factors)
  factor_names <- sapply(factors, function(f) f$name)
  n_levels <- sapply(factors, function(f) f$levels)

  # Generate full factorial design matrix
  design_matrix <- expand.grid(lapply(n_levels, function(n) 1:n))
  colnames(design_matrix) <- factor_names
  n_runs <- nrow(design_matrix)

  # If responses provided, analyze
  if (!is.null(input$responses)) {
    responses <- as.numeric(input$responses)
    if (length(responses) != n_runs) {
      stop(paste("Expected", n_runs, "responses, got", length(responses)))
    }

    # Create data frame for analysis
    df <- as.data.frame(design_matrix)
    df$response <- responses

    # Convert factors
    for (fn in factor_names) {
      df[[fn]] <- as.factor(df[[fn]])
    }

    # Fit model
    formula_str <- paste("response ~", paste(factor_names, collapse = "*"))
    model <- aov(as.formula(formula_str), data = df)
    summary_model <- summary(model)

    # Main effects
    main_effects <- list()
    for (fn in factor_names) {
      group_means <- tapply(df$response, df[[fn]], mean)
      main_effects[[fn]] <- list(
        means = round(as.numeric(group_means), 4),
        levels = names(group_means),
        effect = round(max(group_means) - min(group_means), 4)
      )
    }

    # ANOVA table
    anova_table <- as.data.frame(summary_model[[1]])
    anova_results <- list()
    for (i in 1:(nrow(anova_table) - 1)) {
      row_name <- rownames(anova_table)[i]
      f_val <- anova_table$`F value`[i]
      p_val <- anova_table$`Pr(>F)`[i]
      anova_results[[row_name]] <- list(
        df = anova_table$Df[i],
        ss = round(anova_table$`Sum Sq`[i], 4),
        ms = round(anova_table$`Mean Sq`[i], 4),
        f_stat = ifelse(is.na(f_val), NA, round(f_val, 4)),
        p_value = ifelse(is.na(p_val), NA, round(p_val, 4)),
        significant = !is.na(p_val) && p_val < 0.05
      )
    }

    result <- list(
      doe_type = "full_factorial",
      n_factors = n_factors,
      n_runs = n_runs,
      factors = factor_names,
      design_matrix = as.data.frame(design_matrix),
      responses = round(responses, 4),
      main_effects = main_effects,
      anova = anova_results,
      overall_mean = round(mean(responses), 4),
      interpretation = "Check ANOVA p-values for significant factors"
    )

  } else {
    # Just return the design
    result <- list(
      doe_type = "full_factorial",
      n_factors = n_factors,
      n_runs = n_runs,
      factors = factor_names,
      design_matrix = as.data.frame(design_matrix),
      interpretation = "Design matrix generated. Add responses to analyze."
    )
  }

} else if (doe_type == "fractional_factorial") {
  factors <- input$factors
  if (is.null(factors)) stop("factors required for fractional factorial design")

  n_factors <- length(factors)
  factor_names <- sapply(factors, function(f) f$name)

  # Generate 2^(n-k) fractional factorial
  base_factors <- floor(log2(n_factors)) + 1
  base_matrix <- expand.grid(replicate(base_factors, c(-1, 1), simplify = FALSE))

  # Add interaction columns for additional factors
  if (n_factors > base_factors) {
    for (i in (base_factors + 1):n_factors) {
      # Use interaction of first two columns
      base_matrix <- cbind(base_matrix, base_matrix[, 1] * base_matrix[, 2])
    }
  }

  design_matrix <- base_matrix[, 1:n_factors]
  colnames(design_matrix) <- factor_names
  design_matrix[design_matrix == -1] <- "Low"
  design_matrix[design_matrix == 1] <- "High"

  result <- list(
    doe_type = "fractional_factorial",
    n_factors = n_factors,
    n_runs = nrow(design_matrix),
    resolution = "III",
    factors = factor_names,
    design_matrix = as.data.frame(design_matrix),
    interpretation = "Fractional factorial design. Main effects may be confounded with 2-factor interactions."
  )

} else if (doe_type == "response_surface") {
  factors <- input$factors
  if (is.null(factors)) stop("factors required for response surface design")
  if (length(factors) < 2 || length(factors) > 6) stop("RSM requires 2-6 factors")

  n_factors <- length(factors)
  factor_names <- sapply(factors, function(f) f$name)

  # Central Composite Design
  # Factorial points
  factorial_points <- expand.grid(replicate(n_factors, c(-1, 1), simplify = FALSE))
  colnames(factorial_points) <- factor_names

  # Center points (5 replicates)
  center_points <- as.data.frame(matrix(0, nrow = 5, ncol = n_factors))
  colnames(center_points) <- factor_names

  # Axial (star) points
  alpha <- sqrt(n_factors)
  axial_points <- matrix(0, nrow = 2 * n_factors, ncol = n_factors)
  for (i in 1:n_factors) {
    axial_points[2*i-1, i] <- -alpha
    axial_points[2*i, i] <- alpha
  }
  axial_points <- as.data.frame(axial_points)
  colnames(axial_points) <- factor_names

  # Combine all points
  design_matrix <- rbind(factorial_points, center_points, axial_points)
  n_runs <- nrow(design_matrix)

  # If responses provided, fit quadratic model
  if (!is.null(input$responses)) {
    responses <- as.numeric(input$responses)
    if (length(responses) != n_runs) {
      stop(paste("Expected", n_runs, "responses, got", length(responses)))
    }

    df <- as.data.frame(design_matrix)
    df$response <- responses

    # Fit second-order model
    formula_terms <- c(factor_names,
      paste0("I(", factor_names, "^2)"),
      combn(factor_names, 2, function(x) paste(x, collapse = ":")))
    formula_str <- paste("response ~", paste(formula_terms, collapse = " + "))
    model <- lm(as.formula(formula_str), data = df)
    model_summary <- summary(model)

    # Stationary point
    # Find optimal settings (simplified)
    coef <- model_summary$coefficients

    result <- list(
      doe_type = "response_surface",
      n_factors = n_factors,
      n_runs = n_runs,
      design_type = "Central Composite Design (CCD)",
      alpha = round(alpha, 4),
      factors = factor_names,
      design_matrix = as.data.frame(design_matrix),
      responses = round(responses, 4),
      model = list(
        r_squared = round(model_summary$r.squared, 4),
        adj_r_squared = round(model_summary$adj.r.squared, 4),
        coefficients = round(model_summary$coefficients, 4)
      ),
      interpretation = paste("RSM model fitted. R-squared =", round(model_summary$r.squared, 4))
    )

  } else {
    result <- list(
      doe_type = "response_surface",
      n_factors = n_factors,
      n_runs = n_runs,
      design_type = "Central Composite Design (CCD)",
      alpha = round(alpha, 4),
      factors = factor_names,
      design_matrix = as.data.frame(design_matrix),
      interpretation = "CCD design generated. Add responses to fit model."
    )
  }

} else {
  stop(paste("Unknown DOE type:", doe_type))
}

cat(toJSON(result, auto_unbox = TRUE, pretty = TRUE))
