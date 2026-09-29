import pandas as pd
import streamlit as st

from app.costing import calculate_costs, calculate_variance
from app.document_processing import pdf_page_count, read_text_file
from app.extraction import AIProviderError, extract_blueprint
from app.logs import aggregate_actuals, parse_site_log
from app.models import PriceEntry, ProjectState
from app.reporting import costs_dataframe, excel_report, json_report, takeoff_dataframe, variance_dataframe
from app.takeoff import calculate_takeoff, default_rules


st.set_page_config(page_title="ArcParser", page_icon="A", layout="wide")


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


def process_blueprint(uploaded_file) -> None:
    content = uploaded_file.getvalue()
    try:
        if uploaded_file.name.lower().endswith(".pdf"):
            st.session_state.project.assumptions["pdf_pages"] = pdf_page_count(content)
        extraction = extract_blueprint(uploaded_file.name, content)
        project = st.session_state.project
        project.extraction = extraction
        project.takeoff = calculate_takeoff(
            extraction.building_elements,
            default_rules(),
            project.assumptions.get("wastage", {}),
        )
        project.costs = calculate_costs(project.takeoff, st.session_state.prices)
        project.variance = calculate_variance(
            project.takeoff,
            aggregate_actuals(project.site_logs),
            project.assumptions.get("variance_threshold", 10.0),
        )
        st.success("Blueprint processed. Review extracted values before relying on the takeoff.")
    except (AIProviderError, RuntimeError, ValueError) as exc:
        st.error(str(exc))


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
    if blueprint and st.button("Process blueprint", type="primary"):
        process_blueprint(blueprint)
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
    st.download_button("Download JSON report", json_report(project.takeoff, project.costs, project.variance), "arcparser-report.json", "application/json")
    st.download_button("Download Excel report", excel_report(project.takeoff, project.costs, project.variance), "arcparser-report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


initialize_state()
st.title("ArcParser")
st.caption("Architectural takeoff and construction cost intelligence MVP")
page = st.sidebar.radio("Navigate", ["Dashboard", "Project setup", "Upload documents", "Blueprint analysis", "Takeoff and costs"])
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
