"""Measurement System Analysis (MSA) / Gage R&R command."""
import json
import click

from cli.r_engine import run_r_file
from cli.commands.utils import output


@click.command("gage-rr")
@click.argument("analysis_type", type=click.Choice([
    "crossed", "nested", "attribute", "bias", "linearity", "stability"
]))
@click.option("--measurements", "-m", multiple=True, type=float, help="Measurement values")
@click.option("--parts", "-p", multiple=True, help="Part identifiers")
@click.option("--operators", "-o", multiple=True, help="Operator identifiers")
@click.option("--file", "-f", "data_file", type=click.Path(exists=True), help="JSON file with MSA data")
@click.option("--tolerance", type=float, default=None, help="Tolerance (USL - LSL)")
@click.option("--reference-value", type=float, default=None, help="Reference value (for bias study)")
@click.option("--reference-values", multiple=True, type=float, help="Reference values (for linearity study)")
@click.option("--time-points", multiple=True, help="Time points (for stability study)")
@click.pass_context
def gage_rr(ctx, analysis_type, measurements, parts, operators, data_file,
            tolerance, reference_value, reference_values, time_points):
    """Measurement System Analysis (MSA) / Gage R&R.

    ANALYSIS_TYPE: crossed, nested, attribute, bias, linearity, stability

    Examples:

    \b
    # Crossed Gage R&R (data from file)
    stats-cli gage-rr crossed -f msa_data.json --tolerance 10.0

    \b
    # Bias study
    stats-cli gage-rr bias -m 10.1 -m 10.2 -m 10.3 --reference-value 10.0
    """
    if data_file:
        # Load from JSON file
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['analysis_type'] = analysis_type
    else:
        # Build data from CLI arguments
        data = {'analysis_type': analysis_type}

        if analysis_type == "crossed":
            if not measurements or not parts or not operators:
                raise click.UsageError("Crossed Gage R&R requires --measurements, --parts, and --operators")
            data['measurements'] = list(measurements)
            data['parts'] = list(parts)
            data['operators'] = list(operators)
            if tolerance:
                data['tolerance'] = tolerance

        elif analysis_type == "nested":
            if not measurements or not parts or not operators:
                raise click.UsageError("Nested Gage R&R requires --measurements, --parts, and --operators")
            data['measurements'] = list(measurements)
            data['parts'] = list(parts)
            data['operators'] = list(operators)
            if tolerance:
                data['tolerance'] = tolerance

        elif analysis_type == "attribute":
            raise click.UsageError(
                "Attribute agreement analysis requires a JSON file. "
                "Use --file with JSON containing 'reference' and 'ratings' fields."
            )

        elif analysis_type == "bias":
            if not measurements:
                raise click.UsageError("Bias study requires --measurements")
            if reference_value is None:
                raise click.UsageError("Bias study requires --reference-value")
            data['measurements'] = list(measurements)
            data['reference_value'] = reference_value

        elif analysis_type == "linearity":
            if not measurements or not reference_values:
                raise click.UsageError("Linearity study requires --measurements and --reference-values")
            if len(measurements) != len(reference_values):
                raise click.UsageError("Measurements and reference values must have same length")
            data['measurements'] = list(measurements)
            data['reference_values'] = list(reference_values)

        elif analysis_type == "stability":
            if not measurements:
                raise click.UsageError("Stability study requires --measurements")
            data['measurements'] = list(measurements)
            if time_points:
                data['time_points'] = list(time_points)
            if reference_value is not None:
                data['reference_value'] = reference_value
            if tolerance:
                data['tolerance'] = tolerance

    result = run_r_file("gage_rr.R", data)
    output(result)
