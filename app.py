import pandas as pd
import streamlit as st

from app.costing import calculate_costs, calculate_variance
from app.document_processing import read_text_file
from app.jobs import (
    get_blueprint_job,
    mark_blueprint_job_complete,
    mark_blueprint_job_failed,
    submit_blueprint_job,
)
from app.logs import aggregate_actuals, parse_site_log
from app.models import PriceEntry, ProjectState
from app.reporting import costs_dataframe, excel_report, json_report, takeoff_dataframe, variance_dataframe
from app.takeoff import calculate_takeoff, default_rules


st.set_page_config(page_title="ConstructIQ", page_icon="C", layout="wide")


def initialize_state() -> None:
    if "project" not in st.session_state:
        st.session_state.project = ProjectState()
    if "prices" not in st.session_state:
        st.session_state.prices = {
            "blocks": PriceEntry(material="blocks", unit="pcs", unit_price=750),
            "cement": PriceEntry(material="cement", unit="bag", unit_price=12000),
            "sand": PriceEntry(material="sand", unit="m3", unit_price=85000),
            "tiles": PriceEntry(material="tiles", unit="m2", unit_price=8500),
        }


def start_blueprint_processing(filename: str, content: bytes) -> None:
    st.session_state.blueprint_job_id = submit_blueprint_job(filename, content)


def is_blueprint_processing() -> bool:
    job_id = st.session_state.get("blueprint_job_id")
    job = get_blueprint_job(job_id) if job_id else None
    return job is not None and job.state in {"queued", "running", "extracted"}


def apply_blueprint_result(job) -> None:
    project = st.session_state.project
    project.extraction = job.extraction
    if job.pdf_pages is not None:
        project.assumptions["pdf_pages"] = job.pdf_pages
    project.takeoff = calculate_takeoff(
        job.extraction.building_elements,
        default_rules(),
        project.assumptions.get("wastage", {}),
    )
    project.costs = calculate_costs(project.takeoff, st.session_state.prices)
    project.variance = calculate_variance(
        project.takeoff,
        aggregate_actuals(project.site_logs),
        project.assumptions.get("variance_threshold", 10.0),
    )


@st.fragment(run_every="1s")
def render_blueprint_job_status() -> None:
    job_id = st.session_state.get("blueprint_job_id")
    if not job_id:
        return

    job = get_blueprint_job(job_id)
    if job is None:
        st.warning("The processing task is no longer available. Please submit the blueprint again.")
    elif job.state in {"queued", "running"}:
        st.info(f"{job.message}  File: {job.filename}")
        st.progress(job.progress)
    elif job.state == "extracted":
        st.info(job.message)
        st.progress(job.progress)
        try:
            apply_blueprint_result(job)
            mark_blueprint_job_complete(job_id)
            st.success("Blueprint processing complete. Review extracted values before relying on the takeoff.")
        except (RuntimeError, ValueError) as exc:
            mark_blueprint_job_failed(job_id, str(exc))
            st.error(f"Could not calculate results from the extracted blueprint: {exc}")
    elif job.state == "failed":
        st.error(f"{job.message} {job.error or ''}")
    else:
        st.success("Blueprint processing complete. Review extracted values before relying on the takeoff.")


def refresh_calculations() -> None:
    project = st.session_state.project
    if project.extraction is None:
        return
    project.takeoff = calculate_takeoff(
        project.extraction.building_elements,
        default_rules(),
        project.assumptions.get("wastage", {}),
    )
    project.costs = calculate_costs(project.takeoff, st.session_state.prices)
    project.variance = calculate_variance(
        project.takeoff,
        aggregate_actuals(project.site_logs),
        project.assumptions.get("variance_threshold", 10.0),
    )


def render_setup() -> None:
    project = st.session_state.project
    st.header("Project setup")
    project.name = st.text_input("Project name", project.name)
    project.project_type = st.selectbox("Project type", ["Residential", "Commercial", "Renovation"], index=0)
    project.location = st.text_input("Location", project.location)
    project.currency = st.text_input("Currency", project.currency, max_chars=5).upper()
    st.subheader("Calculation assumptions")
    default_wastage = float(project.assumptions.get("default_wastage", 5.0))
    wastage = st.number_input("Default wastage (%)", min_value=0.0, value=default_wastage, step=0.5)
    threshold = st.number_input("Variance warning threshold (%)", min_value=0.0, value=float(project.assumptions.get("variance_threshold", 10.0)), step=1.0)
    project.assumptions["default_wastage"] = wastage
    project.assumptions["variance_threshold"] = threshold
    project.assumptions["wastage"] = {material: wastage for material in st.session_state.prices}
    st.info("Values extracted from drawings are estimates until reviewed by a qualified professional.")


def render_uploads() -> None:
    st.header("Upload documents")
    blueprint = st.file_uploader("Blueprint or structured extraction", type=["pdf", "png", "jpg", "jpeg", "json"])
    if blueprint:
        st.button(
            "Process blueprint",
            type="primary",
            disabled=is_blueprint_processing(),
            on_click=start_blueprint_processing,
            args=(blueprint.name, blueprint.getvalue()),
        )
    site_log = st.file_uploader("Construction site log", type=["txt", "md", "csv"])
    if site_log and st.button("Process site log"):
        try:
            entries = parse_site_log(read_text_file(site_log.name, site_log.getvalue()))
            st.session_state.project.site_logs.extend(entries)
            refresh_calculations()
            st.success(f"Parsed {len(entries)} material entries.")
        except ValueError as exc:
            st.error(str(exc))
    price_file = st.file_uploader("Price book CSV (material, unit, unit_price, currency)", type=["csv"])
    if price_file:
        try:
            frame = pd.read_csv(price_file)
            st.session_state.prices = {
                row.material.lower(): PriceEntry(
                    material=row.material.lower(), unit=row.unit, unit_price=float(row.unit_price), currency=getattr(row, "currency", st.session_state.project.currency)
                )
                for row in frame.itertuples(index=False)
            }
            refresh_calculations()
            st.success("Price book loaded.")
        except (KeyError, ValueError, AttributeError) as exc:
            st.error(f"Could not load price book: {exc}")


def render_analysis() -> None:
    project = st.session_state.project
    st.header("Blueprint analysis")
    if project.extraction is None:
        st.info("Upload and process a blueprint first.")
        return
    extraction = project.extraction
    st.write(f"**File:** {extraction.filename}  |  **Type:** {extraction.drawing_type}")
    if extraction.warnings:
        for warning in extraction.warnings:
            st.warning(warning)
    rooms = pd.DataFrame([room.model_dump() for room in extraction.rooms])
    if not rooms.empty:
        st.subheader("Rooms")
        st.dataframe(rooms, use_container_width=True, hide_index=True)
    elements = pd.DataFrame([element.model_dump() for element in extraction.building_elements])
    st.subheader("Building elements")
    edited = st.data_editor(elements, use_container_width=True, hide_index=True, key="element_editor")
    if st.button("Apply reviewed elements"):
        extraction.building_elements = [element for element in extraction.building_elements]
        for index, row in edited.iterrows():
            extraction.building_elements[index].quantity = float(row["quantity"])
        refresh_calculations()
        st.success("Reviewed values applied.")


def render_results() -> None:
    project = st.session_state.project
    st.header("Takeoff and cost analysis")
    if not project.takeoff:
        st.info("Process a blueprint first.")
        return
    total_cost = sum(line.estimated_cost for line in project.costs)
    st.metric("Estimated material cost", f"{project.currency} {total_cost:,.2f}")
    st.subheader("Material takeoff")
    st.dataframe(takeoff_dataframe(project.takeoff), use_container_width=True, hide_index=True)
    st.subheader("Cost summary")
    st.dataframe(costs_dataframe(project.costs), use_container_width=True, hide_index=True)
    st.subheader("Planned versus actual")
    variance = variance_dataframe(project.variance)
    st.dataframe(variance, use_container_width=True, hide_index=True)
    if not variance.empty:
        chart = variance.set_index("material")[["planned_quantity", "actual_quantity"]]
        st.bar_chart(chart)
    st.download_button("Download JSON report", json_report(project.takeoff, project.costs, project.variance), "constructiq-report.json", "application/json")
    st.download_button("Download Excel report", excel_report(project.takeoff, project.costs, project.variance), "constructiq-report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


initialize_state()
st.title("ConstructIQ")
st.caption("Architectural takeoff and construction cost intelligence MVP")
page = st.sidebar.radio("Navigate", ["Dashboard", "Project setup", "Upload documents", "Blueprint analysis", "Takeoff and costs"])
if st.session_state.get("blueprint_job_id"):
    render_blueprint_job_status()
if page == "Dashboard":
    render_results()
elif page == "Project setup":
    render_setup()
elif page == "Upload documents":
    render_uploads()
elif page == "Blueprint analysis":
    render_analysis()
else:
    render_results()
