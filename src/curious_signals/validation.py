"""Complete non-mutating validation of protocol, core XML, and astronomy assets."""

from __future__ import annotations

from . import ToolError
from .checkout import Checkout
from .generation import (
    find_xmllint,
    render_core_experiments,
    run_xmllint,
    source_inventory_errors,
    xml_safety_errors,
)
from .phyphox_xml import check_astronomy_experiment, check_core_experiment
from .protocol import contract_errors, parse_protocol, read_contract


def validate(checkout: Checkout) -> list[str]:
    """Run the local contract, XML safety, core, astronomy, and rendering checks."""

    try:
        raw = read_contract(checkout.contract)
    except ToolError as error:
        return [str(error)]
    sources = checkout.core_sources()
    includes = checkout.includes()
    generated = checkout.generated_experiments()
    astronomy = checkout.astronomy_experiments()
    errors = contract_errors(raw)
    protocol = None if errors else parse_protocol(raw)
    if protocol is not None:
        errors.extend(source_inventory_errors(checkout, protocol))
    errors.extend(
        xml_safety_errors([*sources, *includes, *generated, *astronomy], checkout.include_dir)
    )
    if errors or protocol is None:
        return errors
    if not generated:
        errors.append(f"No generated experiments found at {checkout.experiments_dir}/*.phyphox.")
    if {path.name for path in generated} != set(protocol.experiments):
        errors.append(
            f"{checkout.experiments_dir}: generated filenames do not match protocol contract"
        )
    for path in generated:
        mode = protocol.mode_for_experiment(path.name)
        errors.extend(
            check_core_experiment(
                path, protocol, expected_mode=mode.id if mode is not None else None
            )
        )
    for path in astronomy:
        errors.extend(check_astronomy_experiment(path))
    if errors:
        return errors
    try:
        xmllint = find_xmllint()
    except ToolError as error:
        return [str(error)]
    for path in [*includes, *sources, *generated, *astronomy]:
        try:
            run_xmllint([xmllint, "--noout", str(path)])
        except ToolError as error:
            errors.append(str(error))
    try:
        render_core_experiments(checkout, protocol)
    except ToolError as error:
        errors.append(str(error))
    return errors
